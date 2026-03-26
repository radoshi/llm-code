import os
import tomllib
from pathlib import Path
from typing import Any

import yaml
from pydantic import AliasChoices, BaseModel, Field


class Settings(BaseModel):
    """Application settings loaded from defaults, config files, and environment."""

    model: str = "openai-responses:gpt-5.3-codex"
    api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("api_key", "OPENAI_API_KEY"),
    )

    @classmethod
    def load(
        cls,
        *,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> Settings:
        """Load settings from user config, project config, and environment."""
        env = env or dict(os.environ)

        data: dict[str, Any] = {}
        data.update(_get_user_config())
        data.update(_get_project_config(cwd=cwd))
        data.update(_load_env_overrides(env=env, fields=cls.model_fields))

        return cls.model_validate(data)


def _get_user_config() -> dict[str, Any]:
    """Return user config from XDG config home or ~/.config, or an empty mapping."""
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")

    if xdg_config_home:
        base_dir = Path(xdg_config_home).expanduser()
    else:
        base_dir = Path.home() / ".config"

    config_dir = base_dir / "llm_code"
    for filename in ("config.toml", "config.yaml"):
        config_path = config_dir / filename
        if config_path.is_file():
            return _load_config_file(config_path)

    return {}


def _get_project_config(*, cwd: Path | None = None) -> dict[str, Any]:
    """Return the nearest project config from cwd upward, or an empty mapping."""
    current_dir = (cwd or Path.cwd()).resolve()

    for directory in (current_dir, *current_dir.parents):
        candidate = directory / ".config.yaml"
        if candidate.is_file():
            return _load_config_file(candidate)

    return {}


def _load_config_file(path: Path) -> dict[str, Any]:
    """Load a TOML or YAML config file and return its top-level mapping."""
    with path.open("rb") as file_handle:
        if path.suffix == ".toml":
            data = tomllib.load(file_handle)
        elif path.suffix in {".yaml", ".yml"}:
            data = yaml.safe_load(file_handle) or {}
        else:
            raise ValueError(f"Unsupported config file format: {path}")

    if not isinstance(data, dict):
        raise ValueError(f"Config file must contain key-value pairs: {path}")

    return data


_ENV_ALIASES: dict[str, list[str]] = {
    "api_key": ["OPENAI_API_KEY"],
}


def _load_env_overrides(
    *,
    env: dict[str, str],
    fields: dict[str, Any],
) -> dict[str, str]:
    """Return environment values that match known settings fields."""
    overrides: dict[str, str] = {}

    for field_name in fields:
        env_name = field_name.upper()
        if env_name in env:
            overrides[field_name] = env[env_name]
        else:
            for alias in _ENV_ALIASES.get(field_name, []):
                if alias in env:
                    overrides[field_name] = env[alias]
                    break

    return overrides
