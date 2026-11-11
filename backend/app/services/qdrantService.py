import os
from qdrant_client import QdrantClient
from qdrant_client.http import models

class QdrantService:
    def __init__(self):
        # Lee las variables de entorno inyectadas por docker-compose
        # QDRANT_HOST será "qdrant" (el nombre del servicio en la red de Docker)
        self.host = os.getenv("QDRANT_HOST", "qdrant")
        self.port = int(os.getenv("QDRANT_PORT", 6333))
        
        # Inicializar el cliente oficial de Qdrant
        self.client = QdrantClient(host=self.host, port=self.port)
        self.collection_name = "cyberguard_cves"

    def search(self, query: str, limit: int = 3):
        """
        Realiza la búsqueda semántica de CVEs en la base de datos vectorial.
        """
        try:
            # 1. NOTA: Aquí deberías generar el vector de tu 'query' usando tu modelo de embeddings
            # (por ejemplo, con NVIDIA NIM Embeddings API o sentence-transformers).
            query_vector = embedding_model.embed(query)
            
            # 2. Búsqueda en Qdrant (ejemplo de estructura):
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit
            )
            return results
            
        except Exception as e:
            print(f"Error al conectar o buscar en Qdrant: {e}")
            return []

# --- Función de Independencia para FastAPI (Depends) ---
def get_qdrant_service() -> QdrantService:
    """
    Fábrica que instancia el servicio de Qdrant para ser inyectado en las rutas o agentes.
    """
    return QdrantService()