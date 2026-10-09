# 🤖 JARVIS-X

**An elite cutting-edge AI Voice & Autonomous Automation Assistant**

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI/CD](https://github.com/AzimjonKamiljanov/Jarvis-x/actions/workflows/ci.yml/badge.svg)](https://github.com/AzimjonKamiljanov/Jarvis-x/actions)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](#docker)

JARVIS-X is a next-generation AI assistant built with a modular, highly extensible architecture. Designed for speed and autonomy, it features a robust multimodal voice pipeline, smart fallback capabilities, multi-provider routing (Groq, OpenRouter, Ollama), and dynamic memory management.

---

## 🚀 Key Features

*   **⚡ Ultra-Low Latency Voice Pipeline**: Streaming intent classification, text-to-speech, and speech-to-text powered by robust audio buffer management. Responses are spoken as they are generated!
*   **🌐 Multi-Provider AI Routing**: Intelligent model selection and graceful fallback mechanisms across Groq, OpenRouter, and Ollama.
*   **🧠 Dynamic Memory Systems**: Short-term sliding-window conversation context, paired with optional ChromaDB vector storage for long-term semantic recall.
*   **🔌 Modular & Autonomous Architecture**: Strict separation of concerns (audio capture, intent classification, orchestration) makes JARVIS-X incredibly extensible and robust.
*   **🌍 Multilingual**: Fluent in both English 🇬🇧 and Uzbek 🇺🇿.
*   **💻 Multichannel Interfaces**: Accessible via a beautiful terminal UI (powered by `rich`), Voice mode, and a full-featured REST/WebSocket API via FastAPI.

---

## 🏗️ System Architecture

JARVIS-X follows a clean, modular architecture, ensuring separation between capture, processing, and execution.

```mermaid
graph TD
    User((User)) -->|Voice / Text| Input
    Input --> IntentParser
    IntentParser --> |Command| CommandExecutor
    IntentParser --> |Chat| Orchestrator

    Orchestrator --> MemoryManager[Memory (Short & Long)]
    Orchestrator --> ModelRouter

    ModelRouter --> Groq
    ModelRouter --> OpenRouter
    ModelRouter --> Ollama

    Groq --> Orchestrator
    OpenRouter --> Orchestrator
    Ollama --> Orchestrator

    Orchestrator --> |Streaming Chunks| VoiceAssistant
    VoiceAssistant --> |TTS| Output((Speaker / Terminal))
```

### Request Pipeline Detail

1.  **Audio Capture (Microphone)**: Captures audio until silence is detected.
2.  **STT (Speech-to-Text)**: Vosk transcriber converts raw PCM to text.
3.  **Intent Classification**: Analyzes text to determine if it's a built-in command or a general AI query.
4.  **Orchestrator & Routing**: Retrieves context from memory and dynamically routes the prompt to the best available model.
5.  **Streaming AI Generation**: Provider generates responses. If a provider fails, JARVIS-X seamlessly falls back to the next best model.
6.  **Streaming TTS**: As sentences are generated, the TTS engine converts and speaks them immediately for lowest latency.

---

## 🛠️ Quickstart Guide

### 1. Installation

```bash
git clone https://github.com/AzimjonKamiljanov/Jarvis-x.git
cd Jarvis-x

# Install base dependencies
pip install -e .

# Install with all bells and whistles (Dev + Voice + Memory)
pip install -e ".[dev,voice,memory]"
```

### 2. Configuration & Secrets

Copy the example environment file and configure your keys.

```bash
cp .env.example .env
```

Edit `.env` to include your API keys:

```env
GROQ_API_KEY=your_groq_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
OLLAMA_BASE_URL=http://localhost:11434
VOSK_MODEL_PATH=./models/vosk-model-small-en-us
```

### 3. Audio & Hardware Configuration (Voice Mode)

JARVIS-X requires the Vosk STT model to operate in voice mode. We've provided a helper script:

```bash
bash scripts/download_vosk_model.sh
```

Ensure your microphone and speakers are correctly configured. You can test your hardware integration using:

```bash
make voice-test
# or
python -m jarvis --voice-test
```

---

## 💬 Interactive Command Examples

JARVIS-X supports numerous running modes to fit your workflow.

### Voice Mode

Engage the fully autonomous voice pipeline:

```bash
make voice
# or
python -m jarvis --voice
```
*(Say "exit", "quit", or "chiqish" to stop the loop)*

### CLI Chat Mode

Interact with JARVIS-X directly from your terminal:

```bash
# Single Question
jarvis "What is the capital of France?"

# Streaming Mode
jarvis --stream "Write a python script for a simple web server."

# Interactive REPL
jarvis
```

### REST API Server

Launch the FastAPI server to interface via HTTP, SSE, or WebSockets:

```bash
make api
# or
jarvis --api
```

Test the API via cURL:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello Jarvis!", "session_id": "test-session"}'
```

---

## 🐳 Docker Deployment <a name="docker"></a>

Run JARVIS-X seamlessly via Docker (API mode):

```bash
# Build the image
docker build -t jarvis-x .

# Run the container (Make sure to map your .env)
docker run -p 8000:8000 --env-file .env jarvis-x
```

---

## 🔧 Extending & Developing

To add new providers, implement the `BaseProvider` interface in `jarvis/ai/providers/`.
To register new custom commands, extend the logic within `jarvis/core/intent_parser.py`.

Run tests:

```bash
make test
```

## License

MIT © 2024 AzimjonKamiljanov
