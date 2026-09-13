import pytest
import requests


def test_server_is_up_and_responding():
    url = "http://localhost:8000"
    
    try:
        # Realiza la petición HTTP GET con un tiempo de espera de 5 segundos
        response = requests.get(url, timeout=5)
        
        # Comprueba que el código de estado sea 200 OK
        assert response.status_code == 200, f"El servidor respondió con código {response.status_code}"
        
        # Comprueba que llegó texto en el cuerpo del mensaje y no está vacío
        assert response.text.strip() != "", "El servidor respondió, pero el mensaje está vacío"
        
    except requests.exceptions.ConnectionError:
        pytest.fail(f"No se pudo conectar al servidor en {url}. Asegúrate de que esté encendido.")