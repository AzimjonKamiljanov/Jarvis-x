"""Tests for intent parsing and command execution."""

from jarvis.core.intent_parser import IntentParser


def test_intent_parser_chat():
    parser = IntentParser()
    result = parser.parse_intent("Hello Jarvis, how are you?")
    assert result["intent"] == "chat"
    assert result["action"] is None

def test_intent_parser_commands():
    parser = IntentParser()

    result = parser.parse_intent("exit")
    assert result["intent"] == "command"
    assert result["action"] == "exit"

    result = parser.parse_intent("quit")
    assert result["intent"] == "command"
    assert result["action"] == "exit"

    result = parser.parse_intent("chiqish")
    assert result["intent"] == "command"
    assert result["action"] == "exit"

    result = parser.parse_intent("help")
    assert result["intent"] == "command"
    assert result["action"] == "help"

    result = parser.parse_intent("status")
    assert result["intent"] == "command"
    assert result["action"] == "status"

def test_intent_parser_empty():
    parser = IntentParser()
    result = parser.parse_intent("")
    assert result["intent"] == "empty"
    assert result["action"] is None

    result = parser.parse_intent("   ")
    assert result["intent"] == "empty"
    assert result["action"] is None
