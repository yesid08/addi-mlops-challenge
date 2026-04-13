"""Version B — treatment agent.

Changes vs. Version A (control):
  1. System prompt written entirely in Colombian Spanish.
     Rationale: aligning the instruction language with the output language eliminates
     the model's need to code-switch between English rules and Spanish responses,
     which is expected to produce more natural-sounding output.
  2. temperature=0.3 (vs 0.0 in control).
     Rationale: a small amount of stochasticity breaks rote-phrasing patterns
     while keeping the output stable enough to measure statistically.
  3. Knowledge Base formatted as concise per-topic bullet points instead of a raw
     Python dict repr — reduces token noise and improves model parse accuracy.

Everything else (model, output schema shape, data filter, graph topology) is
identical to Version A so that only these three variables are being tested.
"""

import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from source.adapters.utils.data_filter import filter_user_data
from source.adapters.utils.knowledge_base import SCENARIO_KNOWLEDGE_BASE
from source.application.state import GraphState
from source.domain.fetch_user_data import fetch_user_data

load_dotenv()

# ---------------------------------------------------------------------------
# Prompt — written in Colombian Spanish (treatment differentiator #1)
# Rules appear before data sections so the model internalises constraints
# before reading variable content (reduces instruction-following errors).
# ---------------------------------------------------------------------------

TREATMENT_SYSTEM_PROMPT = """\
Eres el asistente virtual de Emporyum Tech, una plataforma colombiana de comercio electrónico \
que ofrece planes de pago en cuotas (compra ahora, paga después).

## REGLAS
- Dirígete siempre al usuario por su primer nombre (campo primer_nombre).
- Para preguntas sobre productos: menciona sus preferencias de categorías y promociones disponibles.
- Para preguntas sobre pedidos: menciona sus pedidos específicos (nombre del producto, estado, montos).
- Para preguntas sobre pagos: menciona sus saldos pendientes y detalles de cuotas.
- Responde en español colombiano natural en 1 a 3 oraciones.
- Si no tienes información suficiente para responder, dilo con honestidad.

## DATOS DEL USUARIO
{user_data}

## BASE DE CONOCIMIENTO
{knowledge_base}
"""

treatment_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", TREATMENT_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
        ("human", "{question}"),
    ]
)


# ---------------------------------------------------------------------------
# Output schema — identical structure to GeneralResponse (Version A)
# so downstream code can treat both variants uniformly.
# ---------------------------------------------------------------------------


class TreatmentResponse(BaseModel):
    reasoning: str = Field(
        ..., description="Razonamiento breve de la respuesta. Máximo 20 palabras."
    )
    respuesta_final: str = Field(
        ..., description="Respuesta al usuario en español colombiano."
    )


def get_treatment_chain() -> Any:
    """Build and return the treatment agent chain with structured output."""
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,  # treatment differentiator #2
        api_key=os.getenv("OPENAI_API_KEY"),  # type: ignore[arg-type]
    )
    return treatment_prompt | llm.with_structured_output(TreatmentResponse)


# ---------------------------------------------------------------------------
# Knowledge-base formatter — treatment differentiator #3
# Converts the raw Python dict repr into a readable bullet list.
# ---------------------------------------------------------------------------

GENERAL_RELEVANT_FIELDS = [
    "delivery_address_city",
    "purchase_history",
    "user_category_preferences",
    "available_promotions",
]


def _format_kb_as_bullets(kb: dict) -> str:  # type: ignore[type-arg]
    """Format the KB as concise per-topic bullet points."""
    lines = []
    for topic, data in kb.items():
        contexto = data.get("contexto", "")
        instrucciones = data.get("instrucciones", "")
        lines.append(f"• {topic}: {contexto} — {instrucciones}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Domain handler
# ---------------------------------------------------------------------------


async def handle_general_b(state: GraphState) -> dict[str, Any]:
    """Treatment version of handle_general.

    Calls the same graph node name ("handle_general") so the `flow` list
    remains consistent between variants.
    """
    state["flow"].append("handle_general")

    knowledge_base = _format_kb_as_bullets(SCENARIO_KNOWLEDGE_BASE)
    filtered_data = filter_user_data(state.get("user_data"), GENERAL_RELEVANT_FIELDS)

    try:
        chain = get_treatment_chain()
        result = await chain.ainvoke(
            {
                "knowledge_base": knowledge_base,
                "user_data": str(filtered_data),
                "messages": state.get("messages", []),
                "question": state["question"],
            }
        )

        return {"generation": result.respuesta_final}

    except Exception as e:
        print(f"[ERROR] handle_general_b failed: {e}")
        return {
            "generation": (
                "Disculpa, tuve un problema procesando tu solicitud. "
                "Por favor intenta de nuevo o contacta a nuestro equipo de soporte."
            ),
        }


# ---------------------------------------------------------------------------
# Graph — same topology as Version A, only the handle_general node differs.
# Node name kept as "handle_general" for flow-list consistency.
# ---------------------------------------------------------------------------

workflow_b = StateGraph(GraphState)

workflow_b.add_node("fetch_user_data", fetch_user_data)
workflow_b.add_node("handle_general", handle_general_b)

workflow_b.set_entry_point("fetch_user_data")
workflow_b.add_edge("fetch_user_data", "handle_general")
workflow_b.add_edge("handle_general", END)
