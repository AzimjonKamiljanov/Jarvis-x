"""Microphone audio capture using sounddevice."""

from __future__ import annotations

import io
import math
import wave
from typing import Any


class AudioStream:
    """Real-time microphone input powered by sounddevice."""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_duration: float = 0.5,
    ) -> None:
        self._sample_rate = sample_rate
        self._channels = channels
        self._chunk_duration = chunk_duration

    def _sd(self) -> Any:
        """Return the sounddevice module, raising RuntimeError if unavailable."""
        try:
            import sounddevice as sd  # type: ignore[import]

            return sd
        except ImportError as exc:
            raise RuntimeError(
                "sounddevice is not installed. Run: pip install 'jarvis-x[voice]'"
            ) from exc

    def _np(self) -> Any:
        """Return the numpy module, raising RuntimeError if unavailable."""
        try:
            import numpy as np  # type: ignore[import]

            return np
        except ImportError as exc:
            raise RuntimeError(
                "numpy is not installed. Run: pip install 'jarvis-x[voice]'"
            ) from exc

    def is_available(self) -> bool:
        """Return True if sounddevice is installed and a microphone exists."""
        try:
            import sounddevice as sd  # type: ignore[import]

            sd.query_devices(kind="input")
            return True
        except (ImportError, OSError):
            return False

    def record_seconds(self, duration: float) -> bytes:
        """Record for *duration* seconds and return raw PCM (int16) bytes."""
        sd = self._sd()
        self._np()  # ensure numpy is available
        audio = sd.rec(
            int(duration * self._sample_rate),
            samplerate=self._sample_rate,
            channels=self._channels,
            dtype="int16",
        )
        sd.wait()
        return audio.tobytes()

    def record_until_silence(
        self,
        silence_threshold: float = 0.01,
        silence_duration: float = 1.5,
        max_duration: float = 30.0,
    ) -> bytes:
        """Record from microphone until silence is detected.

        Uses RMS energy to detect silence.

        Returns:
            Raw PCM int16 bytes.
        """
        sd = self._sd()
        np = self._np()

        chunk_frames = int(self._sample_rate * self._chunk_duration)
        max_frames = int(self._sample_rate * max_duration)
        silence_frames_needed = int(silence_duration / self._chunk_duration)

        frames: list[Any] = []
        silent_chunks = 0
        total_frames = 0

        with sd.InputStream(
            samplerate=self._sample_rate,
            channels=self._channels,
            dtype="int16",
            blocksize=chunk_frames,
        ) as stream:
            while total_frames < max_frames:
                chunk, _ = stream.read(chunk_frames)
                frames.append(chunk.copy())
                total_frames += chunk_frames

                # Compute RMS energy
                rms = math.sqrt(np.mean(chunk.astype(np.float32) ** 2)) / 32768.0
                if rms < silence_threshold:
                    silent_chunks += 1
                else:
                    silent_chunks = 0

                if silent_chunks >= silence_frames_needed and total_frames > chunk_frames:
                    break

        if not frames:
            return b""
        audio = np.concatenate(frames, axis=0)
        return audio.tobytes()

    def save_wav(self, audio_data: bytes, file_path: str, sample_rate: int = 16000) -> str:
        """Save PCM int16 *audio_data* to *file_path* as a WAV file.

        Returns:
            file_path
        """
        with wave.open(file_path, "wb") as wf:
            wf.setnchannels(self._channels)
            wf.setsampwidth(2)  # int16 → 2 bytes
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data)
        return file_path

    def bytes_to_wav_bytes(self, audio_data: bytes, sample_rate: int = 16000) -> bytes:
        """Convert raw PCM bytes to in-memory WAV bytes."""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(self._channels)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data)
        return buf.getvalue()
