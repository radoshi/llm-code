import asyncio
import json
from collections.abc import AsyncIterable, Awaitable, Callable
from typing import Any

import click
from pydantic_ai.messages import FunctionToolCallEvent, FunctionToolResultEvent
from rich.console import Console

from llm_code import __version__
from llm_code.agent import build_agent
from llm_code.settings import Settings


def _build_event_handler(
    console: Console,
) -> Callable[[Any, AsyncIterable[Any]], Awaitable[None]]:
    """Build an event handler that prints tool call events while the agent runs."""

    async def _handle_agent_events(_ctx: Any, event_stream: AsyncIterable[Any]) -> None:
        async for event in event_stream:
            if isinstance(event, FunctionToolCallEvent):
                args = _format_tool_args(event.part.args)
                console.print(
                    f"[dim][tool call][/dim] {event.part.tool_name}({args})",
                    highlight=False,
                )
            elif isinstance(event, FunctionToolResultEvent):
                result = event.result
                if hasattr(result, "outcome"):
                    console.print(
                        "[dim][tool result][/dim] "
                        f"{result.tool_name} [{result.outcome}]",
                        highlight=False,
                    )

    return _handle_agent_events


def _format_tool_args(args: Any) -> str:
    """Format tool call arguments for compact event logging."""
    if isinstance(args, dict):
        return json.dumps(args, ensure_ascii=False)
    if isinstance(args, str):
        return args
    return repr(args)


async def run_prompt(prompt: str, *, console: Console, model: str) -> None:
    """Run the coding agent with a prompt and stream its response."""
    agent = build_agent(model)
    event_console = Console(stderr=True)
    event_handler = _build_event_handler(event_console)

    async with agent.run_stream(
        prompt,
        event_stream_handler=event_handler,
    ) as result:
        async for chunk in result.stream_text(delta=True, debounce_by=None):
            console.print(chunk, end="", markup=False, highlight=False)

    console.print()


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="llm_code")
@click.argument("prompt", nargs=-1, required=True)
def main(prompt: tuple[str, ...]) -> None:
    """Run the coding agent with PROMPT and stream the response."""
    console = Console()
    settings = Settings.load()
    user_prompt = " ".join(prompt).strip()

    asyncio.run(run_prompt(user_prompt, console=console, model=settings.model))


if __name__ == "__main__":
    main()
