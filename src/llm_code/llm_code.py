import asyncio

import click
from rich.console import Console

from llm_code import __version__
from llm_code.agent import build_agent
from llm_code.settings import Settings


async def run_prompt(prompt: str, *, console: Console, model: str) -> None:
    """Run the coding agent with a prompt and stream its response."""
    agent = build_agent(model)

    async with agent.run_stream(prompt) as result:
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
