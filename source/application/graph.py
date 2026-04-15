"""
LangGraph workflow for the Emporyum Tech assistant.

Currently: fetch_user_data -> handle_general -> END

This module exports `workflow` as a StateGraph instance (NOT compiled).
The inline.py entry point compiles it with a checkpointer.
"""

from langgraph.graph import END, StateGraph

from source.application.state import GraphState
from source.domain.fetch_user_data import fetch_user_data
from source.domain.handle_general import handle_general

# Build graph
workflow = StateGraph(GraphState)

workflow.add_node("fetch_user_data", fetch_user_data)
workflow.add_node("handle_general", handle_general)

workflow.set_entry_point("fetch_user_data")
workflow.add_edge("fetch_user_data", "handle_general")
workflow.add_edge("handle_general", END)
