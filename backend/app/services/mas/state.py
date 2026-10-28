# app/services/mas/state.py
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator

class CyberGuardState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add] # Historial acumulativo
    session_id: str
    cve_context: list[str]                                    # Resultados recuperados de Qdrant
    next_node: str                                            # Decisión del router