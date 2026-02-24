"""OpenRouter API provider implementation."""

from __future__ import annotations

import json
import os
from collections.abc import AsyncGenerator

import httpx

from jarvis.ai.providers.base import BaseProvider, ProviderError

_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterProvider(BaseProvider):
    """AI provider backed by the OpenRouter API (Claude, GPT, Gemini, free models)."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("OPENROUTER_API_KEY")

    def is_available(self) -> bool:
        return bool(self._api_key)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/AzimjonKamiljanov/Jarvis-x",
            "X-Title": "JARVIS-X",
        }

    async def generate(
        self,
        messages: list[dict],
        model: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        if not self._api_key:
            raise ProviderError("OPENROUTER_API_KEY is not set. Cannot call OpenRouter API.")
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(_API_URL, headers=self._headers(), json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"] or ""
        except httpx.HTTPStatusError as exc:
            raise ProviderError(f"OpenRouter API error {exc.response.status_code}: {exc}") from exc
        except Exception as exc:
            raise ProviderError(f"OpenRouter error: {exc}") from exc

    async def generate_stream(
        self,
        messages: list[dict],
        model: str,
    ) -> AsyncGenerator[str, None]:
        if not self._api_key:
            raise ProviderError("OPENROUTER_API_KEY is not set. Cannot call OpenRouter API.")
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST", _API_URL, headers=self._headers(), json=payload
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        raw = line.removeprefix("data:").strip()
                        if raw == "[DONE]":
                            break
                        try:
                            chunk = json.loads(raw)
                            delta = chunk["choices"][0]["delta"].get("content")
                            if delta:
                                yield delta
                        except (json.JSONDecodeError, KeyError):
                            continue
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"OpenRouter streaming error {exc.response.status_code}: {exc}"
            ) from exc
        except Exception as exc:
            raise ProviderError(f"OpenRouter streaming error: {exc}") from exc
