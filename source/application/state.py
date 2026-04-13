from typing import TypedDict, List, Optional, Dict, Any


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
    messages: List[Dict[str, Any]]

    # --- Output ---
    generation: str

    # --- Flow tracking ---
    flow: List[str]

    # --- User data (fetched from mock data) ---
    user_data: Optional[Dict[str, Any]]
    user_data_summary: Optional[Dict[str, Any]]

    # --- Router output ---
    selected_topic: Optional[str]
    selected_agent: Optional[str]
    router_reasoning: Optional[str]

    # --- Multi-step process tracking ---
    current_step: Optional[str]
    is_return_in_progress: bool

    # --- Conversation context ---
    last_topic_selected: Optional[str]
    set_previous_selected_topics: List[str]
