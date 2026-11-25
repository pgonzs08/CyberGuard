
import logging
import os

logger = logging.getLogger(__name__)


class QdrantService:

    def __init__(self):
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

    def check_connection(self) -> bool:
        """
        Comprueba la disponibilidad de la colección.
        """
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
            # 2. Recuperar documentos similares.
            # 3. Transformar los resultados a una estructura
            # fácilmente consumible por el agente.
            results = []

            return results

        except Exception:
            logger.exception(
                "[QDRANT_SERVICE] Error durante la búsqueda en Qdrant."
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
