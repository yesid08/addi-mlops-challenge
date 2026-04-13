"""First node: fetches user data from mock data store."""

from typing import Any

from source.adapters.utils.mock_data import MOCK_USERS
from source.application.state import GraphState


async def fetch_user_data(state: GraphState) -> dict[str, Any]:
    """Fetch user data from mock data store."""
    state["flow"].append("fetch_user_data")

    # Skip if already fetched (checkpoint optimization)
    if state.get("user_data"):
        return {}

    user_id = state.get("user_id", "")
    user_data = MOCK_USERS.get(user_id, {})

    return {
        "user_data": user_data,
        "user_data_summary": user_data,
    }
