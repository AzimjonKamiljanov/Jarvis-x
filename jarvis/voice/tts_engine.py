"""Text-to-Speech engine using pyttsx3 (offline, no model download needed)."""

from __future__ import annotations

import threading
from typing import Any


class TTSEngine:
    """Offline text-to-speech engine powered by pyttsx3."""

    def __init__(
        self,
        engine: str = "pyttsx3",
        rate: int = 175,
        voice_id: str | None = None,
    ) -> None:
        self._engine_name = engine
        self._rate = rate
        self._voice_id = voice_id
        self._engine: Any = None

    def _load(self) -> None:
        """Lazy-load pyttsx3 engine."""
        if self._engine is not None:
            return
        try:
            import pyttsx3  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError(
                "pyttsx3 is not installed. Run: pip install 'jarvis-x[voice]'"
            ) from exc

        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", self._rate)
        if self._voice_id:
            self._engine.setProperty("voice", self._voice_id)

    def is_available(self) -> bool:
        """Return True if pyttsx3 can be imported successfully."""
        try:
            import pyttsx3  # type: ignore[import]  # noqa: F401
        except ImportError:
            return False
        return True

    def speak(self, text: str) -> None:
        """Speak *text* through the speakers (blocking)."""
        if not self.is_available():
            raise RuntimeError(
                "TTS is not available. Run: pip install 'jarvis-x[voice]'"
            )
        self._load()
        assert self._engine is not None
        self._engine.say(text)
        self._engine.runAndWait()

    def speak_async(self, text: str) -> None:
        """Speak *text* in a background thread (non-blocking)."""
        thread = threading.Thread(target=self.speak, args=(text,), daemon=True)
        thread.start()

    def save_to_file(self, text: str, output_path: str) -> str:
        """Save speech audio to *output_path* (WAV).

        Returns:
            output_path
        """
        if not self.is_available():
            raise RuntimeError(
                "TTS is not available. Run: pip install 'jarvis-x[voice]'"
            )
        self._load()
        assert self._engine is not None
        self._engine.save_to_file(text, output_path)
        self._engine.runAndWait()
        return output_path

    def set_rate(self, rate: int) -> None:
        """Change speech rate (words per minute)."""
        self._rate = rate
        if self._engine is not None:
            self._engine.setProperty("rate", rate)

    def set_voice(self, voice_id: str) -> None:
        """Change the active voice by ID."""
        self._voice_id = voice_id
        if self._engine is not None:
            self._engine.setProperty("voice", voice_id)

    def list_voices(self) -> list[dict[str, str]]:
        """Return available voices as a list of dicts.

        Returns:
            [{"id": str, "name": str, "language": str}, ...]
        """
        if not self.is_available():
            raise RuntimeError(
                "TTS is not available. Run: pip install 'jarvis-x[voice]'"
            )
        self._load()
        assert self._engine is not None
        voices = self._engine.getProperty("voices")
        result: list[dict[str, str]] = []
        for v in voices:
            lang = ""
            if v.languages:
                raw_lang = v.languages[0]
                lang = raw_lang.decode() if isinstance(raw_lang, bytes) else str(raw_lang)
            result.append({"id": v.id, "name": v.name, "language": lang})
        return result
