"""
Minimal LangGraph graph — run this to verify your environment is set up correctly.

    poetry run python -m source.examples.example_graph

If you see a greeting and "Setup is working!", your dependencies and API key are good.
"""
import asyncio
import os
import sys
from typing import Any, Dict

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from source.application.state import GraphState
from source.adapters.utils.mock_data import MOCK_USERS


async def fetch_user(state: GraphState) -> Dict[str, Any]:
    """Fetch user data from mock store."""
    state["flow"].append("fetch_user")
    user_data = MOCK_USERS.get(state.get("user_id", "user_001"), {})
    return {"user_data": user_data, "user_data_summary": user_data}


async def greet(state: GraphState) -> Dict[str, Any]:
    """Simple greeting using user data — no LLM call needed for this demo."""
    state["flow"].append("greet")
    name = state.get("user_data", {}).get("primer_nombre", "amigo")
    return {"generation": f"Hola {name}! Setup is working."}


# --- Build the graph ---
example_workflow = StateGraph(GraphState)
example_workflow.add_node("fetch_user", fetch_user)
example_workflow.add_node("greet", greet)

example_workflow.set_entry_point("fetch_user")
example_workflow.add_edge("fetch_user", "greet")
example_workflow.add_edge("greet", END)


if __name__ == "__main__":
    async def main():
        checkpointer = MemorySaver()
        graph = example_workflow.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": "setup-check"}}

        result = await graph.ainvoke(
            {
                "question": "Hola!",
                "messages": [],
                "user_id": "user_001",
                "conversation_id": "setup-check",
                "generation": "",
                "flow": [],
                "user_data": None,
                "user_data_summary": None,
                "selected_topic": None,
                "selected_agent": None,
                "router_reasoning": None,
                "current_step": None,
                "is_return_in_progress": False,
                "last_topic_selected": None,
                "set_previous_selected_topics": [],
            },
            config=config,
        )

        print(f"\nResponse: {result['generation']}")
        print(f"Flow: {' -> '.join(result['flow'])}")
        print("\nSetup is working! You're ready to build your solution.")

    asyncio.run(main())
