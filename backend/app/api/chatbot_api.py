"""
 Este archivo guarda APIs de consulta al al chat de CyberGuard. Estas consultas son creadas mediante el envío y la edicción de mensajes.
"""
from datetime import datetime

from fastapi import APIRouter, status
from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    contenido: str = Field(..., example="¿Cómo funciona el stack FARM?")

class MessageAnswer(BaseModel):
    id: str
    rol: str = Field(..., example="assistant")  # "user" o "assistant"
    contenido: str
    fecha_creacion: datetime

class ConversacionResponse(BaseModel):
    conversacion_id: str
    mensaje_usuario: MessageAnswer
    respuesta_bot: MessageAnswer

class HistorialResponse(BaseModel):
    conversacion_id: str
    historial: list[MessageAnswer]


router = APIRouter(tags=["Chatbot"])

@router.post("/conversaciones", status_code=status.HTTP_201_CREATED)
async def iniciar_conversacion():
    """
    Crea una nueva sesión de chat única.
    Devuelve el ID de la conversación generado en MongoDB.
    """
    # Aquí llamarías a tu DAL/Repository: 
    # conversacion_id = await ChatRepository.crear_nueva_sesion()
    id_simulado = "chat_678abc123xyz"
    return {"conversacion_id": id_simulado, "mensaje": "Sesión de chat iniciada"}

@router.post("/conversaciones/{conversacion_id}", response_model=ConversacionResponse)
async def enviar_mensaje(conversacion_id: str, payload: MessageBase):
    """
    Envía un mensaje del usuario al chatbot.
    Procesa la respuesta (puedes inyectar tu servicio RAG aquí) y guarda todo en el DAL.
    """
    # 1. Validar que la conversación exista en base de datos
    # if not await ChatRepository.existe_conversacion(conversacion_id):
    #     raise HTTPException(status_code=404, detail="La sesión de chat no existe")

    # 2. Guardar el mensaje del usuario en el DAL
    # 3. Invocar la lógica de tu módulo RAG o LLM
    # respuesta_texto = await RagsService.generar_respuesta(payload.contenido, conversacion_id)
    respuesta = "NOT IMPLEMENTED: No se responder a preguntas todavía"

    ahora = datetime.now(datetime.timezone.utc())
    return {
        "conversacion_id": conversacion_id,
        "mensaje_usuario": {
            "id": "msg_user_1",
            "rol": "user",
            "contenido": payload.contenido,
            "fecha_creacion": ahora
        },
        "respuesta_bot": {
            "id": "msg_bot_1",
            "rol": "assistant",
            "contenido": respuesta,
            "fecha_creacion": ahora
        }
    }


@router.get("/conversaciones/{conversacion_id}", response_model=HistorialResponse)
async def obtener_historial(conversacion_id: str, limite: int | None = 20):
    """
    Recupera los últimos mensajes de una conversación específica desde tu DAL.
    Útil para cuando el usuario recarga la página en React.
    """
    # historial = await ChatRepository.obtener_mensajes(conversacion_id, limite)
    
    historial_simulado = [
        {"id": "1", "rol": "user", "contenido": "Hola", "fecha_creacion": datetime.now(tz=datetime.utc)},
        {"id": "2", "rol": "assistant", "contenido": "¿En qué puedo ayudarte?", "fecha_creacion": datetime.now(tz=datetime.utc)}
    ]
    
    return {
        "conversacion_id": conversacion_id,
        "historial": historial_simulado
    }