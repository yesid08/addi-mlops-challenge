"""
Example: LLM chain with Pydantic structured output.

This demonstrates how to build a LangChain chain that returns structured data
using Pydantic models. Every agent in the system uses this pattern.

Pattern:
1. Define a Pydantic model for the structured output
2. Define a ChatPromptTemplate with system + message history + human input
3. Build the chain: prompt | ChatOpenAI().with_structured_output(Model)
4. Invoke with: result = await chain.ainvoke({...})
"""

import os

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# --- Step 1: Define Pydantic model for structured output ---


class AgentResponse(BaseModel):
    """Structured output for an agent. Define fields relevant to your use case."""

    reasoning: str = Field(
        ...,
        description="Brief internal reasoning about how to respond. Max 20 words.",
    )
    respuesta_final: str = Field(
        ...,
        description="The response message to send to the user.",
    )


# --- Step 2: Define the prompt template ---

SYSTEM_PROMPT = """You are a helpful assistant.

## USER DATA
{user_data}

## SCENARIOS
{scenarios}

## RULES
- Select the scenario that best matches the user's situation based on their data.
- Replace variable placeholders with actual values from user data.
- Keep responses concise (2-3 sentences max).
"""

agent_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
        ("human", "{question}"),
    ]
)


# --- Step 3: Build the chain ---


def get_example_chain():
    """
    Build and return a chain with structured output.

    Returns a LangChain Runnable: dict input -> AgentResponse output.
    """
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    # Core pattern: prompt | llm.with_structured_output(PydanticModel)
    return agent_prompt | llm.with_structured_output(AgentResponse)
