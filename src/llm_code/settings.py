import os
import tomllib
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel


class Settings(BaseModel):
    model: str = "openai:gpt-5.4"

    @classmethod
    def load(
        cls,
        *,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> Settings:
        cwd = (cwd or Path.cwd()).resolve()
        env = env or dict(os.environ)

        data: dict[str, Any] = {}

        user_config = get_user_config_path(env=env)
        if user_config.is_file():
            data.update(load_config_file(user_config))

        project_config = find_project_config(cwd)
        if project_config is not None:
            data.update(load_config_file(project_config))

        data.update(load_env_overrides(env=env, fields=cls.model_fields))
        return cls.model_validate(data)


def get_user_config_path(*, env: dict[str, str] | None = None) -> Path:
    env = env or dict(os.environ)
    xdg_config_home = env.get("XDG_CONFIG_HOME")

    if xdg_config_home:
        base_dir = Path(xdg_config_home).expanduser()
    else:
        base_dir = Path.home() / ".config"

    return base_dir / "llm_code" / "config.toml"


def find_project_config(start_dir: Path) -> Path | None:
    current_dir = start_dir.resolve()

    for directory in (current_dir, *current_dir.parents):
        candidate = directory / ".config.yaml"
        if candidate.is_file():
            return candidate

    return None


def load_config_file(path: Path) -> dict[str, Any]:
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


def load_env_overrides(
    *,
    env: dict[str, str],
    fields: dict[str, Any],
) -> dict[str, str]:
    overrides: dict[str, str] = {}

    for field_name in fields:
        env_name = field_name.upper()
        if env_name in env:
            overrides[field_name] = env[env_name]

    return overrides
