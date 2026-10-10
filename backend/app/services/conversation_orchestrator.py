from bson import ObjectId


from app.core import settings
from app.core.dal.conversation import ConversationDAL, Conversation, MessageBase, Message
from app.services.agent import Agent

import json
import os
from langchain_openai import ChatOpenAI

class Orchestrator:
    def __init__(self, db_client):
        self._conv_dal = ConversationDAL(db_client)
        self._chatbot = Agent(ChatOpenAI(
                            model="deepseek-ai/deepseek-v4.1-flash",
                            openai_api_key=settings.NVIDIA_API_KEY,
                            openai_api_base="https://integrate.api.nvidia.com/v1",
                            temperature=1,
                            top_p=0.95,
                            max_tokens=262144,
                            streaming=False
                        ))

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