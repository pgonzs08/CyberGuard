from langchain_core.messages import HumanMessage, AIMessage
from app.services.mas.graph import build_cyberguard_graph
from app.services.mongoService import MongoService
from app.services.qdrantService import QdrantService

class ChatService:
    def __init__(self, qdrant_service: QdrantService, mongo_db: MongoService = None):
        self._qdrant_service = qdrant_service
        self._mongo_db = mongo_db # Para guardar/cargar historial en MongoDB
        self._graph = build_cyberguard_graph(qdrant_service)

    async def create_conversation(self, conversation_name: str = "test") -> str:
        conversation_id = await self._mongo_db.create_conversation(owner="pgonzs", conversation_name=conversation_name)
        return conversation_id

    async def process_message(self, message: str, conversation_id: str | None = None) -> dict:
        # 1. (Opcional) Cargar historial previo desde MongoDB si existe conversation_id
        conversation = None
        if conversation_id and self._mongo_db:

            conversation = await self._mongo_db.add_message(conversation_id, message, role="user")

            historical_messages = []
        if conversation:
            for msg in conversation.content:
                historical_messages.append(AIMessage(msg.content) if msg.role.lower() is "ai" else HumanMessage(msg.content))
        
        # 2. Construir el estado inicial del grafo
        initial_state = {
            "messages": historical_messages,
            "resolved_query": "",
            "route": "",
            "retrieved_context": "",
            "draft_response": "",
            "final_response": ""
        }

        # 3. Ejecutar el flujo agéntico de LangGraph
        result = await self._graph.ainvoke(initial_state)

        response_text = result.get("final_response", "No se pudo generar respuesta.")
        route_taken = result.get("route", "unknown")

        if self._mongo_db:
            self._mongo_db.add_message(conversation_id=conversation_id, message=response_text, role="ai")

        return {
            "response": response_text,
            "route_taken": route_taken
        }