import asyncio
import json
from collections.abc import AsyncIterable, Awaitable, Callable
from typing import Any

import click
from pydantic_ai.messages import FunctionToolCallEvent, PartStartEvent
from pydantic_ai.models import Model
from rich.console import Console
from rich.status import Status

from llm_code import __version__
from llm_code.agent import build_agent
from llm_code.models import build_models
from llm_code.providers import build_providers
from llm_code.settings import Settings
from llm_code.tui import launch_tui


def _build_event_handler(
    status: Status,
) -> Callable[[Any, AsyncIterable[Any]], Awaitable[None]]:
    """Build an event handler that updates a status line while the agent runs."""

    async def _handle_agent_events(_ctx: Any, event_stream: AsyncIterable[Any]) -> None:
        async for event in event_stream:
            if isinstance(event, PartStartEvent) and event.part.part_kind == "thinking":
                status.update("[cyan]Thinking[/cyan]")
            elif isinstance(event, FunctionToolCallEvent):
                status.update(_format_tool_call_status(event))
            elif isinstance(event, PartStartEvent) and event.part.part_kind == "text":
                status.stop()

    return _handle_agent_events


def _format_tool_call_status(event: FunctionToolCallEvent) -> str:
    """Format a human-friendly status line for a tool call."""
    tool_name = event.part.tool_name
    args = _tool_args_as_dict(event.part.args)

    if tool_name == "read":
        return f"[yellow]Read[/yellow] {_format_value(args.get('path', '?'))}"
    if tool_name == "write":
        return f"[yellow]Write[/yellow] {_format_value(args.get('path', '?'))}"
    if tool_name == "search":
        search_path = _format_value(args.get("path", "."))
        pattern = _format_value(args.get("pattern"))
        return f"[yellow]Search[/yellow] {search_path} for {pattern}"
    if tool_name == "bash":
        return f"[yellow]Bash[/yellow] {_format_value(args.get('command'))}"

    return f"[yellow]{tool_name}[/yellow] {_format_tool_args(event.part.args)}"


def _tool_args_as_dict(args: Any) -> dict[str, Any]:
    """Convert tool arguments into a dictionary when possible."""
    if isinstance(args, dict):
        return args
    if isinstance(args, str):
        try:
            parsed = json.loads(args)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return parsed
    return {}


def _format_value(value: Any, *, max_length: int = 80) -> str:
    """Format one value for compact display in the status line."""
    if value is None:
        text = ""
    elif isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, ensure_ascii=False)

    if len(text) > max_length:
        return f"{text[: max_length - 1]}…"
    return text


def _format_tool_args(args: Any, *, max_length: int = 80) -> str:
    """Format tool call arguments for compact status updates."""
    if isinstance(args, dict):
        text = json.dumps(args, ensure_ascii=False)
    elif isinstance(args, str):
        text = args
    else:
        text = repr(args)

    if len(text) > max_length:
        return f"{text[: max_length - 1]}…"
    return text


async def run_prompt(
    prompt: str,
    *,
    model: Model,
    console: Console,
) -> None:
    """Run the coding agent with a prompt and stream its response."""
    agent = build_agent(model)
    event_console = Console(stderr=True)

    with event_console.status("[cyan]Thinking[/cyan]") as status:
        event_handler = _build_event_handler(status)
        async with agent.run_stream(
            prompt,
            event_stream_handler=event_handler,
        ) as result:
            async for chunk in result.stream_text(delta=True, debounce_by=None):
                console.print(chunk, end="", markup=False, highlight=False)

    console.print()


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="llm_code")
@click.argument("prompt", nargs=-1)
def main(prompt: tuple[str, ...]) -> None:
    """Run the coding agent with PROMPT or launch the TUI when no prompt is given."""
    settings = Settings.load()
    providers = build_providers(settings)
    models = build_models(providers)

    model = models.get(settings.model)
    if model is None:
        raise ValueError(f"Model {settings.model} not found")

    user_prompt = " ".join(prompt).strip()

    if user_prompt:
        console = Console()
        asyncio.run(
            run_prompt(
                user_prompt,
                console=console,
                model=model,
            )
        )
        return

    launch_tui(model=model)


if __name__ == "__main__":
    main()
