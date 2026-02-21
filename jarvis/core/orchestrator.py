"""Main orchestrator — connects all JARVIS-X modules."""

from __future__ import annotations

import time

from jarvis.ai.model_router import ModelRouter
from jarvis.ai.providers.base import ProviderError
from jarvis.ai.providers.groq_provider import GroqProvider
from jarvis.core.config import JarvisConfig, load_config
from jarvis.memory.short_term import ShortTermMemory

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
        self._memory: ShortTermMemory | None = None
        self._router: ModelRouter | None = None
        self._groq: GroqProvider | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Set up providers, router, and memory."""
        self._memory = ShortTermMemory(limit=self._config.memory.short_term_limit)
        self._router = ModelRouter()
        self._groq = GroqProvider()
        self._initialized = True

    def set_router(self, router: ModelRouter) -> None:
        """Replace the model router (useful for testing or overriding model selection)."""
        self._router = router

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

        # 1. Save user message
        self._memory.add(session_id, "user", user_input)

        # 2. Build messages list (system prompt + history)
        context = self._memory.get_context(session_id)
        messages = [{"role": "system", "content": _SYSTEM_PROMPT}] + context

        # 3. Select model
        try:
            model_cfg = self._router.select_model(user_input, force_offline=force_offline)
        except RuntimeError as exc:
            self._memory.add(session_id, "assistant", str(exc))
            return {"response": str(exc), "model_used": "none", "response_time": 0.0}

        # 4. Call provider with fallback
        start = time.monotonic()
        response_text = await self._call_with_fallback(
            messages=messages,
            model=model_cfg.name,
            force_offline=force_offline,
        )
        elapsed = time.monotonic() - start

        # 5. Save assistant response to memory
        self._memory.add(session_id, "assistant", response_text)

        return {
            "response": response_text,
            "model_used": model_cfg.name,
            "response_time": round(elapsed, 3),
        }

    async def _call_with_fallback(
        self,
        messages: list[dict],
        model: str,
        force_offline: bool,
    ) -> str:
        """Try the primary model; fall back to the fastest available on error."""
        assert self._groq is not None
        assert self._router is not None

        try:
            if self._groq.is_available() and not force_offline:
                return await self._groq.generate(
                    messages=messages,
                    model=model,
                    max_tokens=self._config.ai.max_tokens,
                    temperature=self._config.ai.temperature,
                )
        except ProviderError:
            # Try the fastest model as a fallback
            fallback_registry = self._router.get_models_except(model)
            if fallback_registry and not force_offline:
                fallback = min(fallback_registry, key=lambda m: m.latency_ms)
                try:
                    return await self._groq.generate(
                        messages=messages,
                        model=fallback.name,
                        max_tokens=self._config.ai.max_tokens,
                        temperature=self._config.ai.temperature,
                    )
                except ProviderError:
                    pass

        return (
            "I'm currently unavailable. Please check your API key or internet connection."
        )
