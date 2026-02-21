"""Abstract base class for AI providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator


class ProviderError(Exception):
    """Raised when an AI provider encounters an error."""


class BaseProvider(ABC):
    """Abstract base class that all AI providers must implement."""

    @abstractmethod
    async def generate(
        self,
        messages: list[dict],
        model: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        """Generate a full response from the provider.

        Args:
            messages: List of OpenAI-format message dicts with 'role' and 'content'.
            model: Model identifier to use.
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature (0.0–2.0).

        Returns:
            The generated text response.

        Raises:
            ProviderError: On API or network errors.
        """

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[dict],
        model: str,
    ) -> AsyncGenerator[str, None]:
        """Stream a response token-by-token.

        Args:
            messages: List of OpenAI-format message dicts.
            model: Model identifier to use.

        Yields:
            Successive text chunks from the model.

        Raises:
            ProviderError: On API or network errors.
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this provider is properly configured and ready."""
