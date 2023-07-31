import os
import sys
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from llm_code import __version__, db
from llm_code.llm_code import (
    Settings,
    get_cached_response,
    get_code,
    load_templates,
    main,
)
from llm_code.templates import Message, Template


@patch("llm_code.llm_code.openai.ChatCompletion.create")
def test_main(mocked_openai, tmpdir):
    mocked_openai.return_value = Mock(
        choices=[  # type: ignore
            {
                "message": {
                    "role": "assistant",
                    "content": "```python\nprint('Hello, world!')\n```",
                },
            },
        ],
        usage={
            "prompt_tokens": 1,
            "completion_tokens": 1,
        },
    )

    runner = CliRunner(env={"OPENAI_API_KEY": "test", "CONFIG_DIR": str(tmpdir)})

    # Exercise simple code
    result = runner.invoke(main, ["code"])
    assert result.exit_code == 0
    assert "print('Hello, world!')" in result.stdout.strip()

    # Exercise with input
    filename = "LICENSE"
    result = runner.invoke(main, ["--inputs", filename, "code"])
    assert result.exit_code == 0
    assert "print('Hello, world!')" in result.stdout.strip()

    # Exercise with gpt-4
    result = runner.invoke(main, ["--gpt-4", "code"])
    assert result.exit_code == 0
    assert "print('Hello, world!')" in result.stdout.strip()
    assert mocked_openai.call_args.kwargs["model"] == "gpt-4"


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
        ],
        usage={
            "prompt_tokens": 1,
            "completion_tokens": 1,
        },
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


def test_cli_with_no_api_key(tmpdir):
    runner = CliRunner(env={"CONFIG_DIR": str(tmpdir), "OPENAI_API_KEY": ""})
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


def test_version(capsys):
    sys.argv = ["llm_code", "--version"]
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert f"llm_code version {__version__}" in captured.out


def test_get_cached_response(tmpdir):
    settings = Settings(
        model="gpt-3.5-turbo", temperature=0.8, max_tokens=1000, config_dir=tmpdir
    )
    messages = [
        {"role": "system", "content": "You are a programming expert."},
        {"role": "user", "content": "Write a function to print 'Hello World!'."},
    ]
    _ = db.Database.get(settings.config_dir / "db.sqlite")

    # Test cache miss with no row
    cached_response = get_cached_response(settings, messages)
    assert cached_response is None

    # Setup
    db.write(
        model=settings.model,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        system_message=messages[0]["content"],
        user_message=messages[1]["content"],
        assistant_message="def hello_world():\n    print('Hello World!')",
        input_tokens=5,
        output_tokens=5,
    )

    # Test cache hit
    cached_response = get_cached_response(settings, messages)
    assert cached_response is not None
    assert cached_response.content == "def hello_world():\n    print('Hello World!')"

    # Test cache miss
    messages[1]["content"] = "Write a function to print 'Hello!'"
    cached_response = get_cached_response(settings, messages)
    assert cached_response is None


@patch("llm_code.llm_code.get_cached_response")
def test_cached_response(mocked_cached_response, tmpdir):
    mocked_cached_response.return_value = Message(
        role="assistant",
        content="```python\ndef hello_world():\n    print('Hello World!')```",
    )

    runner = CliRunner(env={"OPENAI_API_KEY": "test", "CONFIG_DIR": str(tmpdir)})

    # Exercise simple code
    result = runner.invoke(main, ["code"])
    assert result.exit_code == 0
    assert "print('Hello World!')" in result.stdout.strip()


def test_get_code(tmpdir):
    # create some files
    (tmpdir / "file1.py").write_text("print('Hello from file1')", encoding="utf-8")
    (tmpdir / "file2.py").write_text("print('Hello from file2')", encoding="utf-8")

    # change the current working directory to tmpdir
    os.chdir(tmpdir)

    inputs = ["file1.py", "file2.py"]
    expected_output = (
        "FILENAME: file1.py\n```print('Hello from file1')\n```\n---\n"
        "FILENAME: file2.py\n```print('Hello from file2')\n```"
    )
    assert get_code(inputs) == expected_output
