"""Model router — selects the best model for a given task."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TaskComplexity(Enum):
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


@dataclass
class ModelConfig:
    name: str
    provider: str
    latency_ms: int
    quality_score: float
    offline_capable: bool


# Pre-configured registry of available models
_MODEL_REGISTRY: list[ModelConfig] = [
    # Groq models
    ModelConfig(
        name="llama-3.1-8b-instant",
        provider="groq",
        latency_ms=300,
        quality_score=0.80,
        offline_capable=False,
    ),
    ModelConfig(
        name="mixtral-8x7b-32768",
        provider="groq",
        latency_ms=600,
        quality_score=0.88,
        offline_capable=False,
    ),
    ModelConfig(
        name="llama-3.3-70b-versatile",
        provider="groq",
        latency_ms=800,
        quality_score=0.95,
        offline_capable=False,
    ),
    # OpenRouter models
    ModelConfig(
        name="google/gemini-2.0-flash-exp:free",
        provider="openrouter",
        latency_ms=400,
        quality_score=0.85,
        offline_capable=False,
    ),
    ModelConfig(
        name="meta-llama/llama-3.3-70b-instruct:free",
        provider="openrouter",
        latency_ms=500,
        quality_score=0.90,
        offline_capable=False,
    ),
    ModelConfig(
        name="deepseek/deepseek-r1:free",
        provider="openrouter",
        latency_ms=2000,
        quality_score=0.93,
        offline_capable=False,
    ),
    # Ollama (local/offline) models
    ModelConfig(
        name="phi3:mini",
        provider="ollama",
        latency_ms=3000,
        quality_score=0.65,
        offline_capable=True,
    ),
    ModelConfig(
        name="mistral:7b",
        provider="ollama",
        latency_ms=5000,
        quality_score=0.75,
        offline_capable=True,
    ),
    ModelConfig(
        name="qwen2.5:3b",
        provider="ollama",
        latency_ms=4000,
        quality_score=0.60,
        offline_capable=True,
    ),
]

# Keywords that indicate a complex task
_COMPLEX_KEYWORDS = {
    "explain",
    "analyze",
    "compare",
    "summarize",
    "write",
    "create",
    "generate",
    "design",
    "implement",
    "solve",
    "tushuntir",
    "tahlil",
    "solishtir",
    "yoz",
    "yaratish",
    "ishlab chiq",
    "qanday qilib",
    "nima uchun",
    "why",
    "how",
    "difference",
    "pros and cons",
}

# Keywords that indicate a simple lookup / trivial question
_TRIVIAL_KEYWORDS = {
    "hi",
    "hello",
    "salom",
    "assalomu alaykum",
    "hey",
    "thanks",
    "rahmat",
    "ok",
    "yes",
    "no",
    "ha",
    "yo'q",
    "bye",
    "xayr",
}


class ModelRouter:
    """Chooses the right model based on task complexity and constraints."""

    def __init__(self, registry: list[ModelConfig] | None = None) -> None:
        self._registry = registry or _MODEL_REGISTRY

    def get_models_except(self, model_name: str) -> list[ModelConfig]:
        """Return all registered models except the one with the given name."""
        return [m for m in self._registry if m.name != model_name]

    def classify_task(self, user_input: str) -> TaskComplexity:
        """Keyword-based heuristic to classify task complexity."""
        text = user_input.lower().strip()

        # Trivial: very short greetings / one-word answers
        if len(text.split()) <= 3 and any(kw in text for kw in _TRIVIAL_KEYWORDS):
            return TaskComplexity.TRIVIAL

        if any(kw in text for kw in _TRIVIAL_KEYWORDS):
            return TaskComplexity.SIMPLE

        # Complex: contains complex keywords or is long
        if any(kw in text for kw in _COMPLEX_KEYWORDS) or len(text.split()) > 20:
            return TaskComplexity.COMPLEX

        # Moderate: everything else of reasonable length
        if len(text.split()) > 8:
            return TaskComplexity.MODERATE

        return TaskComplexity.SIMPLE

    def select_model(
        self,
        user_input: str,
        force_offline: bool = False,
        available_providers: list[str] | None = None,
    ) -> ModelConfig:
        """Select the best model for the given input.

        Args:
            user_input: The user's message.
            force_offline: If True, only consider offline-capable models.
            available_providers: If given, only consider models from these providers.

        Returns:
            The chosen ModelConfig.

        Raises:
            RuntimeError: If no suitable model is found.
        """
        complexity = self.classify_task(user_input)
        candidates = self._registry

        if available_providers is not None:
            candidates = [m for m in candidates if m.provider in available_providers]
            if not candidates:
                raise RuntimeError(
                    f"No models available for providers: {available_providers}"
                )

        if force_offline:
            candidates = [m for m in candidates if m.offline_capable]
            if not candidates:
                raise RuntimeError("No offline-capable models available.")

        if complexity in (TaskComplexity.TRIVIAL, TaskComplexity.SIMPLE):
            # Fastest model (lowest latency)
            return min(candidates, key=lambda m: m.latency_ms)

        # MODERATE / COMPLEX: highest quality
        return max(candidates, key=lambda m: m.quality_score)
