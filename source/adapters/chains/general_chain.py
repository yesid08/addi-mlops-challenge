import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()


class GeneralResponse(BaseModel):
    reasoning: str = Field(
        ..., description="Brief reasoning for the response. Max 20 words."
    )
    respuesta_final: str = Field(
        ..., description="Response to the user in Colombian Spanish."
    )


GENERAL_SYSTEM_PROMPT = """\
You are Emporyum Tech's virtual assistant. Emporyum Tech is a Colombian e-commerce platform \
that offers buy-now-pay-later installment plans.

## USER DATA
{user_data}

## KNOWLEDGE BASE
{knowledge_base}

## RULES
- ALWAYS address the user by their first name (primer_nombre).
- When asked about products, reference their category preferences and available promotions.
- When asked about orders, reference their specific orders (product name, status, amounts).
- When asked about payments, reference their outstanding balances and installment details.
- Respond in natural Colombian Spanish, 2-4 sentences.
- If you don't have enough information to answer, say so honestly."""

general_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", GENERAL_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
        ("human", "{question}"),
    ]
)


def get_general_chain():
    """Build and return the general agent chain with structured output."""
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    return general_prompt | llm.with_structured_output(GeneralResponse)
