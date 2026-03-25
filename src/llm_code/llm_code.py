import asyncio
from pathlib import Path

import click
from pydantic_ai import Agent
from pydantic_ai.capabilities import Thinking
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console

from llm_code import __version__


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path("~/.llm_code/env").expanduser(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    model: str = "openai:gpt-5.4"


DEFAULT_INSTRUCTIONS = "You are an expert at coding."


def build_agent(model: str) -> Agent:
    return Agent(
        model,
        instructions=DEFAULT_INSTRUCTIONS,
        capabilities=[Thinking(effort="high")],
    )


async def run_prompt(prompt: str, *, console: Console, agent: Agent) -> None:
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
    settings = Settings()
    agent = build_agent(settings.model)
    user_prompt = " ".join(prompt).strip()

    asyncio.run(run_prompt(user_prompt, console=console, agent=agent))


if __name__ == "__main__":
    main()
