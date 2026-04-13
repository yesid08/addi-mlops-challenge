from typing import Any, TypedDict


class GraphState(TypedDict):
    """
    State for the Emporyum Tech conversational agent.

    This TypedDict defines all the fields that flow through the LangGraph graph.
    Each node receives the full state and returns a partial dict to update it.
    """

    # --- Identifiers ---
    user_id: str
    conversation_id: str

    # --- Input ---
    question: str
    messages: list[dict[str, Any]]

    # --- Output ---
    generation: str

    # --- Flow tracking ---
    flow: list[str]

    # --- User data (fetched from mock data) ---
    user_data: dict[str, Any] | None
    user_data_summary: dict[str, Any] | None

    # --- Router output ---
    selected_topic: str | None
    selected_agent: str | None
    router_reasoning: str | None

    # --- Multi-step process tracking ---
    current_step: str | None
    is_return_in_progress: bool

    # --- Conversation context ---
    last_topic_selected: str | None
    set_previous_selected_topics: list[str]
