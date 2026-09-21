from typing import List, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.core.dal.conversation import Conversation, MessageBase

class Agent:
    def __init__(self, llm, system_prompt):
        # Inicialización del cliente NIM usando las APIs de NVIDIA
        self.llm = llm
        
        self.system_prompt = system_prompt

    def _build_langchain_messages(self, conv: Conversation) -> List[Any]:
        """Convierte el historial de la BD en formato de mensajes nativos de LangChain."""
        messages = [self.system_prompt]

        #Añade los mensajes de la conversación
        for msg in conv.content:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        return messages

    async def generate_response(self, conv: Conversation) -> str:
        """Invocación asíncrona al LLM."""
        formatted_messages = self._build_langchain_messages(conv)
        
        # Invocar al endpoint de NVIDIA
        response = await self.llm.ainvoke(formatted_messages)
        return MessageBase(content=response.content, role="assistant")