from unittest.mock import Mock, patch

from click.testing import CliRunner
from rich.pretty import pprint

from llm_code.llm_code import load_templates, main


def test_load_templates():
    templates = load_templates()
    assert len(templates) > 0


@patch("llm_code.llm_code.openai.ChatCompletion.create")
def test_main(mocked_openai):
    mocked_openai.return_value = Mock(
        choices=[
            {
                "message": {
                    "role": "assistant",
                    "content": "```python\nprint('Hello, world!')\n```",
                },
            },
        ]
    )

    runner = CliRunner(env={"OPENAI_API_KEY": "test"})
    result = runner.invoke(main, ["code"])
    assert result.exit_code == 0
    assert "print('Hello, world!')" in result.stdout.strip()
