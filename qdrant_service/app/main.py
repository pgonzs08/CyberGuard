"""Punto de entrada ASGI de qdrant_service.

Arranque: uvicorn app.main:app --host 0.0.0.0 --port 8080

HTTP se utiliza para healthchecks y documentación. Las operaciones de
negocio especificadas para el microservicio se expondrán mediante gRPC.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import api_router
from app.config import get_settings

# Si la configuración es inválida, el servicio falla aquí con un mensaje claro.
settings = get_settings()

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("qdrant_service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa y libera los recursos compartidos del servicio."""
    logger.info("Iniciando qdrant_service")
    # Las claves (SecretStr) se muestran enmascaradas.
    logger.info("Configuración cargada: %s", settings)

    # Inicializar aquí, cuando estén implementados, el cliente Qdrant,
    # el cliente HTTP de NVIDIA NIM y el servidor gRPC.
    # No ejecutar la ingestión de forma bloqueante durante el arranque.

    yield

    logger.info("Deteniendo qdrant_service")
    # Cerrar aquí los clientes y detener las tareas/servidores iniciados.


app = FastAPI(
    title="CyberGuard Qdrant Service",
    description=(
        "Gestión de la base vectorial Qdrant. HTTP proporciona healthchecks; "
        "las operaciones de negocio se implementarán mediante gRPC."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router)


def run() -> None:
    """Arranque alternativo mediante `python -m app.main`."""
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.service_host,
        port=settings.service_port,
        log_level=settings.log_level.lower(),
        reload=settings.uvicorn_reload,
    )


if __name__ == "__main__":
    run()
