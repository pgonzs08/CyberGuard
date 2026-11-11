"""test_nim.py - Prueba mínima de conexión con NVIDIA NIM usando LangChain."""
import os
import sys

from langchain_nvidia_ai_endpoints import ChatNVIDIA

llm_nano = {"model": "nvidia/nemotron-3.5-lightning-30b-a3b", "temperature": 0.0}

config = dict(llm_nano)
base_url = os.getenv("NVIDIA_BASE_URL")  # solo para un NIM local, p. ej. http://localhost:8000/v1

if base_url:
    config["base_url"] = base_url
else:
    # Endpoint alojado por NVIDIA: requiere API key y el nombre largo del modelo
    if not os.getenv("NVIDIA_API_KEY"):
        os.environ["NVIDIA_API_KEY"] = "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"
    config["model"] = "nvidia/nemotron-3.5-lightning-30b-a3b"

print(f"Probando conexión con: {config}")

try:
    llm = ChatNVIDIA(**config)
    response = llm.invoke("Responde únicamente con la palabra: OK")
    print("Conexión correcta.")
    print("Respuesta:", response.content)
except Exception as e:
    print(f"Error de conexión: {type(e).__name__}: {e}")
    sys.exit(1)