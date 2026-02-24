"""FastAPI application for JARVIS-X."""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from jarvis.core.orchestrator import JarvisOrchestrator

_orchestrator: JarvisOrchestrator | None = None


@asynccontextmanager
async def _lifespan(app: FastAPI):  # noqa: ANN001
    global _orchestrator
    _orchestrator = JarvisOrchestrator()
    await _orchestrator.initialize()
    yield


app = FastAPI(title="JARVIS-X API", version="0.1.0", lifespan=_lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_orchestrator() -> JarvisOrchestrator:
    assert _orchestrator is not None, "Orchestrator not initialized"
    return _orchestrator


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    force_offline: bool = False


class ChatResponse(BaseModel):
    response: str
    session_id: str
    model_used: str
    response_time: float


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    orchestrator = _get_orchestrator()
    session_id = req.session_id or str(uuid.uuid4())
    result = await orchestrator.process_message(
        user_input=req.message,
        session_id=session_id,
        force_offline=req.force_offline,
    )
    return ChatResponse(
        response=result["response"],
        session_id=session_id,
        model_used=result["model_used"],
        response_time=result["response_time"],
    )


@app.get("/api/chat/stream")
async def chat_stream(
    message: str,
    session_id: str | None = None,
) -> StreamingResponse:
    orchestrator = _get_orchestrator()
    sid = session_id or str(uuid.uuid4())

    async def _event_generator() -> Any:
        async for chunk in orchestrator.process_stream(
            user_input=message, session_id=sid
        ):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(_event_generator(), media_type="text/event-stream")


@app.get("/api/health")
async def health() -> dict:
    orchestrator = _get_orchestrator()
    providers = orchestrator.get_available_providers()
    memory_entries = orchestrator.get_memory_count()
    return {
        "status": "operational",
        "providers": providers,
        "memory_entries": memory_entries,
    }


@app.get("/api/system/stats")
async def system_stats() -> dict:
    try:
        import psutil  # type: ignore[import]

        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "ram_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
        }
    except ImportError:
        return {"error": "psutil not installed"}


@app.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket) -> None:
    await websocket.accept()
    orchestrator = _get_orchestrator()
    session_id = str(uuid.uuid4())
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            stream = data.get("stream", False)

            if stream:
                async for chunk in orchestrator.process_stream(
                    user_input=message, session_id=session_id
                ):
                    await websocket.send_json({"type": "chunk", "content": chunk})
                await websocket.send_json({"type": "done", "content": ""})
            else:
                result = await orchestrator.process_message(
                    user_input=message, session_id=session_id
                )
                await websocket.send_json(
                    {"type": "response", "content": result["response"]}
                )
    except WebSocketDisconnect:
        pass
