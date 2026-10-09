"""Intent parser — separates intent classification from audio/LLM logic."""

from __future__ import annotations

import re


class IntentParser:
    """Classifies user intent from raw text to determine routing/command execution."""

    def __init__(self) -> None:
        self._command_patterns = {
            "exit": re.compile(r"^(exit|quit|chiqish)$", re.IGNORECASE),
            "help": re.compile(r"^(help|yordam)$", re.IGNORECASE),
            "status": re.compile(r"^(status|holat)$", re.IGNORECASE),
            # Add more specific command patterns here in the future
        }

    def parse_intent(self, user_text: str) -> dict[str, str | None]:
        """Parse user text and return classified intent.

        Returns:
            dict with keys 'intent' (e.g., 'command', 'chat') and 'action' (if command).
        """
        text = user_text.strip()
        if not text:
            return {"intent": "empty", "action": None}

        for action, pattern in self._command_patterns.items():
            if pattern.search(text):
                return {"intent": "command", "action": action}

        return {"intent": "chat", "action": None}
