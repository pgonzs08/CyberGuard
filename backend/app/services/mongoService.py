from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.dal.conversation import ConversationDAL, Conversation, MessageEntry
from app.core.settings import MONGO_URI

class MongoService:
    def __init__(self):

        # Instancia el cliente asíncrono requerido por el DAL
        self._client = AsyncIOMotorClient(MONGO_URI)
        self._db = self._client.get_database()
        
        # Inicializa la capa de acceso a datos de conversaciones
        self._conversation_dal = ConversationDAL(self._db.get_collection("conversations"))

    async def create_conversation(self, owner:str, conversation_name:str)-> str:

        id = await self._conversation_dal.create_conversation(owner=owner, name=conversation_name)

        return id

    async def add_message(self, conversation_id, message, role) -> Conversation:
        msg = MessageEntry(content=message, role=role, timetag=datetime.now(tz=timezone.utc).isoformat())
        conversation = await self._conversation_dal.add_message(id=conversation_id, message=msg)

        return conversation

# Función de dependencia (Dependency Injection) para FastAPI
def get_mongo_service() -> MongoService:
    """
    Fábrica que instancia el servicio de MongoDB y su DAL asociado.
    """
    return MongoService()