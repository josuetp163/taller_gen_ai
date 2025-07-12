### 🚀 Instrucciones para ejecutar el proyecto:

Para que este asistente funcione, necesitas tener **Ollama** instalado y ejecutándose, además de los modelos de IA necesarios.

1. **Instalar Ollama:**

   * Descarga e instala Ollama desde su sitio web oficial: [ollama.com](https://ollama.com/)

2. **Descargar modelos de Ollama:**

   * Abre tu terminal o símbolo del sistema y ejecuta los siguientes comandos para descargar los modelos de embeddings y el modelo de lenguaje grande (LLM):

     ```
     ollama pull nomic-embed-text
     ollama pull llama3.2
     ```
   Nota: Puede tomar tiempo la descarga del modelo dependiendo de la velocidad de tu internet.

3. **Crea un ambiente virtual:**

   * Abre tu terminal y navega hasta la carpeta raíz del proyecto.

   * Ejecuta el siguiente comando para crear el ambiente virtual:

     ```
     python -m venv .venv
     ```
   * Ejecuta el siguiente comando para activar el ambiente virtual:

     ```
     .\.venv\Scripts\activate
     ```


3. **Instalar dependencias de Python:**

   * Abre tu terminal y navega hasta la carpeta donde guardarás tus archivos.

   * Ejecuta el siguiente comando para instalar las bibliotecas necesarias:

     ```
     pip install -r requirements.txt
     ```

4. **Iniciar el backend Flask:**

   * Abre una **nueva terminal** en la raíz del proyecto.

   * Ejecuta:

     ```
     python backend.py
     ```

   * Verás mensajes de inicialización de la base de datos vectorial y del LLM. Deja esta terminal abierta.

8. **Iniciar el frontend Streamlit:**

   * Abre otra **nueva terminal** en la raíz del proyecto

   * Ejecuta:

     ```
     streamlit run frontend.py
     ```

   * Esto abrirá automáticamente la aplicación Streamlit en tu navegador web (generalmente en `http://localhost:8501`).

¡Ahora puedes interactuar con tu Asistente Técnico Inteligente en un formato de chat!