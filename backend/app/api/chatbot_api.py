"""
 Este archivo guarda APIs de consulta al al chat de CyberGuard. Estas consultas son creadas mediante el envío y la edicción de mensajes.
"""
import uuid
from datetime import UTC, datetime

from backend.app.services.chat import ChatService
from backend.app.services.mongo_service import MongoService, get_mongo_service
from backend.app.services.qdrant_service import get_qdrant_service
from fastapi import APIRouter, Depends, Path, status
from pydantic import BaseModel, Field

from app.core.dal.conversation import ConversationSummary


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

qds = Depends(get_qdrant_service)
ms = Depends(get_mongo_service)


# Fábrica para instanciar el servicio inyectando Qdrant (y opcionalmente MongoDB)
def get_chat_service(qdrant_service = qds, mongo_service=ms) -> ChatService:
    return ChatService(qdrant_service=qdrant_service, mongo_db=mongo_service)

cs = Depends(get_chat_service)

@router.get("/", response_model=ListConversations)
async def listar_conversaciones(mongo_service: MongoService = ms):

    conversaciones = await mongo_service.get_conversations()

    return ListConversations(conversations = conversaciones)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def iniciar_conversacion(chat_service: ChatService = cs):
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
    chat_service: ChatService = cs,
):
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
            timetag=datetime.now(UTC),
        ),
    )

@router.get("/{conversacion_id}", response_model=HistorialResponse)
async def get_conversation(conversacion_id: str, limite: int | None = 20, mongo_service: MongoService=ms):
    """
    Recupera los últimos mensajes de una conversación específica desde tu DAL.
    Útil para cuando el usuario recarga la página en React.
    """
    conversation = await mongo_service.get_conversation_history(conversacion_id, limite)

    historial = [MessageAnswer(id=msg.id, role=msg.role, content=msg.content, timetag=msg.timetag) for msg in conversation.content]
    
    return HistorialResponse(conversacion_id=conversation.id, historial=historial)