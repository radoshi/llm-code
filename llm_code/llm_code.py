from pathlib import Path

import click
import openai
from pydantic import BaseSettings
from rich.console import Console
from rich.syntax import Syntax

from .templates import Message, TemplateLibrary


class Settings(BaseSettings):
    openai_api_key: str = ""
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.8
    max_tokens: int = 1000
    config_dir: Path = Path("~/.llm_code").expanduser()

    class Config:
        env_file = Path("~/.llm_code").expanduser() / "env"
        env_file_encoding = "utf-8"


def load_templates() -> TemplateLibrary:
    """Load templates from the config directory."""
    settings = Settings()

    # Load from user config directory
    templates_dir = settings.config_dir / "prompts"
    if templates_dir.exists():
        return TemplateLibrary.from_file_or_directory(templates_dir)

    # Load from package directory
    templates_dir = Path(__file__).parent.parent / "prompts"
    if templates_dir.exists():
        return TemplateLibrary.from_file_or_directory(templates_dir)

    return TemplateLibrary()


@click.command()
@click.option("-i", "--inputs", default=None, help="Glob of input files.")
@click.option("-ln", "--line-numbers", is_flag=True, help="Show line numbers.")
@click.argument("instructions", nargs=-1)
def main(inputs, line_numbers, instructions):
    """Coding assistant using OpenAI's chat models.

    Requires OPENAI_API_KEY as an environment variable. Alternately, you can set it in
    ~/.llm_code/env.
    """
    settings = Settings()
    if not settings.openai_api_key:
        click.UsageError("OPENAI_API_KEY must be set.")

    console = Console()

    instructions = " ".join(instructions)

    library = load_templates()

    inputs = Path.cwd().glob(inputs) if inputs else []
    input = "\n\n".join([i.read_text() for i in inputs])

    if input:
        message = library["coding/input"].message(code=input, instructions=instructions)
    else:
        message = library["coding/simple"].message(instructions=instructions)

    messages = [library["coding/system"].message(), message]

    with console.status("[bold green]Asking OpenAI..."):
        response = openai.ChatCompletion.create(
            api_key=settings.openai_api_key,
            model=settings.model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            messages=messages,
        )

    message = Message.from_message(response.choices[0]["message"])  # type: ignore
    # console.log(message)
    code = message.code()
    if code:
        console.print(Syntax(code.code, code.lang, line_numbers=line_numbers))
        # console.print(code.code)
    else:
        console.print(f"No code found in message: \n\n{message.content}")


if __name__ == "__main__":
    main()
