"""CLI entry point for JARVIS-X.

Usage:
    python -m jarvis "Your message here"
    python -m jarvis                    # interactive REPL
    python -m jarvis --offline "Hi"
    python -m jarvis --model llama-3.1-8b-instant "Hello"
    python -m jarvis --config /path/to/config.yaml
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from jarvis import __app_name__, __version__
from jarvis.core.config import load_config
from jarvis.core.orchestrator import JarvisOrchestrator

console = Console()

_BANNER = r"""
     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗    ██╗  ██╗
     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝    ╚██╗██╔╝
     ██║███████║██████╔╝██║   ██║██║███████╗     ╚███╔╝
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║     ██╔██╗
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║    ██╔╝ ██╗
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝    ╚═╝  ╚═╝
"""


def _print_banner() -> None:
    console.print(Text(_BANNER, style="bold cyan"))
    console.print(
        Panel(
            f"[bold green]{__app_name__} v{__version__}[/bold green] — "
            "Next-gen AI assistant (EN/UZ)\n"
            "[dim]Type 'exit', 'quit', or 'chiqish' to leave.[/dim]",
            border_style="cyan",
        )
    )


async def _run_single(
    orchestrator: JarvisOrchestrator,
    message: str,
    session_id: str,
    force_offline: bool,
    force_model: str | None,
) -> None:
    """Send a single message and print the response."""
    if force_model:
        # Override model selection to always return the specified model
        from jarvis.ai.model_router import ModelConfig, ModelRouter

        class _FixedRouter(ModelRouter):
            def select_model(self, user_input: str, force_offline: bool = False) -> ModelConfig:
                for m in self._registry:
                    if m.name == force_model:
                        return m
                # Fallback: default selection
                return super().select_model(user_input, force_offline)

        orchestrator.set_router(_FixedRouter())

    with console.status("[bold cyan]Thinking…[/bold cyan]", spinner="dots"):
        result = await orchestrator.process_message(
            user_input=message,
            session_id=session_id,
            force_offline=force_offline,
        )

    console.print()
    console.print(
        Panel(
            Text(result["response"], style="green"),
            title=f"[dim]model: {result['model_used']} | {result['response_time']:.2f}s[/dim]",
            border_style="green",
        )
    )


async def _run_single_stream(
    orchestrator: JarvisOrchestrator,
    message: str,
    session_id: str,
    force_offline: bool,
) -> None:
    """Send a single message and stream the response."""
    console.print()
    with console.status("[bold cyan]Streaming…[/bold cyan]", spinner="dots"):
        chunks: list[str] = []
        async for chunk in orchestrator.process_stream(
            user_input=message,
            session_id=session_id,
            force_offline=force_offline,
        ):
            chunks.append(chunk)
    console.print(
        Panel(
            Text("".join(chunks), style="green"),
            title="[dim]streamed[/dim]",
            border_style="green",
        )
    )


async def _repl(
    orchestrator: JarvisOrchestrator,
    force_offline: bool,
    force_model: str | None,
) -> None:
    """Interactive REPL mode."""
    _print_banner()
    session_id = str(uuid.uuid4())

    while True:
        try:
            user_input = console.input("[bold cyan]You:[/bold cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye! / Xayr![/dim]")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit", "chiqish"}:
            console.print("[dim]Goodbye! / Xayr![/dim]")
            break

        await _run_single(orchestrator, user_input, session_id, force_offline, force_model)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jarvis",
        description=f"{__app_name__} — Next-gen AI assistant",
    )
    parser.add_argument("message", nargs="?", help="Message to send (optional; omit for REPL)")
    parser.add_argument("--offline", action="store_true", help="Use only offline-capable models")
    parser.add_argument("--model", metavar="MODEL", help="Force a specific model")
    parser.add_argument("--config", metavar="PATH", help="Path to jarvis_config.yaml")
    parser.add_argument("--api", action="store_true", help="Start the FastAPI server")
    parser.add_argument("--stream", action="store_true", help="Stream responses in CLI mode")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.api:
        try:
            import uvicorn  # type: ignore[import]
        except ImportError:
            console.print("[red]uvicorn is not installed. Run: pip install uvicorn[standard][/red]")
            sys.exit(1)
        uvicorn.run(
            "jarvis.api.main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
        )
        return

    config = load_config(args.config)
    orchestrator = JarvisOrchestrator(config=config)

    async def _run() -> None:
        await orchestrator.initialize()
        if args.message:
            session_id = str(uuid.uuid4())
            if args.stream:
                await _run_single_stream(
                    orchestrator,
                    args.message,
                    session_id,
                    force_offline=args.offline,
                )
            else:
                await _run_single(
                    orchestrator,
                    args.message,
                    session_id,
                    force_offline=args.offline,
                    force_model=args.model,
                )
        else:
            await _repl(orchestrator, force_offline=args.offline, force_model=args.model)

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted. Goodbye![/dim]")
        sys.exit(0)


if __name__ == "__main__":
    main()
