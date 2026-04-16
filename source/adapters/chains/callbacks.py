from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult


class TokenUsageCallback(BaseCallbackHandler):
    """Captures token usage and model name from a single LLM call.

    Usage::

        cb = TokenUsageCallback()
        await chain.ainvoke(inputs, config={"callbacks": [cb]})
        # cb.prompt_tokens, cb.completion_tokens, cb.total_tokens, cb.model_name
    """

    def __init__(self) -> None:
        super().__init__()
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self.total_tokens: int = 0
        self.model_name: str = ""

    def on_llm_end(self, response: LLMResult, **kwargs: object) -> None:
        llm_output = response.llm_output or {}
        usage = llm_output.get("token_usage", {})
        self.prompt_tokens = usage.get("prompt_tokens", 0)
        self.completion_tokens = usage.get("completion_tokens", 0)
        self.total_tokens = usage.get("total_tokens", 0)
        self.model_name = llm_output.get("model_name", "")
