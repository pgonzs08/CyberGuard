"""
FastAPI Server
"""
import logging

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from app.api.api_router import router as api_router
from app.core.settings import settings

import os
import sys

MONGO_URI = settings.MONGO_URI
DEBUG = settings.DEBUG
EXPIRATION_MINUTES = settings.EXPIRATION_MINUTES

logger = logging.getLogger("uvicorn")

@asynccontextmanager
async def lifespan(app: FastAPI):

    client = AsyncIOMotorClient(
        MONGO_URI,
        directConnection=True,
        connectTimeoutMS=5000
    )

    try:
        # Petición explícita al catálogo 'admin'
        logger.info("Probando conexión con MongoDB en %s...", MONGO_URI)
        pong = await client.admin.command("ping")
        
        if int(pong.get("ok", 0)) == 1:
            logger.info("Conexión con MongoDB establecida con éxito.")
        else:
            raise RuntimeError(f"Respuesta inesperada de Mongo ping: {pong}")
            
    except TimeoutError as e:
        logger.error("Fallo crítico de conexión a MongoDB: %s", str(e))
        client.close()
        raise TimeoutError(e)

    # Inyectar la base de datos en el estado global
    app.state.mongo_client = client
    app.state.db = client.get_database("cyberguard")

    #Yield back the application
    yield

    #Cerrar aplicación
    client.close()

#Crear la app
app = FastAPI(title="CiberGuard API", lifespan=lifespan, debug=DEBUG)

@app.get("/")
async def root():
    return {"message": "CyberGuard Backend Server is Running"}

#Incluir los routers a servicios
app.include_router(api_router, prefix="/api")

def main(argv=sys.argv[1:]):
    try:
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=DEBUG)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()