"""
FastAPI Server
"""
import logging
import os
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.environ["MONGO_URI"]
DEBUG = os.environ.get("DEBUG", "").strip().lower() in {"1", "true", "on", "yes"}
EXPIRATION_MINUTES = 3*60*24 #3 días

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

app = FastAPI(title="CiberGuard API", lifespan=lifespan, debug=DEBUG)

@app.get("/")
async def root():
    return {"message": "CyberGuard API running"}

def main(argv=sys.argv[1:]):
    try:
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=DEBUG)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()