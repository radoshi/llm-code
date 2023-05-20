from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from llm_code.llm_code import load_templates, main
from llm_code.templates import Template


@patch("llm_code.llm_code.openai.ChatCompletion.create")
def test_main(mocked_openai):
    mocked_openai.return_value = Mock(
        choices=[  # type: ignore
            {
                "message": {
                    "role": "assistant",
                    "content": "```python\nprint('Hello, world!')\n```",
                },
            },
        ]
    )

    runner = CliRunner(env={"OPENAI_API_KEY": "test"})

    # Exercise simple code
    result = runner.invoke(main, ["code"])
    assert result.exit_code == 0
    assert "print('Hello, world!')" in result.stdout.strip()

    # Exercise with input
    filename = "LICENSE"
    result = runner.invoke(main, ["--inputs", filename, "code"])
    assert result.exit_code == 0
    assert "print('Hello, world!')" in result.stdout.strip()


@patch("llm_code.llm_code.openai.ChatCompletion.create")
def test_no_code(mocked_openai):
    mocked_openai.return_value = Mock(
        choices=[  # type: ignore
            {
                "message": {
                    "role": "assistant",
                    "content": "Random text.",
                },
            },
        ]
    )

    runner = CliRunner(env={"OPENAI_API_KEY": "test"})

    # Exercise simple code
    result = runner.invoke(main, ["code"])
    assert result.exit_code == 1
    assert "No code found in message" in result.stdout.strip()


def test_cli_with_no_command():
    runner = CliRunner(env={"OPENAI_API_KEY": "test"})
    result = runner.invoke(main, [])
    assert result.exit_code == 2
    assert "Error: Please provide some instructions." in result.output


def test_cli_with_no_api_key():
    runner = CliRunner()
    result = runner.invoke(main, ["Hello"])
    assert result.exit_code == 2
    assert "Error: OPENAI_API_KEY must be set." in result.output


def test_load_templates(tmpdir):
    non_existant = tmpdir / "non_existant"
    assert not non_existant.exists()
    assert not load_templates(non_existant)

    tmpdir.mkdir("prompts")
    Template(content="Hello, World!", name="coding/simple", role="user").save(
        tmpdir / "prompts" / "coding.json"
    )
    Template(content="Hello, World!", name="coding/system", role="system").save(
        tmpdir / "prompts" / "system.json"
    )
    library = load_templates(tmpdir)
    assert library
    assert library["coding/simple"].content == "Hello, World!"
    assert library["coding/system"].content == "Hello, World!"


@patch("llm_code.llm_code.load_templates")
def test_cli_with_library(mocked_load_templates):
    mocked_load_templates.return_value = None
    runner = CliRunner(env={"OPENAI_API_KEY": "test"})
    result = runner.invoke(main, ["Hello"])
    assert result.exit_code == 2
    assert "Error: No templates found." in result.output
