# backend.py
# Este archivo contiene el servidor Flask que aloja el asistente técnico.
# Se encarga de cargar los documentos, crear la base de datos vectorial,
# y responder a las preguntas utilizando el framework RAG (Retrieval Augmented Generation).

from flask import Flask, request, jsonify
from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import RetrievalQA
from langchain_core.documents import Document
import os
import shutil

app = Flask(__name__)

# --- 1. Preparación de Documentos Técnicos ---
DATA_DIR = "./documents" # Directorio donde se guardarán los archivos de texto (manuales, normas, etc.)

def load_documents_from_files(directory):
    """
    Carga documentos de archivos de texto (.txt) desde un directorio dado.
    Cada archivo se convierte en un objeto Document de Langchain.
    """
    loaded_documents = []
    if not os.path.exists(directory):
        print(f"ADVERTENCIA: El directorio de datos '{directory}' no existe. Creando uno vacío.")
        os.makedirs(directory)

    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                # Creamos un objeto Document con el contenido y el nombre del archivo como fuente
                loaded_documents.append(Document(page_content=content, metadata={"source": filename}))
                print(f"Cargado: {filename}")
            except Exception as e:
                print(f"Error al cargar el archivo {filename}: {e}")
    return loaded_documents

# Cargar los documentos desde los archivos de texto
docs_with_metadata = load_documents_from_files(DATA_DIR)

# Si no se cargaron documentos
if not docs_with_metadata:
    print(f"ERROR: No se encontraron archivos .txt en el directorio '{DATA_DIR}'.")
    print("Por favor, coloca al menos un archivo .txt con contenido en esta carpeta (ej. en la carpeta './data/').")
    exit(1)

# --- 2. Creación de la Base de Datos Vectorial ---
# Dividir los documentos en fragmentos (chunks) para una búsqueda más eficiente.
# chunk_size: tamaño máximo de cada fragmento.
# chunk_overlap: cantidad de texto superpuesto entre fragmentos consecutivos para mantener el contexto.
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

all_splits = text_splitter.split_documents(docs_with_metadata) # Ahora se pasa la lista de objetos Document

# Inicializar el modelo de embeddings de Ollama.
# Este modelo convierte el texto en vectores numéricos (embeddings).
# Asegúrate de que Ollama esté corriendo y tengas un modelo de embeddings descargado,
# por ejemplo, 'nomic-embed-text'. Puedes descargarlo con `ollama pull nomic-embed-text`.
print("Inicializando OllamaEmbeddings (requiere 'nomic-embed-text')...")
try:
    embeddings = OllamaEmbeddings(model="nomic-embed-text") # Modelo recomendado para embeddings
    print("OllamaEmbeddings inicializado.")
except Exception as e:
    print(f"Error al inicializar OllamaEmbeddings: {e}")
    print("Asegúrate de que Ollama esté corriendo y el modelo 'nomic-embed-text' esté descargado.")
    print("Ejecuta `ollama serve` y luego `ollama pull nomic-embed-text` en tu terminal.")
    exit(1) # Salir si no se pueden inicializar los embeddings

# Crear la base de datos vectorial local con ChromaDB.
# ChromaDB es una base de datos vectorial ligera que se puede usar localmente.
# Se indexan los fragmentos de documentos con sus embeddings.
print("Creando base de datos vectorial ChromaDB y indexando documentos...")
# Directorio para almacenar la base de datos Chroma
persist_directory = "./chroma_db"

if os.path.exists(persist_directory):
    print(f"Intentando eliminar el directorio existente de ChromaDB: {persist_directory}")
    try:
        shutil.rmtree(persist_directory)
        print(f"Directorio '{persist_directory}' eliminado exitosamente.")
    except PermissionError as e:
        print(f"Error específico: {e}")
        exit(1)
    except Exception as e:
        print(f"ADVERTENCIA: Ocurrió un error inesperado al intentar eliminar el directorio '{persist_directory}': {e}")
        exit(1)

if not os.path.exists(persist_directory):
    os.makedirs(persist_directory)

vectorstore = Chroma.from_documents(
    documents=all_splits,
    embedding=embeddings,
    persist_directory=persist_directory
)
# Persistir la base de datos para que no se reconstruya cada vez que se inicie el servidor
vectorstore.persist()
print(f"Base de datos vectorial ChromaDB creada y documentos indexados en '{persist_directory}'.")

# --- 3. Implementación del Asistente RAG ---
# Inicializar el modelo de lenguaje grande (LLM) de Ollama.
# Este modelo se usará para generar las respuestas.
# Asegúrate de que Ollama esté corriendo y tengas un modelo LLM descargado,
# por ejemplo, 'llama3.2' o 'mistral'. Puedes descargarlo con `ollama pull llama3.2`.
print("Inicializando Ollama LLM (requiere 'llama2' u otro modelo LLM Ollama)...")
try:
    llm = ChatOllama(model="llama3.2") # Modelo LLM recomendado
    print("Ollama LLM inicializado.")
except Exception as e:
    print(f"Error al inicializar Ollama LLM: {e}")
    print("Asegúrate de que Ollama esté corriendo y el modelo 'llama3.2' esté descargado.")
    print("Ejecuta `ollama pull llama3.2` en tu terminal.")
    exit(1) # Salir si no se puede inicializar el LLM

# Crear el recuperador (retriever) de la base de datos vectorial.
# El retriever es responsable de buscar los documentos más relevantes dada una pregunta.
retriever = vectorstore.as_retriever(search_kwargs={"k": 5}) # Recuperar los 2 documentos más relevantes

# Definir un prompt personalizado para el RAG.
# Este prompt guía al LLM sobre cómo usar el contexto recuperado para responder.
prompt_template = ChatPromptTemplate.from_template(
    """
    Eres un asistente técnico útil y conciso. Utiliza el siguiente contexto proporcionado
    para responder a la pregunta. Si no encuentras la respuesta en el contexto,
    simplemente di que no lo sabes. No intentes inventar información.

    Contexto:
    {context}

    Pregunta: {question}
    Respuesta:
    """
)

# Crear la cadena RetrievalQA.
# Esta cadena integra la recuperación de documentos con la generación de respuestas del LLM.
# 'stuff' chain_type: Junta todos los documentos recuperados en un solo prompt para el LLM.
# return_source_documents=True: Para mostrar qué documentos se utilizaron para la respuesta.
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True,
    chain_type_kwargs={"prompt": prompt_template}
)
print("Cadena RAG (RetrievalQA) configurada y lista para consultas.")

# --- Endpoint de la API Flask ---
# Este endpoint recibe preguntas del frontend y devuelve las respuestas del asistente.
@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data.get('question')

    if not question:
        return jsonify({"error": "Por favor, proporciona una pregunta en el cuerpo de la solicitud."}), 400

    print(f"Pregunta recibida: '{question}'")
    try:
        # Invocar la cadena RAG con la pregunta del usuario.
        result = qa_chain.invoke({"query": question})
        answer = result.get('result', "Lo siento, no pude encontrar una respuesta clara en la documentación.")
        # Extraer los metadatos de los documentos fuente para mostrar de dónde vino la información.
        source_documents = [doc.metadata.get('source', 'N/A') for doc in result.get('source_documents', [])]

        print(f"Respuesta generada: {answer}")
        print(f"Documentos fuente utilizados: {source_documents}")
        return jsonify({"answer": answer, "sources": source_documents})
    except Exception as e:
        print(f"Error al procesar la pregunta: {e}")
        return jsonify({"error": f"Error interno del servidor al procesar la pregunta: {str(e)}"}), 500

# Punto de entrada para ejecutar el servidor Flask.
if __name__ == '__main__':
    print("Iniciando el servidor Flask...")
    print("----------------------------------------------------------------------------------")
    print("¡IMPORTANTE! Asegúrate de que Ollama esté corriendo")
    print("Para iniciar Ollama: `ollama serve` en tu terminal.")
    print("Asegúrate de haber descargado los modelos necesarios:")
    print("  - Para embeddings: `ollama pull nomic-embed-text`")
    print("  - Para el LLM: `ollama pull llama3.2`")
    print("----------------------------------------------------------------------------------")
    app.run(debug=True, port=5000, use_reloader=False)
