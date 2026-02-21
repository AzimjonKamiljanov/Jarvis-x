# 🤖 JARVIS-X

**Next-gen AI assistant — modular, multilingual (EN/UZ), production-ready**

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Features

- 🚀 **Fast responses** via Groq API (llama-3.3-70b-versatile, llama-3.1-8b-instant, mixtral-8x7b-32768)
- 🌍 **Multilingual** — fully supports Uzbek 🇺🇿 and English 🇬🇧
- 🧠 **Smart model routing** — automatically selects the best model based on task complexity
- 💬 **Short-term memory** — sliding-window conversation context per session
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

### 3. Set your API key

```bash
cp .env.example .env
# Edit .env and add your Groq API key
export GROQ_API_KEY=your_groq_api_key_here
```

Get a free Groq API key at <https://console.groq.com>.

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
usage: jarvis [-h] [--offline] [--model MODEL] [--config PATH] [message]

positional arguments:
  message          Message to send (optional; omit for REPL)

options:
  --offline        Use only offline-capable models
  --model MODEL    Force a specific model
  --config PATH    Path to jarvis_config.yaml
```

### Examples

```bash
# Force a specific model
python -m jarvis --model llama-3.1-8b-instant "Quick question"

# Use a custom config file
python -m jarvis --config /path/to/my_config.yaml

# Interactive mode with make
make run
```

---

## Architecture

```
jarvis/
├── __init__.py          # Version info
├── __main__.py          # CLI entry point
├── core/
│   ├── config.py        # YAML config loader (JarvisConfig dataclass)
│   └── orchestrator.py  # Main brain — connects all modules
├── ai/
│   ├── model_router.py  # Smart model selection (TaskComplexity enum)
│   └── providers/
│       ├── base.py      # Abstract BaseProvider + ProviderError
│       └── groq_provider.py  # Groq API provider
└── memory/
    └── short_term.py    # Sliding-window conversation memory

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

- [ ] Streaming responses in the terminal
- [ ] Offline LLM support (Ollama integration)
- [ ] Long-term memory with vector search
- [ ] Voice input/output
- [ ] Plugin system

---

## License

MIT © 2024 AzimjonKamiljanov
