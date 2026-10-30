"""
FastAPI Server
"""

import sys
import logging

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api_router import router as api_router
import app.core.settings as settings


MONGO_URI = settings.MONGO_URI
DEBUG = settings.DEBUG
EXPIRATION_MINUTES = settings.EXPIRATION_MINUTES

logger = logging.getLogger("uvicorn")

@asynccontextmanager
async def lifespan(app: FastAPI):

    

    #Yield back the application
    yield



#Crear la app
app = FastAPI(title="CiberGuard API", lifespan=lifespan, debug=DEBUG)

@app.get("/")
async def root():
    return {"message": "CyberGuard Backend Server is Running"}

#Incluir los routers a servicios
app.include_router(api_router, prefix="/api")

# Configurar orígenes permitidos
origins = [
    "http://localhost:5173",  # Vite Dev Server
    "http://localhost:80",    # Nginx
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def main(argv=sys.argv[1:]):
    try:
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=DEBUG)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()