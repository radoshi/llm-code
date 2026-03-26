from llm_code.tui import PromptInput


def test_prompt_input_binds_enter_to_submit() -> None:
    binding = next(
        binding for binding in PromptInput.BINDINGS if binding.key == "enter"
    )

    assert binding.action == "submit"
    assert binding.priority is True


def test_prompt_input_submit_action_posts_message(monkeypatch) -> None:
    prompt = PromptInput("hello")
    posted: dict[str, str] = {}

    def fake_post_message(message: PromptInput.Submitted) -> None:
        posted["prompt"] = message.prompt

    monkeypatch.setattr(prompt, "post_message", fake_post_message)

    prompt.action_submit()

    assert posted == {"prompt": "hello"}
