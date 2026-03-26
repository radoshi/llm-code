import json
from types import SimpleNamespace

from click.testing import CliRunner
from pydantic_ai.messages import FunctionToolCallEvent, ToolCallPart

from llm_code.llm_code import _format_tool_call_status, _tool_args_as_dict, main


def test_tool_args_as_dict_returns_dict_input() -> None:
    args = {"path": "src/example.py"}

    result = _tool_args_as_dict(args)

    assert result == {"path": "src/example.py"}


def test_tool_args_as_dict_parses_json_string() -> None:
    args = json.dumps({"path": "src/example.py"})

    result = _tool_args_as_dict(args)

    assert result == {"path": "src/example.py"}


def test_format_tool_call_status_for_read_uses_path_from_json_args() -> None:
    event = FunctionToolCallEvent(
        ToolCallPart(
            tool_name="read",
            args=json.dumps({"path": "src/example.py"}),
            tool_call_id="call-1",
        )
    )

    result = _format_tool_call_status(event)

    assert result == "[yellow]Read[/yellow] src/example.py"


def test_format_tool_call_status_for_write_uses_path_from_dict_args() -> None:
    event = FunctionToolCallEvent(
        ToolCallPart(
            tool_name="write",
            args={"path": "src/example.py", "content": "print('hello')\n"},
            tool_call_id="call-2",
        )
    )

    result = _format_tool_call_status(event)

    assert result == "[yellow]Write[/yellow] src/example.py"


def test_format_tool_call_status_for_search_is_human_friendly() -> None:
    event = FunctionToolCallEvent(
        ToolCallPart(
            tool_name="search",
            args={"path": "src/*.py", "pattern": "Agent"},
            tool_call_id="call-3",
        )
    )

    result = _format_tool_call_status(event)

    assert result == "[yellow]Search[/yellow] src/*.py for Agent"


def test_format_tool_call_status_for_bash_is_human_friendly() -> None:
    event = FunctionToolCallEvent(
        ToolCallPart(
            tool_name="bash",
            args={"command": "uv run pytest"},
            tool_call_id="call-4",
        )
    )

    result = _format_tool_call_status(event)

    assert result == "[yellow]Bash[/yellow] uv run pytest"


def test_main_runs_prompt_when_prompt_is_given(monkeypatch) -> None:
    monkeypatch.setattr(
        "llm_code.llm_code.Settings.load",
        lambda: SimpleNamespace(model="test-model", api_key=None),
    )

    called: dict[str, str] = {}

    async def fake_run_prompt(
        prompt: str, *, console, model: str, api_key: str | None = None
    ) -> None:
        called["prompt"] = prompt
        called["model"] = model
        called["console_type"] = type(console).__name__

    monkeypatch.setattr("llm_code.llm_code.run_prompt", fake_run_prompt)

    result = CliRunner().invoke(main, ["hello", "world"])

    assert result.exit_code == 0
    assert called == {
        "prompt": "hello world",
        "model": "test-model",
        "console_type": "Console",
    }


def test_main_launches_tui_when_no_prompt_is_given(monkeypatch) -> None:
    monkeypatch.setattr(
        "llm_code.llm_code.Settings.load",
        lambda: SimpleNamespace(model="test-model", api_key=None),
    )

    called: dict[str, str] = {}

    def fake_launch_tui(*, model: str, api_key: str | None = None) -> None:
        called["model"] = model

    monkeypatch.setattr("llm_code.llm_code.launch_tui", fake_launch_tui)

    result = CliRunner().invoke(main, [])

    assert result.exit_code == 0
    assert called == {"model": "test-model"}
