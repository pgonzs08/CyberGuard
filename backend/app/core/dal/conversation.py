from datetime import date, datetime, timezone
from uuid import uuid4

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel, Field
from pymongo import ReturnDocument


class MessageBase(BaseModel):
    content: str = Field(..., example="How can I make a safe password?",description="Content of a new message")
    role: str = Field(..., description="Who sent the message")

class Message(BaseModel):
    id: uuid4
    role: str = Field(..., description="Who sent the message")
    timetag: datetime = Field(..., description="When was the message sent")
    content: str = Field(..., description="What does the message say")

    @staticmethod
    def from_doc(doc) -> 'Message':
        return Message(
            id = doc["_id"],
            role = doc["role"],
            timetag = doc["timetag"],
            content = doc["content"]
        )

    @staticmethod
    def from_msg(msg: MessageBase) -> 'Message':
        return Message(
            id = uuid4().hex,
            role = msg.role,
            timetag = datetime.now(tz=datetime.timezone.utc).isoformat(),
            content = msg.content
        )


    
class Conversation(BaseModel):
    id: ObjectId
    name: str = Field(..., description="A name that describes the conversation topic")
    owner: ObjectId = Field(..., description="User Id of the creator of the conversation")
    creation_date: date = Field(..., description="Date of creation of the conversation")
    content: list[Message] = Field(..., description= "A list of all the messages sent in chronological order")

    @staticmethod
    def from_doc(doc) -> 'Conversation':
        return Conversation(
            id = doc["_id"],
            name = doc["name"],
            owner = doc["owner"],
            creation_date = doc["creation_date"],
            content = doc["content"]
        )

    @staticmethod
    def from_msglist(historic: list[Message], owner: ObjectId, name: str) -> 'Conversation':
        return Conversation(
            id= ObjectId(),
            name = name,
            owner = owner,
            creation_date = date.fromisoformat(historic[0].timetag).isoformat(),
            content = historic
        )

class ConversationSummary(BaseModel):
    id: ObjectId = Field(..., description="The Id of the conversation summarized")
    name: str = Field(..., description="The name of the conversation summarized")
    owner: ObjectId = Field(..., description="Owner of the conversation summarized")
    creation_date: date = Field(..., description="Date of creation of the conversation summarized")
    msg_count: int = Field(..., description="Number of messages in the conversation")

    @staticmethod
    def from_document(doc) -> 'ConversationSummary':
        return ConversationSummary(
            id = doc["_id"],
            name = doc["name"],
            owner = doc["owner"],
            creation_date = doc["creation_date"],
            msg_count= doc["msg_count"]
        )


    @staticmethod
    def from_conversation(conv: Conversation) -> 'ConversationSummary':
        return ConversationSummary(
            id = conv.id,
            name = conv.name,
            owner = conv.owner,
            creation_date = conv.creation_date,
            msg_count= len(conv.content)
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
            yield ConversationSummary.from_doc(doc) if doc else doc

    async def create_conversation(self, owner: str | ObjectId, name: str, session=None) -> str:
        response = await self._collection.insert_one(
            {"name":name, "owner": owner, "creation_date": datetime.now(tz=timezone.utc).date().isoformat(),"content":[]},
            session=session,
        )

        return str(response.inserted_id)

    async def get_conversation(self, id:str | ObjectId, session=None) -> Conversation:
        doc = await self._collection.find_one(
            {"_id":ObjectId(id)},
            session=session,
        )
        return Conversation.from_doc(doc) if doc else doc

    async def delete_conversation(self, id:str | ObjectId, session=None) -> bool:
        response = await self._collection.delete_one(
            {"_id":ObjectId(id)},
            session=session,
        )
        return response.deleted_count == 1

    async def add_meesage(self, id: str|ObjectId, message:MessageBase, session=None) -> Conversation | None:
        result = await self._collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {
                "$push":{
                    "content":{
                        "_id": uuid4().hex,
                        "role": message.role,
                        "content": message.content, 
                        "timetag": datetime.now(tz=timezone.utc).isoformat()
                    }
                }
            },
            session=session,
            return_document=ReturnDocument.AFTER
        )
        if result:
            return Conversation.from_doc(result) 

    async def change_contents(self, doc_id: str|ObjectId, item_id: str, content: str, session=None) -> Conversation|None:
        result = await self._collection.find_one_and_update(
            {"_id": ObjectId(doc_id), "content._id": item_id},
            {"$set":{
                    "items.$.content": content,
                    "items.$.timetag": datetime.now(tz=timezone.utc).isoformat()
                },
            },
            session=session,
            return_document=ReturnDocument.AFTER
        )
        if result:
            return Conversation.from_doc(result)

    async def delete_item(self, doc_id: str|ObjectId, msg_id: str, session=None) -> Conversation | None:
        result = await self._collection.find_one_and_update(
            {"_id": ObjectId(doc_id)},
            {"$pull":{
                "content": {"_id": msg_id},
            }},
            session=session,
            return_document= ReturnDocument.AFTER
        )
        if result:
            return Conversation.from_doc(result)
