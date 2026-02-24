"""Ollama local LLM provider implementation."""

from __future__ import annotations

import json
import os
from collections.abc import AsyncGenerator

import httpx

from jarvis.ai.providers.base import BaseProvider, ProviderError

_DEFAULT_BASE_URL = "http://localhost:11434"


class OllamaProvider(BaseProvider):
    """AI provider backed by a local Ollama instance."""

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = (
            base_url or os.environ.get("OLLAMA_BASE_URL") or _DEFAULT_BASE_URL
        ).rstrip("/")

    def is_available(self) -> bool:
        """Return True if Ollama is running and reachable."""
        try:
            import httpx as _httpx

            with _httpx.Client(timeout=3.0) as client:
                resp = client.get(f"{self._base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    async def generate(
        self,
        messages: list[dict],
        model: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": temperature},
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{self._base_url}/api/chat", json=payload
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("message", {}).get("content", "")
        except httpx.ConnectError as exc:
            raise ProviderError(
                f"Cannot connect to Ollama at {self._base_url}. Is it running?"
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"Ollama API error {exc.response.status_code}: {exc}"
            ) from exc
        except Exception as exc:
            raise ProviderError(f"Ollama error: {exc}") from exc

    async def generate_stream(
        self,
        messages: list[dict],
        model: str,
    ) -> AsyncGenerator[str, None]:
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST", f"{self._base_url}/api/chat", json=payload
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            content = chunk.get("message", {}).get("content")
                            if content:
                                yield content
                            if chunk.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue
        except httpx.ConnectError as exc:
            raise ProviderError(
                f"Cannot connect to Ollama at {self._base_url}. Is it running?"
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"Ollama streaming error {exc.response.status_code}: {exc}"
            ) from exc
        except Exception as exc:
            raise ProviderError(f"Ollama streaming error: {exc}") from exc
