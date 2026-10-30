"""
 Este archivo guarda APIs de consulta al al chat de CyberGuard. Estas consultas son creadas mediante el envío y la edicción de mensajes.
"""
from datetime import datetime, timezone
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, Field

from app.services.chatService import ChatService
from app.services.qdrantService import get_qdrant_service
from app.services.mongoService import get_mongo_service

class MessageBase(BaseModel):
    contenido: str = Field(..., example="¿Cómo funciona el stack FARM?")

class MessageAnswer(BaseModel):
    id: str
    rol: str = Field(..., example="assistant")  # "user" o "assistant"
    contenido: str
    creation_date: datetime

class MessageRequest(BaseModel):
    content: str

class MessageResponse(BaseModel):
    conversacion_id: str
    respuesta_agente: MessageAnswer


class ConversacionResponse(BaseModel):
    conversacion_id: str
    mensaje_usuario: MessageAnswer
    respuesta_bot: MessageAnswer

class HistorialResponse(BaseModel):
    conversacion_id: str
    historial: list[MessageAnswer]

router = APIRouter(tags=["Chatbot"])

# Fábrica para instanciar el servicio inyectando Qdrant (y opcionalmente MongoDB)
def get_chat_service(qdrant_service = Depends(get_qdrant_service), mongo_service=Depends(get_mongo_service)) -> ChatService:
    return ChatService(qdrant_service=qdrant_service, mongo_db=mongo_service)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def iniciar_conversacion(chat_service: ChatService = Depends(get_chat_service)):
    """
    Crea una nueva sesión de chat única.
    Devuelve el ID de la conversación generado en MongoDB.
    """
    # Aquí llamarías a tu DAL/Repository: 
    conversation_id = await chat_service.create_conversation()
    return {"conversacion_id": conversation_id, "mensaje": "Sesión de chat iniciada"}
    

@router.post("/{conversacion_id}", response_model=MessageResponse)
async def enviar_mensaje_conversacion(
    conversacion_id: str = Path(..., description="ID único de la conversación"),
    payload: MessageRequest = None,
    chat_service: ChatService = Depends(get_chat_service)
):
    try:

        # 1. Procesar el mensaje a través del flujo agéntico de LangGraph
        result = await chat_service.process_message(
            message=payload.content,
            conversation_id=conversacion_id
        )
        
        respuesta_texto = result["response"]

        # 2. Generar metadatos de respuesta exigidos
        mensaje_id = f"msg_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        return MessageResponse(
            mensaje_id=mensaje_id,
            conversacion_id=conversacion_id,
            respuesta_agente=respuesta_texto,
            timestamp=timestamp
        )

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Error al procesar el mensaje en la conversación: {str(e)}")


@router.get("/{conversacion_id}", response_model=HistorialResponse)
async def obtener_historial(conversacion_id: str, limite: int | None = 20):
    """
    Recupera los últimos mensajes de una conversación específica desde tu DAL.
    Útil para cuando el usuario recarga la página en React.
    """
    # historial = await ChatRepository.obtener_mensajes(conversacion_id, limite)
    
    historial_simulado = [
        {"id": "1", "rol": "user", "contenido": "Hola", "creation_date": datetime.now(tz=datetime.utc)},
        {"id": "2", "rol": "assistant", "contenido": "¿En qué puedo ayudarte?", "creation_date": datetime.now(tz=datetime.utc)}
    ]
    
    return {
        "conversacion_id": conversacion_id,
        "historial": historial_simulado
    }