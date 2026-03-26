from pathlib import Path

import pytest

from llm_code.settings import (
    Settings,
    _get_project_config,
    _get_user_config,
    _load_config_file,
)


def test_get_user_config_uses_xdg_config_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    xdg_config_home = tmp_path / "xdg-config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_config_home))

    config_path = xdg_config_home / "llm_code" / "config.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text('model = "xdg-model"\n', encoding="utf-8")

    config = _get_user_config()

    assert config == {"model": "xdg-model"}


def test_get_project_config_uses_closest_parent(tmp_path: Path) -> None:
    root_config = tmp_path / ".config.yaml"
    root_config.write_text("model: root-model\n", encoding="utf-8")

    nested_dir = tmp_path / "project" / "pkg"
    nested_dir.mkdir(parents=True)

    nested_config = tmp_path / "project" / ".config.yaml"
    nested_config.write_text("model: nested-model\n", encoding="utf-8")

    config = _get_project_config(cwd=nested_dir)

    assert config == {"model": "nested-model"}
    assert config != {"model": "root-model"}


def test_settings_load_merges_user_then_project_then_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home_dir = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home_dir)

    user_config = home_dir / ".config" / "llm_code" / "config.toml"
    user_config.parent.mkdir(parents=True)
    user_config.write_text('model = "user-model"\n', encoding="utf-8")

    project_dir = tmp_path / "workspace" / "app"
    project_dir.mkdir(parents=True)
    project_config = tmp_path / "workspace" / ".config.yaml"
    project_config.write_text("model: project-model\n", encoding="utf-8")

    settings = Settings.load(cwd=project_dir, env={"MODEL": "env-model"})

    assert settings.model == "env-model"


def test_settings_load_uses_project_config_over_user_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home_dir = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home_dir)

    user_config = home_dir / ".config" / "llm_code" / "config.toml"
    user_config.parent.mkdir(parents=True)
    user_config.write_text('model = "user-model"\n', encoding="utf-8")

    project_dir = tmp_path / "workspace" / "app"
    project_dir.mkdir(parents=True)
    project_config = tmp_path / "workspace" / ".config.yaml"
    project_config.write_text("model: project-model\n", encoding="utf-8")

    settings = Settings.load(cwd=project_dir, env={})

    assert settings.model == "project-model"


def test_load_config_file_rejects_non_mapping_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / ".config.yaml"
    config_path.write_text("- one\n- two\n", encoding="utf-8")

    with pytest.raises(ValueError, match="key-value pairs"):
        _load_config_file(config_path)


def test_api_key_from_config_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home_dir = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home_dir)

    user_config = home_dir / ".config" / "llm_code" / "config.yaml"
    user_config.parent.mkdir(parents=True)
    user_config.write_text("OPENAI_API_KEY: sk-from-config\n", encoding="utf-8")

    settings = Settings.load(cwd=tmp_path, env={})

    assert settings.api_key == "sk-from-config"


def test_api_key_from_env_var(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home_dir = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home_dir)

    settings = Settings.load(cwd=tmp_path, env={"OPENAI_API_KEY": "sk-from-env"})

    assert settings.api_key == "sk-from-env"


def test_api_key_env_overrides_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home_dir = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home_dir)

    user_config = home_dir / ".config" / "llm_code" / "config.yaml"
    user_config.parent.mkdir(parents=True)
    user_config.write_text("OPENAI_API_KEY: sk-from-config\n", encoding="utf-8")

    settings = Settings.load(cwd=tmp_path, env={"OPENAI_API_KEY": "sk-from-env"})

    assert settings.api_key == "sk-from-env"


def test_get_user_config_reads_yaml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    xdg_config_home = tmp_path / "xdg-config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_config_home))

    config_path = xdg_config_home / "llm_code" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("model: yaml-model\n", encoding="utf-8")

    config = _get_user_config()

    assert config == {"model": "yaml-model"}


def test_get_user_config_prefers_toml_over_yaml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    xdg_config_home = tmp_path / "xdg-config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_config_home))

    config_dir = xdg_config_home / "llm_code"
    config_dir.mkdir(parents=True)
    (config_dir / "config.toml").write_text('model = "toml-model"\n', encoding="utf-8")
    (config_dir / "config.yaml").write_text("model: yaml-model\n", encoding="utf-8")

    config = _get_user_config()

    assert config == {"model": "toml-model"}
