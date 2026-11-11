
import os
import logging
from typing import Any

from qdrant_client import QdrantClient
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

logger = logging.getLogger(__name__)


class QdrantService:

    def __init__(self, embedding_model: Any = None):
        """
        Inicializa el servicio de Qdrant.

        Args:
            embedding_model: Servicio encargado de generar
                             los embeddings de las consultas.
        """

        self.host = os.getenv("QDRANT_HOST", "qdrant")
        self.port = int(os.getenv("QDRANT_PORT", "6333"))

        self.collection_name = os.getenv(
            "QDRANT_COLLECTION",
            "cyberguard_cves"
        )

        self.embedding_model = embedding_model

        self.client = QdrantClient(
            host=self.host,
            port=self.port,
            timeout=10
        )

    def check_connection(self) -> bool:
        """
        Comprueba la disponibilidad de la colección.
        """
        try:
            return self.client.collection_exists(
                collection_name=self.collection_name
            )

        except Exception as e:
            logger.error(
                "Error conectando con Qdrant: %s", e
            )
            return False

    def search(
        self,
        query: str,
        limit: int = 3
    ) -> list:
        """
        Realiza una búsqueda semántica en Qdrant.

        Args:
            query: Consulta del agente cve_agent.
            limit: Número máximo de resultados.

        Returns:
            Lista de documentos recuperados.
        """

        if not query or not query.strip():
            logger.warning("La query está vacía.")
            return []

        if limit < 1:
            logger.warning("El límite debe ser mayor que cero.")
            return []

        if self.embedding_model is None:
            logger.error("No se ha configurado embedding_model.")
            return []

        try:
            # 1. Generar embedding de la consulta.
            query_vector = self.embedding_model.embed(
                query.strip()
            )

            # 2. Recuperar documentos similares.
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )

            # 3. Transformar los resultados a una estructura
            # fácilmente consumible por el agente.
            results = []

            for point in response.points:
                results.append({
                    "id": point.id,
                    "score": point.score,
                    "payload": point.payload or {}
                })

            return results

        except Exception as e:
            logger.exception(
                "Error durante la búsqueda en Qdrant: %s", e
            )
            return []


# --------------------------------------------------
# Dependencia para FastAPI
# --------------------------------------------------

def get_qdrant_service() -> QdrantService:
    """
    Fábrica del servicio Qdrant.
    """
    return QdrantService()
