import json

from pydantic_ai.messages import FunctionToolCallEvent, ToolCallPart

from llm_code.llm_code import _format_tool_call_status, _tool_args_as_dict


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
