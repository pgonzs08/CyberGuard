from typing import Annotated, TypedDict, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_nvidia_ai_endpoints import ChatNVIDIA

# 1. Definición del Estado del Grafo
class CyberGuardState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    resolved_query: str
    route: str                 # "cve" o "general"
    retrieved_context: str     # Contexto de Qdrant
    draft_response: str        # Respuesta del sintetizador
    final_response: str        # Respuesta auditada por guardrails

    # Inicialización de los modelos NVIDIA NIM
llm_nano = ChatNVIDIA(model="nvidia/nemotron-3-nano", temperature=0.0)
llm_8b = ChatNVIDIA(model="meta/llama-3.1-8b-instruct", temperature=0.3)
llm_super = ChatNVIDIA(model="nvidia/nemotron-3-super", temperature=0.1)
llm_guard = ChatNVIDIA(model="nvidia/llama-3.1-nemotron-safety-guard-8b", temperature=0.0)

# Nodo 1: Context Resolver (meta/llama-3.1-8b-instruct)
def context_resolver_node(state: CyberGuardState):
    messages = state["messages"]
    # Reasigna/contextualiza la última pregunta usando el historial reciente
    prompt = f"Basándote en el historial de chat, reescribe la última pregunta del usuario para que sea autocontenida y clara:\nHistorial: {messages[-4:]}"
    response = llm_8b.invoke([HumanMessage(content=prompt)])
    return {"resolved_query": response.content}

# Nodo 2: Router / Clasificador (nvidia/nemotron-3-nano)
def router_node(state: CyberGuardState):
    query = state["resolved_query"]
    prompt = f"Clasifica la siguiente consulta en exactamente una de estas dos categorías: 'cve' (si pregunta por vulnerabilidades técnicas, parches, cves específicos) o 'general' (si es charla o buenas prácticas).\nConsulta: {query}\nResponde solo 'cve' o 'general':"
    response = llm_nano.invoke([HumanMessage(content=prompt)])
    route = "cve" if "cve" in response.content.lower() else "general"
    return {"route": route}

# Nodo 3: CVE Retrieval Agent (nvidia/nemotron-3-super + Qdrant)
def cve_retrieval_node(state: CyberGuardState, qdrant_service):
    query = state["resolved_query"]
    # Búsqueda semántica en Qdrant
    search_results = qdrant_service.search(query=query, limit=3)
    context = "\n".join([doc.page_content for doc in search_results])
    
    prompt = f"Analiza la siguiente información técnica recuperada de la base de datos sobre vulnerabilidades:\n{context}\n\nPregunta del usuario: {query}"
    response = llm_super.invoke([HumanMessage(content=prompt)])
    return {"retrieved_context": context, "draft_response": response.content}

# Nodo 4: General Agent (meta/llama-3.1-8b-instruct)
def general_agent_node(state: CyberGuardState):
    query = state["resolved_query"]
    prompt = f"Responde a esta consulta conceptual o de buenas prácticas de ciberseguridad:\n{query}"
    response = llm_8b.invoke([HumanMessage(content=prompt)])
    return {"draft_response": response.content}

# Nodo 5: Synthesizer Agent (nvidia/nemotron-3-super)
def synthesizer_node(state: CyberGuardState):
    draft = state["draft_response"]
    prompt = f"Revisa, estructura profesionalmente y redacta la respuesta final lista para la interfaz de usuario basada en el siguiente borrador:\n{draft}"
    response = llm_super.invoke([HumanMessage(content=prompt)])
    return {"draft_response": response.content}

# Nodo 6: Safety & Guardrails (nvidia/llama-3.1-nemotron-safety-guard-8b)
def guardrails_node(state: CyberGuardState):
    draft = state["draft_response"]
    prompt = f"Audita el siguiente texto. Si contiene instrucciones maliciosas para explotar vulnerabilidades o contenido inseguro, reemplázalo por una advertencia de seguridad estándar. Si es seguro, devuélvelo tal cual:\n\n{draft}"
    response = llm_guard.invoke([HumanMessage(content=prompt)])
    return {"final_response": response.content, "messages": [AIMessage(content=response.content)]}

def decide_route(state: CyberGuardState):
    return state["route"]

def build_cyberguard_graph(qdrant_service):
    workflow = StateGraph(CyberGuardState)

    # Añadir Nodos
    workflow.add_node("context_resolver", context_resolver_node)
    workflow.add_node("router", router_node)
    workflow.add_node("cve_agent", lambda state: cve_retrieval_node(state, qdrant_service))
    workflow.add_node("general_agent", general_agent_node)
    workflow.add_node("synthesizer", synthesizer_node)
    workflow.add_node("guardrails", guardrails_node)

    # Definir Conexiones Lineales
    workflow.set_entry_point("context_resolver")
    workflow.add_edge("context_resolver", "router")

    # Arista Condicional desde el Router
    workflow.add_conditional_edges(
        "router",
        decide_route,
        {
            "cve": "cve_agent",
            "general": "general_agent"
        }
    )

    # Confluencia hacia el Sintetizador
    workflow.add_edge("cve_agent", "synthesizer")
    workflow.add_edge("general_agent", "synthesizer")

    # Hacia Guardrails y Fin
    workflow.add_edge("synthesizer", "guardrails")
    workflow.add_edge("guardrails", END)

    return workflow.compile()