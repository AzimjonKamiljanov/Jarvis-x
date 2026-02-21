"""Short-term conversation memory with a sliding window."""

from __future__ import annotations

from collections import defaultdict, deque


class ShortTermMemory:
    """Stores recent conversation history per session using a sliding window.

    System messages are always preserved when the window is trimmed.
    """

    def __init__(self, limit: int = 20) -> None:
        self._limit = max(1, limit)
        self._store: dict[str, deque[dict]] = defaultdict(lambda: deque())

    def add(self, session_id: str, role: str, content: str) -> None:
        """Add a message to the session history."""
        buf = self._store[session_id]
        buf.append({"role": role, "content": content})
        self._trim(session_id)

    def get_context(self, session_id: str) -> list[dict]:
        """Return all messages in OpenAI message format."""
        return list(self._store[session_id])

    def clear(self, session_id: str) -> None:
        """Clear all messages for a session."""
        self._store.pop(session_id, None)

    def _trim(self, session_id: str) -> None:
        """Keep only the most recent messages, always preserving system messages."""
        buf = self._store[session_id]
        if len(buf) <= self._limit:
            return

        system_msgs = [m for m in buf if m["role"] == "system"]
        non_system = [m for m in buf if m["role"] != "system"]

        # Keep the most recent non-system messages within the budget
        budget = max(0, self._limit - len(system_msgs))
        trimmed_non_system = non_system[-budget:] if budget > 0 else []

        self._store[session_id] = deque(system_msgs + trimmed_non_system)
