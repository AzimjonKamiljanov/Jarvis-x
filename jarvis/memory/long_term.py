"""Long-term memory using ChromaDB vector database."""

from __future__ import annotations

import uuid
from pathlib import Path


class LongTermMemory:
    """Persistent semantic memory backed by ChromaDB."""

    def __init__(self, persist_dir: str = "./data/chromadb") -> None:
        self._persist_dir = persist_dir
        self._client = None
        self._collection = None
        self._available = False
        self._init_chromadb()

    def _init_chromadb(self) -> None:
        try:
            import chromadb  # type: ignore[import]

            Path(self._persist_dir).mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self._persist_dir)
            self._collection = self._client.get_or_create_collection("jarvis_memory")
            self._available = True
        except ImportError:
            self._available = False
        except Exception:
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def store(self, text: str, metadata: dict | None = None) -> None:
        """Store text with an auto-generated ID."""
        if not self._available or self._collection is None:
            return
        doc_id = str(uuid.uuid4())
        self._collection.add(
            documents=[text],
            ids=[doc_id],
            metadatas=[metadata or {}],
        )

    def search(self, query: str, n_results: int = 5) -> list[dict]:
        """Semantic search; returns list of {text, distance, metadata}."""
        if not self._available or self._collection is None:
            return []
        try:
            count = self._collection.count()
            if count == 0:
                return []
            results = self._collection.query(
                query_texts=[query],
                n_results=min(n_results, count),
            )
            output: list[dict] = []
            docs = results.get("documents", [[]])[0]
            distances = results.get("distances", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            for doc, dist, meta in zip(docs, distances, metadatas):
                output.append({"text": doc, "distance": dist, "metadata": meta})
            return output
        except Exception:
            return []

    def count(self) -> int:
        """Return number of stored entries."""
        if not self._available or self._collection is None:
            return 0
        try:
            return self._collection.count()
        except Exception:
            return 0
