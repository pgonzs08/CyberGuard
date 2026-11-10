from typing import List
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_nvidia_ai_endpoints import ChatNVIDIA


class AgentNode:
    def __init__(self, system_prompt: str = "", **model_kwargs):
        # Inicialización del cliente NIM usando las APIs de NVIDIA
        self.llm = ChatNVIDIA(**model_kwargs)
        self.system_prompt = system_prompt

    async def __call__(self, messages: List[BaseMessage]) -> AIMessage:
        """Invocación asíncrona al LLM."""
        if self.system_prompt:
            messages = [SystemMessage(content=self.system_prompt), *messages]
        return await self.llm.ainvoke(messages)