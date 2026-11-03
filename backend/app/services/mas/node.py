from typing import List, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_nvidia_ai_endpoints import ChatNVIDIA

class AgentNode:
    def __init__(self, system_prompt="", **model_kwargs):
        # Inicialización del cliente NIM usando las APIs de NVIDIA
        #self.llm = ChatNVIDIA(**model_kwargs)
        self.system_prompt = system_prompt

    async def __call__(self, message: BaseMessage) -> str:
        """Invocación asíncrona al LLM."""
        # Invocar al endpoint de NVIDIA
        return await self.llm.ainvoke(formatted_messages)