# frontend.py
# Este archivo contiene la interfaz de usuario para el asistente técnico,
# construida con Streamlit. Se comunica con el backend de Flask para obtener respuestas.

import streamlit as st
import requests
import json

# --- Configuración de la página Streamlit ---
st.set_page_config(
    page_title="Asistente Técnico Inteligente con IA Generativa",
    page_icon="🤖",
    layout="centered"
)

# --- Título y descripción de la aplicación ---
st.title("🤖 Asistente Técnico Inteligente")
st.markdown(
    """
    Bienvenido al asistente técnico impulsado por IA Generativa y RAG.
    Este demo muestra cómo la IA puede ayudarte a obtener información relevante de documentación técnica.
    """
)

st.write("---")

# --- Inicializar historial de chat en Streamlit session state ---
# Esto permite que la conversación persista a través de las interacciones del usuario.
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Mostrar mensajes de chat anteriores ---
# Itera sobre el historial de mensajes y los muestra en la interfaz.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "sources" in message and message["sources"]:
            st.caption(f"Fuentes: {', '.join(message['sources'])}")

# --- Campo de entrada para la pregunta del usuario (estilo chatbot) ---
# Usa st.chat_input para una experiencia de chat más nativa.
if prompt := st.chat_input("Escribe tu pregunta aquí..."):
    # Añadir el mensaje del usuario al historial y mostrarlo
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Preparar y enviar la pregunta al backend de Flask
    with st.chat_message("assistant"):
        with st.spinner("Buscando y generando respuesta..."):
            try:
                response = requests.post(
                    "http://localhost:5000/ask",
                    json={"question": prompt},
                    timeout=120
                )
                response.raise_for_status()
                data = response.json()

                if "answer" in data:
                    assistant_response = data["answer"]
                    sources = data.get("sources", [])

                    # Mostrar la respuesta del asistente
                    st.markdown(assistant_response)
                    if sources:
                        st.caption(f"Fuentes: {', '.join(sources)}")

                    # Añadir la respuesta del asistente al historial
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_response,
                        "sources": sources
                    })
                elif "error" in data:
                    error_message = f"Error del asistente: {data['error']}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
                else:
                    unexpected_response_message = "Respuesta inesperada del servidor. Formato de datos incorrecto."
                    st.error(unexpected_response_message)
                    st.json(data)
                    st.session_state.messages.append({"role": "assistant", "content": unexpected_response_message})

            except requests.exceptions.ConnectionError:
                conn_error_message = (
                    "❌ Error de conexión: Asegúrate de que el servidor Flask esté corriendo en "
                    "`http://localhost:5000`. Abre una terminal y ejecuta `python backend.py`."
                )
                st.error(conn_error_message)
                st.session_state.messages.append({"role": "assistant", "content": conn_error_message})
            except requests.exceptions.Timeout:
                timeout_message = "⏰ La solicitud al backend ha superado el tiempo de espera. Intenta de nuevo o verifica el modelo Ollama."
                st.error(timeout_message)
                st.session_state.messages.append({"role": "assistant", "content": timeout_message})
            except requests.exceptions.RequestException as e:
                request_error_message = f"❌ Error al comunicarse con el backend: {e}"
                st.error(request_error_message)
                st.write("Por favor, verifica la consola del backend para más detalles.")
                st.session_state.messages.append({"role": "assistant", "content": request_error_message})
            except json.JSONDecodeError:
                json_error_message = "❌ Error al decodificar la respuesta JSON del servidor. El backend pudo haber enviado una respuesta no JSON."
                st.error(json_error_message)
                st.write(f"Respuesta cruda: {response.text}")
                st.session_state.messages.append({"role": "assistant", "content": json_error_message})
            except Exception as e:
                generic_error_message = f"Ocurrió un error inesperado: {e}"
                st.error(generic_error_message)
                st.session_state.messages.append({"role": "assistant", "content": generic_error_message})