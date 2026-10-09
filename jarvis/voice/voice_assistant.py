"""Main voice assistant — combines STT, TTS, and the orchestrator."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from rich.console import Console

from jarvis.core.intent_parser import IntentParser
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
        self._intent_parser = IntentParser()
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

        intent_data = self._intent_parser.parse_intent(user_text)
        if intent_data["intent"] == "command":
            action = intent_data["action"]
            if action in ("exit", "quit", "chiqish"):
                return {"user_text": user_text, "response": "exit", "model_used": "system"}
            elif action == "help":
                response_text = "I am Jarvis. How can I help you?"
                self._tts.speak_async(response_text)
                return {"user_text": user_text, "response": response_text, "model_used": "system"}
            elif action == "status":
                response_text = "All systems operational."
                self._tts.speak_async(response_text)
                return {"user_text": user_text, "response": response_text, "model_used": "system"}

        # 3. Get AI response (streamed for lower latency TTS)
        console.print("[bold green]JARVIS:[/bold green] ", end="")
        full_response = []
        sentence_buffer = ""

        # Using a simple sentence boundary detection (. ? !)
        async for chunk in self._orchestrator.process_stream(
            user_input=user_text,
            session_id=self._session_id,
        ):
            console.print(chunk, end="")
            full_response.append(chunk)
            sentence_buffer += chunk

            # Find the first punctuation mark that indicates a sentence boundary
            split_char = None
            split_idx = -1
            for char in [".", "?", "!", "\n"]:
                idx = sentence_buffer.find(char)
                if idx != -1 and (split_idx == -1 or idx < split_idx):
                    split_idx = idx
                    split_char = char

            if split_char is not None and split_idx != -1:
                # Speak the buffered sentence up to the punctuation mark
                sentence = sentence_buffer[:split_idx + 1]
                if sentence.strip():
                    self._tts.speak_async(sentence.strip())
                sentence_buffer = sentence_buffer[split_idx + 1:]

        console.print()

        # Speak any remaining text
        if sentence_buffer.strip():
            self._tts.speak_async(sentence_buffer.strip())

        response_text = "".join(full_response)

        # We don't have model_used from process_stream directly in the output,
        # so we'll just return 'streamed' for now, or adapt later if needed.
        return {
            "user_text": user_text,
            "response": response_text,
            "model_used": "streamed",
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

                if result["response"] == "exit" and result["model_used"] == "system":
                    console.print("[dim]Goodbye! / Xayr![/dim]")
                    break
        except KeyboardInterrupt:
            console.print("\n[dim]Voice mode stopped. Goodbye![/dim]")
