"""Speech-to-Text engine using Vosk for offline recognition."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

_DEFAULT_MODEL_PATH = "./models/vosk-model-small-en-us"


class STTEngine:
    """Offline speech-to-text engine powered by Vosk."""

    def __init__(self, model_path: str | None = None, sample_rate: int = 16000) -> None:
        self._model_path = model_path or _DEFAULT_MODEL_PATH
        self._sample_rate = sample_rate
        self._model = None
        self._vosk = None

    def _load(self) -> None:
        """Lazy-load Vosk model."""
        if self._model is not None:
            return
        try:
            import vosk  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError(
                "vosk is not installed. Run: pip install 'jarvis-x[voice]'"
            ) from exc

        if not os.path.isdir(self._model_path):
            raise RuntimeError(
                f"Vosk model not found at '{self._model_path}'. "
                "Run: bash scripts/download_vosk_model.sh"
            )

        vosk.SetLogLevel(-1)
        self._vosk = vosk
        self._model = vosk.Model(self._model_path)

    def is_available(self) -> bool:
        """Return True if Vosk is installed and the model directory exists."""
        try:
            import vosk  # type: ignore[import]  # noqa: F401
        except ImportError:
            return False
        return os.path.isdir(self._model_path)

    def transcribe_audio(self, audio_data: bytes) -> dict[str, object]:
        """Transcribe raw PCM 16-bit audio bytes.

        Returns:
            {"text": str, "confidence": float}
        """
        if not self.is_available():
            raise RuntimeError(
                "STT is not available. Install vosk and download the model first."
            )
        self._load()
        assert self._vosk is not None and self._model is not None
        rec = self._vosk.KaldiRecognizer(self._model, self._sample_rate)
        rec.AcceptWaveform(audio_data)
        raw = json.loads(rec.FinalResult())
        text: str = raw.get("text", "")
        confidence: float = raw.get("confidence", 1.0) if text else 0.0
        return {"text": text, "confidence": confidence}

    def transcribe_file(self, file_path: str) -> dict[str, object]:
        """Read a WAV file and transcribe it.

        Returns:
            {"text": str, "confidence": float}
        """
        import wave

        if not self.is_available():
            raise RuntimeError(
                "STT is not available. Install vosk and download the model first."
            )
        self._load()
        assert self._vosk is not None and self._model is not None

        with wave.open(file_path, "rb") as wf:
            sample_rate = wf.getframerate()
            rec = self._vosk.KaldiRecognizer(self._model, sample_rate)
            audio_data = wf.readframes(wf.getnframes())

        rec.AcceptWaveform(audio_data)
        raw = json.loads(rec.FinalResult())
        text: str = raw.get("text", "")
        confidence: float = raw.get("confidence", 1.0) if text else 0.0
        return {"text": text, "confidence": confidence}
