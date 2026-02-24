.PHONY: run chat test lint api api-prod voice voice-test install-voice help

run:
	python -m jarvis

chat:
	python -m jarvis

test:
	pytest

lint:
	ruff check .

api:
	uvicorn jarvis.api.main:app --reload --host 0.0.0.0 --port 8000

api-prod:
	uvicorn jarvis.api.main:app --host 0.0.0.0 --port 8000

voice:
	python -m jarvis --voice

voice-test:
	python -m jarvis --voice-test

install-voice:
	pip install -e ".[voice]"

help:
	@echo "Available commands:"
	@echo "  make run          — Start JARVIS-X interactive mode"
	@echo "  make chat         — Alias for 'make run'"
	@echo "  make test         — Run tests with pytest"
	@echo "  make lint         — Lint code with ruff"
	@echo "  make api          — Start FastAPI server (dev mode with reload)"
	@echo "  make api-prod     — Start FastAPI server (production mode)"
	@echo "  make voice        — Start voice assistant mode"
	@echo "  make voice-test   — Test voice components (STT, TTS, mic)"
	@echo "  make install-voice — Install voice dependencies"
	@echo "  make help         — Show this help message"
