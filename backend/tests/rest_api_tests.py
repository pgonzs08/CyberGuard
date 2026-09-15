import pytest
import requests


def test_api_online():
    url = "http://localhost:8000/api"
    
    try:
        # Realiza la petición HTTP GET con un tiempo de espera de 5 segundos
        response = requests.get(url, timeout=5)
        
        # Comprueba que el código de estado sea 200 OK
        assert response.status_code == 200, f"El servidor respondió con código {response.status_code}"
        
        # Comprueba que llegó texto en el cuerpo del mensaje y no está vacío
        assert response.text.strip() != "", "El servidor respondió, pero el mensaje está vacío"
        
    except requests.exceptions.ConnectionError:
        pytest.fail(f"No se pudo conectar al servidor en {url}")    

def test_api_creates_conversations():
    url = "http://localhost:8000/api/chatbot/conversaciones"
    
    try:
        # Realiza la petición HTTP POST con un tiempo de espera de 5 segundos
        response = requests.post(url, timeout=5)
        
        # Comprueba que el código de estado sea 201 CREATED
        assert response.status_code == 201, f"El servidor respondió con código {response.status_code}"

        data = response.json()
        
        # Comprueba que creó la conversación
        assert "conversacion_id" in data, "El servidor no creó conversación"

        # Comprueba que inicia la conversación
        assert "mensaje" in data, "El servidor no respondío con ningún mensaje"
                
    except requests.exceptions.ConnectionError:
        pytest.fail(f"No se pudo conectar al servidor en {url}. Asegúrate de que esté encendido.")