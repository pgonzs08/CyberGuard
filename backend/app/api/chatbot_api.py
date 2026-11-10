"""
 Este archivo guarda APIs de consulta al al chat de CyberGuard. Estas consultas son creadas mediante el envío y la edicción de mensajes.
"""
from datetime import datetime, timezone
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, Field

from app.services.chatService import ChatService
from app.services.qdrantService import get_qdrant_service, QdrantService
from app.services.mongoService import get_mongo_service, MongoService

from app.core.dal.conversation import Message, MessageEntry, Conversation, ConversationSummary

class MessageAnswer(BaseModel):
    id: str
    role: str = Field(..., example="assistant")  # "user" o "assistant"
    content: str
    timetag: datetime

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

class ListConversations(BaseModel):
    conversations: list[ConversationSummary]

router = APIRouter(tags=["Chatbot"])

# Fábrica para instanciar el servicio inyectando Qdrant (y opcionalmente MongoDB)
def get_chat_service(qdrant_service = Depends(get_qdrant_service), mongo_service=Depends(get_mongo_service)) -> ChatService:
    return ChatService(qdrant_service=qdrant_service, mongo_db=mongo_service)

@router.get("/", response_model=ListConversations)
async def listar_conversaciones(mongo_service: MongoService = Depends(get_mongo_service)):

    conversaciones = await mongo_service.get_conversations()

    return ListConversations(conversations = conversaciones)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def iniciar_conversacion(chat_service: ChatService = Depends(get_chat_service)):
    """
    Crea una nueva sesión de chat única.
    Devuelve el ID de la conversación generado en MongoDB.
    """
    # Aquí llamarías a tu DAL/Repository: 
    conversation_id = await chat_service.create_conversation()
    return {"id": conversation_id, "mensaje": "Sesión de chat iniciada"}
    
@router.post("/{conversacion_id}", response_model=MessageResponse)
async def enviar_mensaje_conversacion(
    payload: MessageRequest,
    conversacion_id: str = Path(..., description="ID único de la conversación"),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        result = await chat_service.process_message(
            message=payload.content,
            conversation_id=conversacion_id,
        )

        return MessageResponse(
            conversacion_id=conversacion_id,
            respuesta_agente=MessageAnswer(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                role="assistant",
                content=result["response"],
                timetag=datetime.now(timezone.utc),
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar el mensaje en la conversación: {str(e)}")

@router.get("/{conversacion_id}", response_model=HistorialResponse)
async def get_conversation(conversacion_id: str, limite: int | None = 20, mongo_service: MongoService=Depends(get_mongo_service)):
    """
    Recupera los últimos mensajes de una conversación específica desde tu DAL.
    Útil para cuando el usuario recarga la página en React.
    """
    conversation = await mongo_service.get_conversation_history(conversacion_id, limite)

    historial = [MessageAnswer(id=msg.id, role=msg.role, content=msg.content, timetag=msg.timetag) for msg in conversation.content]
    
    return HistorialResponse(conversacion_id=conversation.id, historial=historial)