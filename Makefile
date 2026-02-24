.PHONY: run chat test lint api api-prod help

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

help:
	@echo "Available commands:"
	@echo "  make run      — Start JARVIS-X interactive mode"
	@echo "  make chat     — Alias for 'make run'"
	@echo "  make test     — Run tests with pytest"
	@echo "  make lint     — Lint code with ruff"
	@echo "  make api      — Start FastAPI server (dev mode with reload)"
	@echo "  make api-prod — Start FastAPI server (production mode)"
	@echo "  make help     — Show this help message"
