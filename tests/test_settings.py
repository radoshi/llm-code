from pathlib import Path

import pytest

from llm_code.settings import (
    Settings,
    find_project_config,
    get_user_config_path,
    load_config_file,
)


def test_get_user_config_path_uses_xdg_config_home() -> None:
    env = {"XDG_CONFIG_HOME": "/tmp/xdg-config"}

    path = get_user_config_path(env=env)

    assert path == Path("/tmp/xdg-config/llm_code/config.toml")


def test_find_project_config_uses_closest_parent(tmp_path: Path) -> None:
    root_config = tmp_path / ".config.yaml"
    root_config.write_text("model: root-model\n", encoding="utf-8")

    nested_dir = tmp_path / "project" / "pkg"
    nested_dir.mkdir(parents=True)

    nested_config = tmp_path / "project" / ".config.yaml"
    nested_config.write_text("model: nested-model\n", encoding="utf-8")

    path = find_project_config(nested_dir)

    assert path == nested_config
    assert path != root_config


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
        load_config_file(config_path)
