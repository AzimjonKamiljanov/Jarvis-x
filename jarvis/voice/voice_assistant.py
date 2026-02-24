"""Main voice assistant — combines STT, TTS, and the orchestrator."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from rich.console import Console

from jarvis.voice.audio_stream import AudioStream
from jarvis.voice.stt_engine import STTEngine
from jarvis.voice.tts_engine import TTSEngine

if TYPE_CHECKING:
    from jarvis.core.orchestrator import JarvisOrchestrator

console = Console()


class VoiceAssistant:
    """End-to-end voice assistant: microphone → STT → orchestrator → TTS → speaker."""

    def __init__(
        self,
        orchestrator: JarvisOrchestrator,
        config: dict | None = None,
    ) -> None:
        cfg = config or {}
        self._orchestrator = orchestrator
        self._session_id = str(uuid.uuid4())

        self._stt = STTEngine(
            model_path=cfg.get("stt_model_path"),
            sample_rate=cfg.get("sample_rate", 16000),
        )
        self._tts = TTSEngine(
            engine=cfg.get("tts_engine", "pyttsx3"),
            rate=cfg.get("tts_rate", 175),
        )
        self._audio = AudioStream(
            sample_rate=cfg.get("sample_rate", 16000),
            channels=1,
            chunk_duration=0.5,
        )
        self._silence_threshold: float = cfg.get("silence_threshold", 0.01)
        self._silence_duration: float = cfg.get("silence_duration", 1.5)
        self._max_record_duration: float = cfg.get("max_record_duration", 30.0)

    def is_available(self) -> bool:
        """Return True only when all three voice components are ready."""
        return self._stt.is_available() and self._tts.is_available() and self._audio.is_available()

    def get_status(self) -> dict[str, bool]:
        """Return availability of each component.

        Returns:
            {"stt": bool, "tts": bool, "microphone": bool}
        """
        return {
            "stt": self._stt.is_available(),
            "tts": self._tts.is_available(),
            "microphone": self._audio.is_available(),
        }

    async def listen_and_respond(self) -> dict[str, str]:
        """One full voice turn: record → transcribe → AI response → speak.

        Returns:
            {"user_text": str, "response": str, "model_used": str}
        """
        # 1. Record audio
        audio_data = self._audio.record_until_silence(
            silence_threshold=self._silence_threshold,
            silence_duration=self._silence_duration,
            max_duration=self._max_record_duration,
        )

        # 2. Transcribe
        stt_result = self._stt.transcribe_audio(audio_data)
        user_text: str = str(stt_result.get("text", "")).strip()

        if not user_text:
            return {"user_text": "", "response": "", "model_used": ""}

        console.print(f"[bold cyan]You:[/bold cyan] {user_text}")

        # 3. Get AI response
        result = await self._orchestrator.process_message(
            user_input=user_text,
            session_id=self._session_id,
        )
        response_text: str = result["response"]
        model_used: str = result["model_used"]

        console.print(f"[bold green]JARVIS:[/bold green] {response_text}")

        # 4. Speak response
        self._tts.speak_async(response_text)

        return {
            "user_text": user_text,
            "response": response_text,
            "model_used": model_used,
        }

    async def run_voice_loop(self) -> None:
        """Continuous voice interaction loop."""
        console.print(
            "[bold cyan]🎙️  Voice mode active.[/bold cyan] "
            "[dim]Say 'exit', 'quit', or 'chiqish' to stop.[/dim]"
        )

        try:
            while True:
                console.print("\n[bold yellow]🎤 Listening…[/bold yellow]")
                result = await self.listen_and_respond()

                if not result["user_text"]:
                    continue

                if result["user_text"].lower() in {"exit", "quit", "chiqish"}:
                    console.print("[dim]Goodbye! / Xayr![/dim]")
                    break
        except KeyboardInterrupt:
            console.print("\n[dim]Voice mode stopped. Goodbye![/dim]")
