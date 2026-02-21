"""Configuration loader for JARVIS-X."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv


@dataclass
class ProviderModelConfig:
    name: str
    latency_ms: int
    quality_score: float
    offline_capable: bool


@dataclass
class GroqProviderConfig:
    api_endpoint: str = "https://api.groq.com/openai/v1"
    models: list[ProviderModelConfig] = field(default_factory=list)


@dataclass
class AIConfig:
    default_provider: str = "groq"
    temperature: float = 0.7
    max_tokens: int = 2048
    model_preferences: dict[str, str] = field(
        default_factory=lambda: {
            "trivial": "llama-3.1-8b-instant",
            "simple": "llama-3.1-8b-instant",
            "moderate": "llama-3.3-70b-versatile",
            "complex": "llama-3.3-70b-versatile",
        }
    )


@dataclass
class MemoryConfig:
    short_term_limit: int = 20


@dataclass
class SystemConfig:
    language: str = "uz"
    debug: bool = False


@dataclass
class JarvisConfig:
    ai: AIConfig = field(default_factory=AIConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    system: SystemConfig = field(default_factory=SystemConfig)
    groq: GroqProviderConfig = field(default_factory=GroqProviderConfig)


def load_config(path: str | None = None) -> JarvisConfig:
    """Load configuration from a YAML file and .env, returning a JarvisConfig."""
    load_dotenv()

    raw: dict = {}
    if path and Path(path).exists():
        with open(path) as fh:
            raw = yaml.safe_load(fh) or {}
    else:
        default_path = Path(__file__).parent.parent.parent / "config" / "jarvis_config.yaml"
        if default_path.exists():
            with open(default_path) as fh:
                raw = yaml.safe_load(fh) or {}

    ai_raw = raw.get("ai", {})
    ai_config = AIConfig(
        default_provider=ai_raw.get("default_provider", "groq"),
        temperature=float(ai_raw.get("temperature", 0.7)),
        max_tokens=int(ai_raw.get("max_tokens", 2048)),
        model_preferences=ai_raw.get(
            "model_preferences",
            {
                "trivial": "llama-3.1-8b-instant",
                "simple": "llama-3.1-8b-instant",
                "moderate": "llama-3.3-70b-versatile",
                "complex": "llama-3.3-70b-versatile",
            },
        ),
    )

    mem_raw = raw.get("memory", {})
    memory_config = MemoryConfig(short_term_limit=int(mem_raw.get("short_term_limit", 20)))

    sys_raw = raw.get("system", {})
    system_config = SystemConfig(
        language=sys_raw.get("language", "uz"),
        debug=bool(sys_raw.get("debug", False)),
    )

    providers_raw = raw.get("providers", {})
    groq_raw = providers_raw.get("groq", {})
    groq_models = [
        ProviderModelConfig(
            name=m["name"],
            latency_ms=int(m.get("latency_ms", 500)),
            quality_score=float(m.get("quality_score", 0.8)),
            offline_capable=bool(m.get("offline_capable", False)),
        )
        for m in groq_raw.get("models", [])
    ]
    groq_config = GroqProviderConfig(
        api_endpoint=groq_raw.get("api_endpoint", "https://api.groq.com/openai/v1"),
        models=groq_models,
    )

    _validate_api_keys()

    return JarvisConfig(
        ai=ai_config,
        memory=memory_config,
        system=system_config,
        groq=groq_config,
    )


def _validate_api_keys() -> None:
    """Warn if required API keys are missing."""
    if not os.environ.get("GROQ_API_KEY"):
        import warnings

        warnings.warn(
            "GROQ_API_KEY environment variable is not set. "
            "Groq provider will not be available. "
            "Set it via: export GROQ_API_KEY=your_key_here",
            stacklevel=3,
        )
