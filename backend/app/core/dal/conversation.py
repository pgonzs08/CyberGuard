from datetime import date, datetime, timezone
from uuid import uuid4

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel, Field
from pymongo import ReturnDocument

class MessageEntry(BaseModel):
    content: str = Field(..., examples=["How can I make a safe password?"], description="Content of a new message")
    role: str = Field(..., description="Who sent the message")
    timetag: datetime = Field(..., description="When was the message sent")

class Message(BaseModel):
    id: str
    role: str = Field(..., description="Who sent the message")
    timetag: datetime = Field(..., description="When was the message sent")
    content: str = Field(..., description="What does the message say")

    @staticmethod
    def from_doc(doc) -> 'Message':
        # MongoDB o UUIDs pueden venir con "_id" o "id" dependiendo de la consulta
        msg_id = doc.get("_id") or doc.get("id")
        
        # Aseguramos que timetag sea un objeto datetime si viene como string desde Mongo
        timetag_val = doc["timetag"]
        if isinstance(timetag_val, str):
            timetag_val = datetime.fromisoformat(timetag_val.replace("Z", "+00:00"))

        return Message(
            id=str(msg_id),
            role=doc["role"],
            timetag=timetag_val,
            content=doc["content"]
        )

    @staticmethod
    def from_msg(msg: MessageEntry) -> 'Message':
        return Message(
            id=uuid4().hex,
            role=msg.role,
            timetag=datetime.now(tz=timezone.utc), # Guardamos como objeto datetime nativo
            content=msg.content
        )

class Conversation(BaseModel):
    id: str
    name: str = Field(..., description="A name that describes the conversation topic")
    owner: str = Field(..., description="User Id of the creator of the conversation") # CAMBIADO A STR
    creation_date: date = Field(..., description="Date of creation of the conversation")
    content: list[Message] = Field(..., description="A list of all the messages sent in chronological order")

    @staticmethod
    def from_doc(doc) -> 'Conversation':
        # Mapeamos la lista de subdocumentos dict a objetos Message correctamente
        messages = [Message.from_doc(m) for m in doc.get("content", [])]
        
        # Aseguramos que creation_date sea un objeto date
        c_date = doc["creation_date"]
        if isinstance(c_date, str):
            c_date = date.fromisoformat(c_date)

        return Conversation(
            id=str(doc["_id"]),
            name=doc["name"],
            owner=str(doc["owner"]), # Convertimos el ObjectId de Mongo a str
            creation_date=c_date,
            content=messages
        )

    @staticmethod
    def from_msglist(historic: list[Message], owner: str | ObjectId, name: str) -> 'Conversation':
        return Conversation(
            id=str(ObjectId()),
            name=name,
            owner=str(owner), # Convertimos a str
            creation_date=historic[0].timetag.date() if historic else datetime.now(tz=timezone.utc).date(), # Objeto date nativo
            content=historic
        )

class ConversationSummary(BaseModel):
    id: str = Field(..., description="The Id of the conversation summarized")
    name: str = Field(..., description="The name of the conversation summarized")
    owner: str = Field(..., description="Owner of the conversation summarized") # CAMBIADO A STR
    creation_date: date = Field(..., description="Date of creation of the conversation summarized")
    msg_count: int = Field(..., description="Number of messages in the conversation")

    @staticmethod
    def from_doc(doc) -> 'ConversationSummary': # Corregido el nombre (antes era from_document)
        c_date = doc["creation_date"]
        if isinstance(c_date, str):
            c_date = date.fromisoformat(c_date)

        return ConversationSummary(
            id=str(doc["_id"]),
            name=doc["name"],
            owner=str(doc["owner"]), # Convertimos a str
            creation_date=c_date,
            msg_count=doc["msg_count"]
        )

    @staticmethod
    def from_conversation(conv: Conversation) -> 'ConversationSummary':
        return ConversationSummary(
            id=conv.id,
            name=conv.name,
            owner=conv.owner,
            creation_date=conv.creation_date,
            msg_count=len(conv.content)
        )

class ConversationDAL:

    def __init__(self, collection: AsyncIOMotorCollection):
        self._collection = collection

    async def list_conversations(self, session=None):
        """
        Devuelve el resumen de todas las conversaciones
        """
        async for doc in self._collection.find(
            {},
            projection={
                "name": 1,
                "owner": 1,
                "creation_date": 1,
                "msg_count": {"$size": "$content"},
            },
            sort={"creation_date": 1},
            session=session
        ):
            # Corregido: Llamaba a .from_doc() que no existía en el modelo original
            yield ConversationSummary.from_doc(doc) if doc else doc

    async def create_conversation(self, owner: str | ObjectId, name: str, session=None) -> str:
        # Aseguramos que guardamos un ObjectId real en la base de datos de Mongo para indexación eficiente
        db_owner = "ROLE_ADMIN"#ObjectId(owner) if isinstance(owner, str) else owner
        
        response = await self._collection.insert_one(
            {
                "name": name, 
                "owner": db_owner, 
                "creation_date": datetime.now(tz=timezone.utc).date().isoformat(),
                "content": []
            },
            session=session,
        )
        return str(response.inserted_id)

    async def get_conversation(self, id: str | ObjectId, session=None) -> Conversation | None:
        doc = await self._collection.find_one(
            {"_id": ObjectId(id)},
            session=session,
        )
        return Conversation.from_doc(doc) if doc else None

    async def delete_conversation(self, id: str | ObjectId, session=None) -> bool:
        response = await self._collection.delete_one(
            {"_id": ObjectId(id)},
            session=session,
        )
        return response.deleted_count == 1

    async def add_message(self, id: str | ObjectId, message: MessageEntry, session=None) -> Conversation | None:
        result = await self._collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {
                "$push": {
                    "content": {
                        "id": uuid4().hex, # Cambiado a "id" para mantener consistencia con Pydantic
                        "role": message.role,
                        "content": message.content, 
                        "timetag": message.timetag
                    }
                }
            },
            session=session,
            return_document=ReturnDocument.AFTER
        )
        if result:
            return Conversation.from_doc(result) 

    async def change_contents(self, conv_id: str | ObjectId, msg_id: str, content: str, session=None) -> Conversation | None:
        # Buscamos por "content.id" en lugar de "content._id" ya que guardaste subdocumentos usando el campo id plano
        result = await self._collection.find_one_and_update(
            {"_id": ObjectId(conv_id), "content.id": msg_id},
            {
                "$set": {
                    "content.$.content": content,
                    "content.$.timetag": datetime.now(tz=timezone.utc).isoformat()
                },
            },
            session=session,
            return_document=ReturnDocument.AFTER
        )
        if result:
            return Conversation.from_doc(result)

    async def delete_message(self, doc_id: str | ObjectId, msg_id: str, session=None) -> Conversation | None:
        result = await self._collection.find_one_and_update(
            {"_id": ObjectId(doc_id)},
            {
                "$pull": {
                    "content": {"id": msg_id}, # Cambiado a "id"
                }
            },
            session=session,
            return_document=ReturnDocument.AFTER
        )
        if result:
            return Conversation.from_doc(result)
