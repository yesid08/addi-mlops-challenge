import logging
import os
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)


def build_chain_with_fallback(
    prompt: ChatPromptTemplate,
    schema: type[BaseModel],
    temperature: float,
) -> Any:
    """Build a (prompt | llm.with_structured_output(schema)) chain with Gemini 2.0 Flash fallback.

    The returned chain transparently retries with Gemini 2.0 Flash whenever the
    primary OpenAI call raises an exception (rate limit, network error, auth failure, etc.).
    GOOGLE_API_KEY and OPENAI_API_KEY must be set in the environment.
    """
    primary_llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=temperature,
        api_key=os.getenv("OPENAI_API_KEY"),  # type: ignore[arg-type]
    )
    primary_chain = prompt | primary_llm.with_structured_output(schema)

    fallback_llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=temperature,
        google_api_key=os.getenv("GOOGLE_API_KEY"),  # type: ignore[arg-type]
    )
    fallback_chain = prompt | fallback_llm.with_structured_output(schema)

    return primary_chain.with_fallbacks(
        [fallback_chain], exceptions_to_handle=(Exception,)
    )
