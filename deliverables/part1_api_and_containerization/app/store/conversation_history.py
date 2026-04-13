import threading
from collections import defaultdict
from typing import Any


class ConversationHistoryStore:
    """Thread-safe in-memory conversation history keyed by conversation_id.

    Each entry is a list of {"role": "user"|"assistant", "content": "..."} dicts,
    matching the format expected by the LangGraph GraphState `messages` field.

    Note: state is lost on process restart. For multi-process deployments,
    replace with a Redis or database-backed implementation.
    """

    def __init__(self, max_messages: int = 50) -> None:
        self._store: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._lock = threading.Lock()
        self._max = max_messages

    def get(self, conversation_id: str) -> list[dict[str, Any]]:
        """Return a copy of the message history for a conversation."""
        with self._lock:
            return list(self._store[conversation_id])

    def append_turn(
        self,
        conversation_id: str,
        user_message: str,
        assistant_message: str,
    ) -> None:
        """Append a user + assistant turn and trim to max_messages."""
        with self._lock:
            history = self._store[conversation_id]
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": assistant_message})
            if len(history) > self._max:
                self._store[conversation_id] = history[-self._max :]

    def clear(self, conversation_id: str) -> None:
        """Delete all history for a conversation."""
        with self._lock:
            self._store.pop(conversation_id, None)

    def list_conversations(self) -> list[str]:
        """Return all known conversation IDs."""
        with self._lock:
            return list(self._store.keys())
