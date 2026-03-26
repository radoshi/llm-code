import subprocess
from pathlib import Path

import pytest

from llm_code.agent import _read_files, _search_files, _write_file


def test_read_files_reads_a_single_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    file_path = tmp_path / "hello.txt"
    file_path.write_text("hello world\n", encoding="utf-8")

    result = _read_files("hello.txt")

    assert result == {"hello.txt": "hello world\n"}


def test_read_files_reads_a_glob(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "a.py").write_text("print('a')\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("print('b')\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("ignore\n", encoding="utf-8")

    result = _read_files("*.py")

    assert result == {
        "a.py": "print('a')\n",
        "b.py": "print('b')\n",
    }


def test_read_files_rejects_paths_outside_cwd(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError, match="current working directory"):
        _read_files("../secret.txt")


def test_write_file_writes_a_single_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    message = _write_file("nested/out.txt", "hello")

    assert message == "Wrote nested/out.txt"
    assert (tmp_path / "nested/out.txt").read_text(encoding="utf-8") == "hello"


def test_write_file_rejects_paths_outside_cwd(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError, match="current working directory"):
        _write_file("../out.txt", "hello")


def test_search_files_returns_grouped_matches_with_context_from_glob(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text(
        "zero\nalpha\nhello world\nomega\nlast\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "other.py").write_text(
        "before\nhello there\nafter\n",
        encoding="utf-8",
    )

    result = _search_files("hello", path="src/*.py", context_lines=1)

    assert result == [
        {
            "path": "src/app.py",
            "matches": [
                {
                    "line_number": 3,
                    "snippet": "2: alpha\n3: hello world\n4: omega",
                }
            ],
        },
        {
            "path": "src/other.py",
            "matches": [
                {
                    "line_number": 2,
                    "snippet": "1: before\n2: hello there\n3: after",
                }
            ],
        },
    ]


def test_search_files_accepts_direct_file_paths(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text(
        "zero\nalpha\nhello world\nomega\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "other.py").write_text(
        "before\nhello there\nafter\n",
        encoding="utf-8",
    )

    result = _search_files("hello", path="src/app.py", context_lines=1)

    assert result == [
        {
            "path": "src/app.py",
            "matches": [
                {
                    "line_number": 3,
                    "snippet": "2: alpha\n3: hello world\n4: omega",
                }
            ],
        }
    ]


def test_search_files_rejects_paths_outside_cwd(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError, match="current working directory"):
        _search_files("hello", path="../src/*.py", context_lines=1)


def test_search_files_falls_back_to_grep_when_rg_is_unavailable(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    file_path = tmp_path / "app.py"
    file_path.write_text("zero\nhello world\nomega\n", encoding="utf-8")

    monkeypatch.setattr("llm_code.agent.shutil.which", lambda name: None)

    def fake_run(command: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
        assert command[:4] == ["grep", "-R", "-n", "-E"]
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="./app.py:2:hello world\n",
            stderr="",
        )

    monkeypatch.setattr("llm_code.agent.subprocess.run", fake_run)

    result = _search_files("hello", path="app.py", context_lines=1)

    assert result == [
        {
            "path": "app.py",
            "matches": [
                {
                    "line_number": 2,
                    "snippet": "1: zero\n2: hello world\n3: omega",
                }
            ],
        }
    ]
