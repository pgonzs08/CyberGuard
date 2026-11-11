import functools
import json
import logging
from typing import Annotated, TypedDict
 
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
 
from app.services.mas.node import AgentNode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cyberguard.graph")


def log_node_errors(node_name: str):
    """Envuelve un nodo del grafo: si falla, registra el motivo con logging.error
    (incluyendo traceback) y vuelve a lanzar la excepción para que el grafo
    se detenga como lo haría sin el decorador."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"[{node_name}] Fallo en el nodo: {e!r}",
                    exc_info=True,
                )
                raise
        return wrapper
    return decorator


# 1. Definición del Estado del Grafo
class CyberGuardState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    resolved_query: str
    route: str                 # "cve" o "general"
    retrieved_context: str     # Contexto de Qdrant
    draft_response: str        # Respuesta del sintetizador
    final_response: str        # Respuesta auditada por guardrails

    # Parámetros de los modelos NVIDIA NIM
llm_nano = {"model": "nvidia/nemotron-3.5-lightning-30b-a3b", 
            "temperature": 0.0,
            "max_tokens": 2048,
            "chat_template_kwargs": {
                "enable_thinking": False
            }
            }
llm_8b = {"model": "nvidia/nemotron-3.5-lightning-30b-a3b", 
          "temperature": 0.3,"max_tokens": 2048,
        "chat_template_kwargs": {
            "enable_thinking": False
            }
          }
llm_super = {"model": "nvidia/nemotron-3-super-120b-a12b", 
             "temperature": 0.1,
            "max_tokens": 4096,
            "extra_body": {
                "reasoning_effort": "none"
                }
            }
llm_guard = {"model": "nvidia/llama-3.1-nemotron-safety-guard-8b-v3", "temperature": 0.0}

context_solver_agent = AgentNode(**llm_8b)
router_agent = AgentNode(**llm_nano)
cve_retrieval_agent = AgentNode(**llm_nano)
general_agent = AgentNode(**llm_8b)
synthesizer_agent = AgentNode(**llm_8b)
guard_agent = AgentNode(**llm_guard)


# Nodo 1: Context Resolver
@log_node_errors("context_resolver")
async def context_resolver_node(state: CyberGuardState):
    
    logger.info("PREGUNTANDO A RESOLVER")
    messages = state["messages"]
    # Reasigna/contextualiza la última pregunta usando el historial reciente
    prompt = f"Basándote en el historial de chat, reescribe la última pregunta del usuario para que sea autocontenida y clara:\nHistorial: {messages[-4:]}"
    response = await context_solver_agent([HumanMessage(content=prompt)])
    logger.info(f"CONTENT: {response.content!r}")
    logger.info(f"METADATA: {response.response_metadata}")
    logger.info(f"USAGE: {response.usage_metadata}")
    return {"resolved_query": response.content}


# Nodo 2: Router / Clasificador
@log_node_errors("router")
async def router_node(state: CyberGuardState):
    
    query = state["resolved_query"]
    prompt = f"Clasifica la siguiente consulta en exactamente una de estas dos categorías: 'cve' (si pregunta por vulnerabilidades técnicas, parches, cves específicos) o 'general' (si es charla o buenas prácticas).\nConsulta: {query}\nResponde solo 'cve' o 'general':"
    response = await router_agent([HumanMessage(content=prompt)])
    logger.info(f"CONTENT: {response.content!r}")
    logger.info(f"METADATA: {response.response_metadata}")
    logger.info(f"USAGE: {response.usage_metadata}")
    route = "cve" if "cve" in response.content.lower() else "general"
    return {"route": route}


# Nodo 3: CVE Retrieval Agent (+ Qdrant)
@log_node_errors("cve_agent")
async def cve_retrieval_node(state: CyberGuardState, qdrant_service):
    logger.info("Consultando en QDrant")
    query = state["resolved_query"]
    # Búsqueda semántica en Qdrant
    search_results = qdrant_service.search(query=query, limit=3)
    context = "\n".join([doc.page_content for doc in search_results])

    prompt = f"Analiza la siguiente información técnica recuperada de la base de datos sobre vulnerabilidades:\n{context}\n\nPregunta del usuario: {query}"
    response = await cve_retrieval_agent([HumanMessage(content=prompt)])
    return {"retrieved_context": context, "draft_response": response.content}


# Nodo 4: General Agent
@log_node_errors("general_agent")
async def general_agent_node(state: CyberGuardState):
    logger.info("PREGUNTANDO A GENERAL AGENT")
    query = state["resolved_query"]
    prompt = f"Responde a esta consulta conceptual o de buenas prácticas de ciberseguridad:\n{query}"
    response = await general_agent([HumanMessage(content=prompt)])
    logger.info(f"CONTENT: {response.content!r}")
    logger.info(f"METADATA: {response.response_metadata}")
    logger.info(f"USAGE: {response.usage_metadata}")
    return {"draft_response": response.content}


@log_node_errors("synthesizer")
async def synthesizer_node(state: CyberGuardState):

    logger.info("PREGUNTANDO A SYNTHESIZER")

    draft = state["draft_response"]

    prompt = f"""
Eres un agente especializado exclusivamente en reescribir
y mejorar respuestas de un asistente de ciberseguridad.

TU ÚNICA TAREA:
Reescribir el texto proporcionado para mejorar su claridad,
gramática, estructura y legibilidad, manteniendo exactamente
su significado y la información original.

REGLAS OBLIGATORIAS:

1. Devuelve exclusivamente la respuesta reescrita.
2. No incluyas introducciones como "Aquí tienes la versión...".
3. No expliques los cambios realizados.
4. No justifiques tus decisiones de redacción.
5. No añadas recomendaciones, información ni ejemplos
   que no estén presentes en el texto original.
6. No inventes contexto ni atribuyas emociones al usuario.
7. No añadas disculpas, preguntas o conclusiones que no
   estén justificadas por el borrador.
8. Conserva los términos técnicos y las referencias CVE.
9. Mantén el idioma original del borrador.
10. Utiliza Markdown únicamente cuando mejore la legibilidad.

IMPORTANTE:
Si el borrador ya está correctamente redactado, devuélvelo
sin modificaciones.
Si el borrador es un saludo o una respuesta breve,
mantén su brevedad.
Si el borrador está vacío, no inventes una respuesta.

FORMATO DE SALIDA:
Devuelve únicamente el texto final destinado al usuario.
No incluyas títulos sobre tu trabajo, comentarios,
explicaciones, justificaciones ni bloques de análisis.

<BEGIN_DRAFT>
{draft}
<END_DRAFT>

RESPUESTA REESCRITA:
"""

    response = await synthesizer_agent(
        [HumanMessage(content=prompt)]
    )

    synthesized = (response.content or "").strip()

    if not synthesized:
        logger.warning(
            "[synthesizer] Respuesta vacía. "
            "Se conserva el borrador original."
        )
        synthesized = draft

    logger.info(f"CONTENT: {response.content!r}")
    logger.info(f"METADATA: {response.response_metadata}")
    logger.info(f"USAGE: {response.usage_metadata}")

    return {"draft_response": synthesized}


SAFETY_TAXONOMY = """<BEGIN UNSAFE CONTENT CATEGORIES>
S1: Violencia.
S2: Planificación o facilitación de actividades delictivas.
S3: Armas de fuego y armas ilegales.
S4: Sustancias controladas o ilegales.
S5: Suicidio y autolesión.
S6: Contenido sexual.
S7: Odio y discriminación.
S8: Privacidad y datos personales (PII).
S9: Instrucciones de explotación técnica de vulnerabilidades o ciberataques.
<END UNSAFE CONTENT CATEGORIES>"""
 
 
def _build_safety_prompt(user_query: str, agent_response: str) -> str:
    return (
        "Task: Check if there is unsafe content in the user or agent messages "
        "in the below conversation in accordance with our safety policy with "
        "the below categories. Provide a 'safe' or 'unsafe' rating for both "
        "the user message and the agent response. If there is unsafe content, "
        "also provide a list of violated categories.\n\n"
        f"{SAFETY_TAXONOMY}\n\n"
        "<BEGIN CONVERSATION>\n"
        f"user: {user_query}\n"
        f"response: agent: {agent_response}\n"
        "<END CONVERSATION>\n\n"
        "Provide your safety assessment for the above conversation in the "
        "below output JSON format:\n"
        '{"User Safety": "safe o unsafe", "Response Safety": "safe o unsafe", '
        '"Safety Categories": "lista separada por comas si aplica, omitir si '
        'todo es seguro"}\n'
        "Do not include anything other than the output JSON in your response.\n"
        "Output JSON:"
    )
 
 
def _parse_guard_verdict(raw_content: str) -> dict | None:
    """Limpia posibles fences de markdown y parsea el JSON del guard model.
    Devuelve None si no se puede parsear."""
    text = raw_content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
 
 
# Nodo 6: Safety & Guardrails
@log_node_errors("guardrails")
async def guardrails_node(state: CyberGuardState):
    draft = state["draft_response"]
    user_query = state.get("resolved_query", "")
 
    prompt = _build_safety_prompt(user_query, draft)
    response = await guard_agent([HumanMessage(content=prompt)])
    verdict = _parse_guard_verdict(response.content)
 
    if verdict is None:
        logger.error(
            f"[guardrails] Respuesta del guard model no es JSON válido: {response.content!r}"
        )
        final = (
            "⚠️ No se pudo verificar la seguridad de la respuesta. "
            "Por favor, reformula tu consulta."
        )
        return {"final_response": final, "messages": [AIMessage(content=final)]}
 
    # "Response Safety" es lo relevante (la respuesta del agente);
    # si el modelo no lo incluyó, caemos a "User Safety" como señal secundaria.
    safety = verdict.get("Response Safety") or verdict.get("User Safety", "unsafe")
 
    if str(safety).lower() == "unsafe":
        categories = verdict.get("Safety Categories", "contenido no especificado")
        final = f"⚠️ No puedo proporcionar esa información por motivos de seguridad ({categories})."
    else:
        final = draft
 
    return {"final_response": final, "messages": [AIMessage(content=final)]}


def decide_route(state: CyberGuardState):
    return state["route"]


def build_simple_graph():
    workflow = StateGraph(CyberGuardState)

    workflow.add_node("context_resolver", context_resolver_node)
    workflow.add_node("general_agent", general_agent_node)
    workflow.add_node("synthesizer", synthesizer_node)
    workflow.add_node("guardrails", guardrails_node)

    workflow.set_entry_point("context_resolver")
    workflow.add_edge("context_resolver", "general_agent")
    workflow.add_edge("general_agent", "synthesizer")
    workflow.add_edge("synthesizer", "guardrails")
    workflow.add_edge("guardrails", END)

    return workflow.compile()


def build_cyberguard_graph(qdrant_service):
    workflow = StateGraph(CyberGuardState)
 
    # Añadir Nodos
    workflow.add_node("context_resolver", context_resolver_node)
    workflow.add_node("router", router_node)
    workflow.add_node("cve_agent", cve_retrieval_node)
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