from bson import ObjectId

from app.core.dal.conversation import ConversationDAL, Conversation, MessageBase, Message
from app.services.agent import Agent

class Orchestrator:
    def __init__(self, db_client):
        self._conv_dal = ConversationDAL(db_client)

        client = ChatNVIDIA(
                    model="nvidia/nemotron-3.5-lightning-30b-a3b",
                    api_key="$NVIDIA_API_KEY", 
                    temperature=1,
                    top_p=0.95,
                    max_tokens=16384,
                    reasoning_budget=16384,
                    chat_template_kwargs={"enable_thinking":False},
                )
        
        self._chatbot = Agent(client, "Eres CyberGuard, un asistente conversacional de ciberseguridad para todos los públicos.")

    async def send_message(self, conv_id: str|ObjectId, msg: MessageBase):
        """
            Inserta el mensaje del usuario en la conversación y genera una respuesta del chatbot
            Devuelve la conversación actualizada
        """
        conv = self._conv_dal.add_message(conv_id, msg)
        response = await self._chatbot.generate_response(conv)
        return response

    async def create_conversation(self):
        return self._conv_dal.create_conversation(owner="pgonzs", name="Test_conv")

    async def delete_conversation(self, conv_id: str|ObjectId):
        return self._conv_dal.delete_conversation(conv_id)

    async def edit_conversation(self, conv_id: str|ObjectId, msg_id: str, content:str):
            return self._conv_dal.change_contents(conv_id)