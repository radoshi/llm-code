"""Registry of LLM providers."""

from pydantic_ai.providers import Provider
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.openai import OpenAIProvider

from llm_code.settings import Settings


def build_providers(settings: Settings) -> dict[str, Provider]:
    """Build providers from settings."""
    providers = {}
    if settings.openai_api_key:
        providers["openai"] = OpenAIProvider(api_key=settings.openai_api_key)

    if settings.anthropic_api_key:
        providers["anthropic"] = AnthropicProvider(api_key=settings.anthropic_api_key)
    return providers
