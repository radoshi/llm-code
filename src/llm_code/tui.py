import asyncio
from typing import Any

from pydantic_ai.models import Model
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.widgets import TextArea

from llm_code.agent import build_agent


class PromptInput(TextArea):
    """Prompt input where Enter submits."""

    BINDINGS = [
        Binding("enter", "submit", show=False, priority=True),
    ]

    class Submitted(Message):
        """Posted when the prompt input is submitted."""

        def __init__(self, prompt: str) -> None:
            self.prompt = prompt
            super().__init__()

    def action_submit(self) -> None:
        """Submit the current prompt contents."""
        self.post_message(self.Submitted(self.text))


class LlmCodeApp(App[None]):
    """A minimal TUI for chatting with the coding agent."""

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False, priority=True),
    ]

    CSS = """
    Screen {
        layout: vertical;
    }

    #output {
        height: 1fr;
    }

    #prompt {
        height: 7;
    }
    """

    def __init__(self, *, model: Model) -> None:
        super().__init__()
        self._model = model
        self._agent = build_agent(model)
        self._transcript = ""
        self._pending_task: asyncio.Task[Any] | None = None

    def compose(self) -> ComposeResult:
        """Compose the main output area and prompt box."""
        yield TextArea(
            "",
            id="output",
            read_only=True,
            show_line_numbers=False,
            soft_wrap=True,
        )
        yield PromptInput(
            "",
            id="prompt",
            show_line_numbers=False,
            soft_wrap=True,
            placeholder="Enter to send.",
        )

    def on_mount(self) -> None:
        """Focus the prompt when the app starts."""
        self.query_one("#prompt", PromptInput).focus()

    def on_prompt_input_submitted(self, message: PromptInput.Submitted) -> None:
        """Send the prompt to the agent."""
        if self._pending_task is not None and not self._pending_task.done():
            self.notify("Wait for the current response to finish.")
            return

        prompt = message.prompt.strip()
        if not prompt:
            return

        prompt_input = self.query_one("#prompt", PromptInput)
        prompt_input.clear()
        prompt_input.disabled = True

        self._append_transcript(f"You:\n{prompt}\n\nAssistant:\n")
        self._pending_task = asyncio.create_task(self._run_prompt(prompt))

    async def _run_prompt(self, prompt: str) -> None:
        """Run one prompt and stream the response into the transcript."""
        try:
            async with self._agent.run_stream(prompt) as result:
                async for chunk in result.stream_text(delta=True, debounce_by=None):
                    self._append_transcript(chunk)
            self._append_transcript("\n")
        except Exception as exc:  # pragma: no cover - defensive UI path
            self._append_transcript(f"\n[error] {exc}\n")
        finally:
            prompt_input = self.query_one("#prompt", PromptInput)
            prompt_input.disabled = False
            prompt_input.focus()

    def _append_transcript(self, text: str) -> None:
        """Append text to the transcript and refresh the output widget."""
        self._transcript += text
        output = self.query_one("#output", TextArea)
        output.load_text(self._transcript)
        output.scroll_end(animate=False)


def launch_tui(*, model: Model) -> None:
    """Launch the Textual TUI."""
    app = LlmCodeApp(model=model)
    app.run()
