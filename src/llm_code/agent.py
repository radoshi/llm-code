import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.capabilities import Thinking

DEFAULT_INSTRUCTIONS = "You are an expert at coding."


def build_agent(model: str) -> Agent:
    """Build an agent configured with the local file tools."""
    agent = Agent(
        model,
        instructions=DEFAULT_INSTRUCTIONS,
        capabilities=[Thinking(effort="high")],
    )

    @agent.tool_plain
    def read(path: str) -> dict[str, str]:
        """Read one file or a glob of files relative to the current working directory.

        Args:
            path: A relative file path or glob pattern to read.
        """
        return _read_files(path)

    @agent.tool_plain
    def write(path: str, content: str) -> str:
        """Write content to a single file relative to the current working directory.

        Args:
            path: A relative file path to write.
            content: The full file contents to write.
        """
        return _write_file(path, content)

    @agent.tool_plain
    def search(
        pattern: str,
        path: str = ".",
        context_lines: int = 2,
    ) -> list[dict[str, Any]]:
        """Search files with ripgrep and return matches with context snippets.

        Args:
            pattern: A regular expression to search for.
            path: A relative file path, directory, or glob pattern to limit the search.
            context_lines: Number of lines of context to include around each match.
        """
        return _search_files(pattern, path=path, context_lines=context_lines)

    return agent


def _read_files(path: str) -> dict[str, str]:
    """Read one file or a glob of files relative to the current working directory."""
    files = _resolve_paths(path)
    return {str(file): file.read_text(encoding="utf-8") for file in files}


def _write_file(path: str, content: str) -> str:
    """Write content to a single file relative to the current working directory."""
    target = _resolve_relative_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Wrote {target}"


def _search_files(
    pattern: str,
    *,
    path: str = ".",
    context_lines: int = 2,
) -> list[dict[str, Any]]:
    """Search files with rg or grep and return grouped matches with context snippets."""
    targets = _resolve_search_targets(path)

    if shutil.which("rg"):
        return _search_with_rg(
            pattern,
            targets=targets,
            context_lines=context_lines,
        )

    return _search_with_grep(
        pattern,
        targets=targets,
        context_lines=context_lines,
    )


def _search_with_rg(
    pattern: str,
    *,
    targets: list[Path],
    context_lines: int,
) -> list[dict[str, Any]]:
    """Search with ripgrep and return grouped matches."""
    command = ["rg", "-n", "--json", pattern, *[str(target) for target in targets]]
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode not in {0, 1}:
        raise RuntimeError(result.stderr.strip() or "rg failed")

    grouped_matches: dict[str, list[dict[str, Any]]] = {}
    for line in result.stdout.splitlines():
        event = json.loads(line)
        if event.get("type") != "match":
            continue

        data = event["data"]
        file_path = _normalize_result_path(data["path"]["text"])
        line_number = data["line_number"]
        _add_match(
            grouped_matches,
            file_path=file_path,
            line_number=line_number,
            context_lines=context_lines,
        )

    return _format_search_results(grouped_matches)


def _search_with_grep(
    pattern: str,
    *,
    targets: list[Path],
    context_lines: int,
) -> list[dict[str, Any]]:
    """Search with grep and return grouped matches."""
    command = ["grep", "-R", "-n", "-E", pattern, *[str(target) for target in targets]]
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode not in {0, 1}:
        raise RuntimeError(result.stderr.strip() or "grep failed")

    grouped_matches: dict[str, list[dict[str, Any]]] = {}
    for line in result.stdout.splitlines():
        file_path, line_number, _matched_text = line.split(":", maxsplit=2)
        _add_match(
            grouped_matches,
            file_path=_normalize_result_path(file_path),
            line_number=int(line_number),
            context_lines=context_lines,
        )

    return _format_search_results(grouped_matches)


def _resolve_paths(path: str) -> list[Path]:
    """Resolve a relative file path or glob pattern into a sorted list of files."""
    _validate_relative_path_input(path)

    candidate = Path(path)
    if candidate.is_file():
        return [_resolve_relative_path(path)]

    files = sorted(
        _ensure_within_cwd(file.resolve()).relative_to(Path.cwd().resolve())
        for file in Path().glob(path)
        if file.is_file()
    )
    return files


def _resolve_search_targets(path: str) -> list[Path]:
    """Resolve a search path into files or directories for external search tools."""
    if path in {"", "."}:
        return [Path(".")]

    _validate_relative_path_input(path)
    candidate = Path(path)
    if candidate.exists():
        resolved = _ensure_within_cwd(candidate.resolve())
        return [resolved.relative_to(Path.cwd().resolve())]

    matches = sorted(
        _ensure_within_cwd(match.resolve()).relative_to(Path.cwd().resolve())
        for match in Path().glob(path)
    )
    if matches:
        return matches

    return [candidate]


def _resolve_relative_path(path: str) -> Path:
    """Resolve one relative path and ensure it stays within the current directory."""
    _validate_relative_path_input(path)
    resolved = _ensure_within_cwd(Path(path).resolve())
    return resolved.relative_to(Path.cwd().resolve())


def _validate_relative_path_input(path: str) -> None:
    """Reject absolute or parent-traversing paths before file operations."""
    path_obj = Path(path)
    if path_obj.is_absolute() or ".." in path_obj.parts:
        raise ValueError("Paths must stay within the current working directory")


def _ensure_within_cwd(path: Path) -> Path:
    """Ensure a resolved path is within the current working directory."""
    cwd = Path.cwd().resolve()

    try:
        path.relative_to(cwd)
    except ValueError as exc:
        raise ValueError(
            "Paths must stay within the current working directory"
        ) from exc

    return path


def _normalize_result_path(path: str) -> str:
    """Normalize search output paths and keep them within the current directory."""
    normalized = path.removeprefix("./")
    return str(_resolve_relative_path(normalized))


def _add_match(
    grouped_matches: dict[str, list[dict[str, Any]]],
    *,
    file_path: str,
    line_number: int,
    context_lines: int,
) -> None:
    """Add one grouped search match with a context snippet."""
    snippet = _build_snippet(
        Path(file_path),
        line_number=line_number,
        context_lines=context_lines,
    )
    grouped_matches.setdefault(file_path, []).append(
        {"line_number": line_number, "snippet": snippet}
    )


def _format_search_results(
    grouped_matches: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Format grouped search matches as a stable list."""
    return [
        {"path": file_path, "matches": matches}
        for file_path, matches in sorted(grouped_matches.items())
    ]


def _build_snippet(path: Path, *, line_number: int, context_lines: int) -> str:
    """Build a small numbered context snippet around a matching line."""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = max(1, line_number - context_lines)
    end = min(len(lines), line_number + context_lines)

    snippet_lines = [
        f"{current_line}: {lines[current_line - 1]}"
        for current_line in range(start, end + 1)
    ]
    return "\n".join(snippet_lines)
