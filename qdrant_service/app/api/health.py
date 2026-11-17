from fastapi.responses import JSONResponse
from starlette import status
from fastapi import APIRouter

api_router = APIRouter()

@api_router.get("/", tags=["operaciones"])
async def root() -> dict:
    return {
        "service": "qdrant_service",
        "status": "running",
        "health": "/health",
        "docs": "/docs",
    }


@api_router.get("/health", tags=["operaciones"])
async def health() -> JSONResponse:
    """Endpoint requerido por el healthcheck de Docker Compose."""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "ok", "service": "qdrant_service"},
    )


@api_router.get("/docs", tags=["operaciones"])
async def health() -> JSONResponse:
    """Endpoint de docs Docker Compose."""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "ok", "service": "qdrant_service"},
    )
