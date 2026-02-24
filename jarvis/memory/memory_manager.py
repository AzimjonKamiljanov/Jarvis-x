"""Memory manager — combines short-term and long-term memory."""

from __future__ import annotations

from jarvis.memory.long_term import LongTermMemory
from jarvis.memory.short_term import ShortTermMemory


class MemoryManager:
    """Unified memory interface that wraps short-term and long-term storage."""

    def __init__(
        self,
        short_term_limit: int = 20,
        vector_db_path: str = "./data/chromadb",
    ) -> None:
        self.short = ShortTermMemory(limit=short_term_limit)
        self.long: LongTermMemory | None = None
        _lt = LongTermMemory(persist_dir=vector_db_path)
        if _lt.available:
            self.long = _lt

    def add(self, session_id: str, role: str, content: str) -> None:
        """Add a message to short-term memory."""
        self.short.add(session_id, role, content)

    def get_context(self, session_id: str) -> list[dict]:
        """Return short-term context for the session."""
        return self.short.get_context(session_id)

    def save_interaction(
        self, session_id: str, user_msg: str, assistant_msg: str
    ) -> None:
        """Persist the exchange to both short-term and long-term memory."""
        self.short.add(session_id, "user", user_msg)
        self.short.add(session_id, "assistant", assistant_msg)
        if self.long is not None:
            self.long.store(
                f"User: {user_msg}\nAssistant: {assistant_msg}",
                metadata={"session_id": session_id},
            )

    def search_memory(self, query: str, n_results: int = 5) -> list[dict]:
        """Search long-term memory; returns [] if unavailable."""
        if self.long is None:
            return []
        return self.long.search(query, n_results=n_results)

    def build_context(
        self, session_id: str, current_query: str
    ) -> list[dict]:
        """Build a rich context list combining short-term and relevant long-term memories."""
        short_ctx = self.short.get_context(session_id)

        if self.long is None:
            return short_ctx

        memories = self.long.search(current_query, n_results=3)
        if not memories:
            return short_ctx

        memory_text = "\n".join(
            f"[Memory {i + 1}]: {m['text']}" for i, m in enumerate(memories)
        )
        memory_message: dict = {
            "role": "system",
            "content": f"Relevant past interactions:\n{memory_text}",
        }
        return [memory_message] + short_ctx
