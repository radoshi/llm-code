"""Registry of LLM models."""

from pydantic_ai.models import Model
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers import Provider

OPENAI_MODELS = [
    "gpt-5.3-codex",
    "gpt-5.4",
]

ANTHROPIC_MODELS = [
    "claude-opus-4-6",
    "claude-sonnet-4-6",
    "claude-haiku-4-6",
]


def build_models(providers: dict[str, Provider]) -> dict[str, Model]:
    """Build models from providers."""
    models = {}
    if "openai" in providers:
        for model_name in OPENAI_MODELS:
            models[model_name] = OpenAIResponsesModel(
                model_name=model_name, provider=providers["openai"]
            )
    if "anthropic" in providers:
        for model_name in ANTHROPIC_MODELS:
            models[model_name] = AnthropicModel(
                model_name=model_name, provider=providers["anthropic"]
            )
    return models
