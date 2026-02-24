# 🤖 JARVIS-X

**Next-gen AI assistant — modular, multilingual (EN/UZ), production-ready**

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Features

- 🚀 **Fast responses** via Groq API (llama-3.3-70b-versatile, llama-3.1-8b-instant, mixtral-8x7b-32768)
- 🌐 **Multi-provider** — Groq, OpenRouter (Claude, GPT, Gemini, free models), Ollama (local/offline)
- 🌍 **Multilingual** — fully supports Uzbek 🇺🇿 and English 🇬🇧
- 🧠 **Smart model routing** — automatically selects the best model based on task complexity and provider availability
- 💬 **Short-term memory** — sliding-window conversation context per session
- 🗄️ **Long-term memory** — optional ChromaDB vector storage for semantic search across past interactions
- ⚡ **Streaming** — real-time token streaming in CLI and API
- 🌐 **REST API** — FastAPI server with HTTP, Server-Sent Events, and WebSocket endpoints
- 🎨 **Beautiful terminal UI** — powered by `rich` (ASCII banner, colored output, response time)
- ⚡ **Async-first** — all I/O operations use `async/await`
- 🛡️ **Graceful error handling** — fallback providers, rate-limit awareness
- 🔧 **Configurable** — YAML config file + `.env` for secrets

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/AzimjonKamiljanov/Jarvis-x.git
cd Jarvis-x
```

### 2. Install

```bash
pip install -e .
```

### 3. Set your API keys

```bash
cp .env.example .env
# Edit .env and add your API keys
export GROQ_API_KEY=your_groq_api_key_here
export OPENROUTER_API_KEY=your_openrouter_api_key_here  # optional
# For Ollama (local), no key needed — just have Ollama running
```

Get a free Groq API key at <https://console.groq.com>.
Get a free OpenRouter API key at <https://openrouter.ai>.

### 4. Run

```bash
# Single message
python -m jarvis "Salom, qanday yordam bera olasiz?"

# Interactive REPL
python -m jarvis

# Or via the installed script
jarvis "Hello, what can you do?"
```

---

## Usage

```
usage: jarvis [-h] [--offline] [--model MODEL] [--config PATH] [--api] [--stream] [message]

positional arguments:
  message          Message to send (optional; omit for REPL)

options:
  --offline        Use only offline-capable models
  --model MODEL    Force a specific model
  --config PATH    Path to jarvis_config.yaml
  --api            Start the FastAPI server
  --stream         Stream the response in CLI mode
```

### Examples

```bash
# Force a specific model
python -m jarvis --model llama-3.1-8b-instant "Quick question"

# Use a custom config file
python -m jarvis --config /path/to/my_config.yaml

# Stream response in CLI
python -m jarvis --stream "Explain async/await in Python"

# Interactive mode with make
make run

# Start REST API server
make api
# or
python -m jarvis --api
```

---

## Providers

### Groq (default)
Fast cloud inference. Set `GROQ_API_KEY` in your `.env`.
Models: `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `mixtral-8x7b-32768`

### OpenRouter
Access to Claude, GPT, Gemini, and many free models. Set `OPENROUTER_API_KEY` in your `.env`.
Free models: `google/gemini-2.0-flash-exp:free`, `meta-llama/llama-3.3-70b-instruct:free`, `deepseek/deepseek-r1:free`

### Ollama (local/offline)
Run models locally with [Ollama](https://ollama.ai). No API key required.
```bash
# Install Ollama and pull a model
ollama pull phi3:mini
# Then use JARVIS-X in offline mode
python -m jarvis --offline "Hello"
```

---

## REST API

Start the server:
```bash
make api
# or
python -m jarvis --api
```

### Endpoints

**POST /api/chat** — Send a message
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "session_id": "my-session"}'
```

**GET /api/chat/stream** — Server-Sent Events streaming
```bash
curl "http://localhost:8000/api/chat/stream?message=Hello&session_id=my-session"
```

**GET /api/health** — Health check
```bash
curl http://localhost:8000/api/health
```

**GET /api/system/stats** — CPU, RAM, disk usage
```bash
curl http://localhost:8000/api/system/stats
```

**WebSocket /ws/chat** — Real-time chat
```javascript
const ws = new WebSocket("ws://localhost:8000/ws/chat");
ws.send(JSON.stringify({"message": "Hello!", "stream": true}));
```

---

## Memory

JARVIS-X supports two memory tiers:

- **Short-term** — sliding-window conversation history per session (always active)
- **Long-term** — ChromaDB vector storage for semantic search across all past interactions (optional)

To enable long-term memory:
```bash
pip install "jarvis-x[memory]"
```

---

## Architecture

```
jarvis/
├── __init__.py          # Version info
├── __main__.py          # CLI entry point (--api, --stream flags)
├── api/
│   ├── __init__.py
│   └── main.py          # FastAPI app (REST + WebSocket)
├── core/
│   ├── config.py        # YAML config loader (JarvisConfig dataclass)
│   └── orchestrator.py  # Main brain — connects all modules
├── ai/
│   ├── model_router.py  # Smart model selection (TaskComplexity enum)
│   └── providers/
│       ├── base.py              # Abstract BaseProvider + ProviderError
│       ├── groq_provider.py     # Groq API provider
│       ├── openrouter_provider.py  # OpenRouter provider
│       └── ollama_provider.py   # Ollama local provider
└── memory/
    ├── short_term.py    # Sliding-window conversation memory
    ├── long_term.py     # ChromaDB vector storage
    └── memory_manager.py  # Unified memory interface

config/
└── jarvis_config.yaml   # Main configuration
```

### Request pipeline

```
User input
    │
    ▼
ShortTermMemory.add()          ← save user message
    │
    ▼
ModelRouter.classify_task()    ← heuristic complexity detection
    │
    ▼
ModelRouter.select_model()     ← pick fastest / highest-quality model
    │
    ▼
GroqProvider.generate()        ← async API call (with fallback)
    │
    ▼
ShortTermMemory.add()          ← save assistant response
    │
    ▼
Return {response, model_used, response_time}
```

---

## Configuration

Edit `config/jarvis_config.yaml`:

```yaml
ai:
  default_provider: groq
  temperature: 0.7
  max_tokens: 2048

memory:
  short_term_limit: 20   # sliding window size

system:
  language: uz           # uz | en
  debug: false
```

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
make test

# Lint
make lint
```

---

## Roadmap

- [x] Streaming responses in the terminal
- [x] Offline LLM support (Ollama integration)
- [x] Long-term memory with vector search
- [x] REST API (FastAPI)
- [ ] Voice input/output
- [ ] Plugin system

---

## License

MIT © 2024 AzimjonKamiljanov
