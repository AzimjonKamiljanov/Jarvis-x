.PHONY: run chat test lint help

run:
	python -m jarvis

chat:
	python -m jarvis

test:
	pytest

lint:
	ruff check .

help:
	@echo "Available commands:"
	@echo "  make run    — Start JARVIS-X interactive mode"
	@echo "  make chat   — Alias for 'make run'"
	@echo "  make test   — Run tests with pytest"
	@echo "  make lint   — Lint code with ruff"
	@echo "  make help   — Show this help message"
