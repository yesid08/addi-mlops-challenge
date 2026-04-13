"""
Example: Domain function (graph node) skeleton.

Each agent in the graph is an async function that receives the full state
and returns a partial dict to update it. LangGraph merges the returned
fields into the state automatically.

Your domain functions should follow this pattern.
"""
from typing import Any, Dict

from source.application.state import GraphState


async def example_agent(state: GraphState) -> Dict[str, Any]:
    """
    Skeleton of a graph node. Replace with your actual implementation.

    Every domain function should:
    1. Append its name to state["flow"] for tracing
    2. Get relevant KB data for its topic
    3. Filter user data to only the fields it needs (see data_filter.py)
    4. Invoke its LLM chain with the prepared inputs
    5. Return a partial state dict with the results
    """
    state["flow"].append("example_agent")

    # ... your implementation here ...

    return {
        "generation": "response text",
        "selected_topic": "TOPIC_NAME",
        "last_topic_selected": "TOPIC_NAME",
    }
