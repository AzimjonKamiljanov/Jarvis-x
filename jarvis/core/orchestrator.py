"""Main orchestrator — connects all JARVIS-X modules."""

from __future__ import annotations

import time
from collections.abc import AsyncGenerator

from jarvis.ai.model_router import ModelRouter
from jarvis.ai.providers.base import BaseProvider, ProviderError
from jarvis.ai.providers.groq_provider import GroqProvider
from jarvis.ai.providers.ollama_provider import OllamaProvider
from jarvis.ai.providers.openrouter_provider import OpenRouterProvider
from jarvis.core.config import JarvisConfig, load_config
from jarvis.memory.memory_manager import MemoryManager

_SYSTEM_PROMPT = (
    "You are JARVIS-X, a next-generation AI assistant. "
    "You are multilingual and can respond fluently in both Uzbek and English. "
    "Always detect the language of the user's message and reply in the same language. "
    "You are helpful, concise, and precise. "
    "If asked who you are, introduce yourself as JARVIS-X, an AI assistant."
)


class JarvisOrchestrator:
    """The main brain of JARVIS-X — coordinates config, memory, routing, and providers."""

    def __init__(self, config: JarvisConfig | None = None) -> None:
        self._config = config or load_config()
        self._memory: MemoryManager | None = None
        self._router: ModelRouter | None = None
        self._providers: dict[str, BaseProvider] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Set up providers, router, and memory."""
        self._memory = MemoryManager(
            short_term_limit=self._config.memory.short_term_limit,
        )
        self._router = ModelRouter()
        self._providers = {
            "groq": GroqProvider(),
            "openrouter": OpenRouterProvider(),
            "ollama": OllamaProvider(),
        }
        self._initialized = True

    def set_router(self, router: ModelRouter) -> None:
        """Replace the model router (useful for testing or overriding model selection)."""
        self._router = router

    def get_available_providers(self) -> list[str]:
        """Return names of providers that are currently available."""
        return [name for name, p in self._providers.items() if p.is_available()]

    def get_memory_count(self) -> int:
        """Return number of entries in long-term memory (0 if unavailable)."""
        if self._memory is None or self._memory.long is None:
            return 0
        return self._memory.long.count()

    async def process_message(
        self,
        user_input: str,
        session_id: str = "default",
        force_offline: bool = False,
    ) -> dict:
        """Process a user message end-to-end.

        Returns a dict with keys: response, model_used, response_time.
        """
        if not self._initialized:
            await self.initialize()

        assert self._memory is not None
        assert self._router is not None

        # 1. Build context (short-term + relevant long-term memories)
        context = self._memory.build_context(session_id, user_input)
        messages = [{"role": "system", "content": _SYSTEM_PROMPT}] + context

        # 2. Select model considering available providers
        available = self.get_available_providers()
        try:
            model_cfg = self._router.select_model(
                user_input,
                force_offline=force_offline,
                available_providers=available or None,
            )
        except RuntimeError as exc:
            self._memory.add(session_id, "assistant", str(exc))
            return {"response": str(exc), "model_used": "none", "response_time": 0.0}

        # 3. Call provider with fallback
        start = time.monotonic()
        response_text = await self._call_with_fallback(
            messages=messages,
            model_cfg_name=model_cfg.name,
            model_cfg_provider=model_cfg.provider,
            force_offline=force_offline,
        )
        elapsed = time.monotonic() - start

        # 4. Save interaction to memory
        self._memory.save_interaction(session_id, user_input, response_text)

        return {
            "response": response_text,
            "model_used": model_cfg.name,
            "response_time": round(elapsed, 3),
        }

    async def process_stream(
        self,
        user_input: str,
        session_id: str = "default",
        force_offline: bool = False,
    ) -> AsyncGenerator[str, None]:
        """Stream a response chunk by chunk."""
        if not self._initialized:
            await self.initialize()

        assert self._memory is not None
        assert self._router is not None

        context = self._memory.build_context(session_id, user_input)
        messages = [{"role": "system", "content": _SYSTEM_PROMPT}] + context

        available = self.get_available_providers()
        try:
            model_cfg = self._router.select_model(
                user_input,
                force_offline=force_offline,
                available_providers=available or None,
            )
        except RuntimeError as exc:
            yield str(exc)
            return

        provider = self._providers.get(model_cfg.provider)
        if provider is None or not provider.is_available():
            yield "I'm currently unavailable. Please check your API key or internet connection."
            return

        full_response: list[str] = []
        try:
            async for chunk in provider.generate_stream(
                messages=messages, model=model_cfg.name
            ):
                full_response.append(chunk)
                yield chunk
        except ProviderError as exc:
            yield str(exc)
            return

        self._memory.save_interaction(session_id, user_input, "".join(full_response))

    async def _call_with_fallback(
        self,
        messages: list[dict],
        model_cfg_name: str,
        model_cfg_provider: str,
        force_offline: bool,
    ) -> str:
        """Try the primary provider/model; fall back on error."""
        assert self._router is not None

        provider = self._providers.get(model_cfg_provider)
        if provider and provider.is_available():
            try:
                return await provider.generate(
                    messages=messages,
                    model=model_cfg_name,
                    max_tokens=self._config.ai.max_tokens,
                    temperature=self._config.ai.temperature,
                )
            except ProviderError:
                pass

        # Try fallback models from other available providers
        fallbacks = self._router.get_models_except(model_cfg_name)
        for fallback in sorted(fallbacks, key=lambda m: m.latency_ms):
            if force_offline and not fallback.offline_capable:
                continue
            fb_provider = self._providers.get(fallback.provider)
            if fb_provider and fb_provider.is_available():
                try:
                    return await fb_provider.generate(
                        messages=messages,
                        model=fallback.name,
                        max_tokens=self._config.ai.max_tokens,
                        temperature=self._config.ai.temperature,
                    )
                except ProviderError:
                    continue

        return "I'm currently unavailable. Please check your API key or internet connection."
