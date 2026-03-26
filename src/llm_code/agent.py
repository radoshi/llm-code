"""Agent construction and local developer tools.

This module builds the coding agent and wires in a small set of tools for
working with files and the local shell. All file access is restricted to the
current working directory so prompts cannot read or write outside the project
root.
"""

import asyncio
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.capabilities import Thinking

DEFAULT_INSTRUCTIONS = "You are an expert at coding."


def build_agent(model: str) -> Agent:
    """Build an agent configured with local filesystem and shell tools.

    Args:
        model: The model identifier passed to ``pydantic_ai.Agent``.

    Returns:
        An agent instance with read, write, search, and bash tools registered.
    """
    agent = Agent(
        model,
        instructions=DEFAULT_INSTRUCTIONS,
        capabilities=[Thinking(effort="high")],
    )

    @agent.tool_plain
    async def read(path: str) -> dict[str, str]:
        """Read one file or a glob of files relative to the current directory.

        Args:
            path: A relative file path or glob pattern to read.

        Returns:
            A mapping of relative file paths to file contents.
        """
        return await _read_files(path)

    @agent.tool_plain
    async def write(path: str, content: str) -> str:
        """Write content to a single file relative to the current directory.

        Args:
            path: A relative file path to write.
            content: The full file contents to write.

        Returns:
            A short confirmation message describing the written file.
        """
        return await _write_file(path, content)

    @agent.tool_plain
    async def search(
        pattern: str,
        path: str = ".",
        context_lines: int = 2,
    ) -> list[dict[str, Any]]:
        """Search files and return grouped matches with context snippets.

        Args:
            pattern: A regular expression to search for.
            path: A relative file path, directory, or glob pattern to limit the
                search.
            context_lines: Number of surrounding lines to include in each
                snippet.

        Returns:
            A list of per-file match groups with line numbers and snippets.
        """
        return await _search_files(pattern, path=path, context_lines=context_lines)

    @agent.tool_plain
    async def bash(command: str) -> dict[str, Any]:
        """Execute a shell command in the current working directory.

        Args:
            command: The shell command to execute.

        Returns:
            A mapping containing the command's return code, stdout, and stderr.
        """
        return await _run_bash(command)

    return agent


async def _read_files(path: str) -> dict[str, str]:
    """Read one or more files selected by a relative path or glob pattern.

    Args:
        path: A relative file path or glob pattern rooted at the current working
            directory.

    Returns:
        A mapping of relative file paths to their UTF-8 contents.
    """
    files = _resolve_paths(path)
    return await asyncio.to_thread(_read_files_sync, files)


async def _write_file(path: str, content: str) -> str:
    """Write UTF-8 text to a file within the current working directory.

    Args:
        path: The relative path to write.
        content: The full file contents.

    Returns:
        A confirmation message describing the written file.
    """
    target = _resolve_relative_path(path)
    return await asyncio.to_thread(_write_file_sync, target, content)


async def _search_files(
    pattern: str,
    *,
    path: str = ".",
    context_lines: int = 2,
) -> list[dict[str, Any]]:
    """Search files using ``rg`` when available and ``grep`` otherwise.

    Args:
        pattern: The regular expression to search for.
        path: A relative path, directory, or glob pattern used to restrict the
            search scope.
        context_lines: The number of lines of context to include before and
            after each matching line.

    Returns:
        A list of grouped match records keyed by relative file path.
    """
    targets = _resolve_search_targets(path)
    return await asyncio.to_thread(
        _search_files_sync,
        pattern,
        targets,
        context_lines,
    )


async def _run_bash(command: str) -> dict[str, Any]:
    """Execute a shell command without blocking the event loop.

    Args:
        command: The shell command to execute.

    Returns:
        A mapping with ``returncode``, ``stdout``, and ``stderr`` keys.
    """
    return await asyncio.to_thread(_run_bash_sync, command)


def _read_files_sync(files: list[Path]) -> dict[str, str]:
    """Synchronously read a list of UTF-8 text files.

    Args:
        files: Relative file paths to read.

    Returns:
        A mapping of file paths to file contents.
    """
    return {str(file): file.read_text(encoding="utf-8") for file in files}


def _write_file_sync(target: Path, content: str) -> str:
    """Synchronously write text to a file, creating parent directories.

    Args:
        target: The relative file path to write.
        content: The full file contents.

    Returns:
        A confirmation message describing the written file.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Wrote {target}"


def _search_files_sync(
    pattern: str,
    targets: list[Path],
    context_lines: int,
) -> list[dict[str, Any]]:
    """Synchronously search files with the best available external tool.

    Args:
        pattern: The regular expression to search for.
        targets: Relative files or directories to search.
        context_lines: Number of surrounding lines to include in each snippet.

    Returns:
        A list of grouped match records.
    """
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


def _run_bash_sync(command: str) -> dict[str, Any]:
    """Synchronously execute a shell command in the current directory.

    Args:
        command: The shell command to execute.

    Returns:
        A mapping with the subprocess return code, stdout, and stderr.
    """
    result = subprocess.run(
        command,
        shell=True,
        check=False,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def _search_with_rg(
    pattern: str,
    *,
    targets: list[Path],
    context_lines: int,
) -> list[dict[str, Any]]:
    """Search with ripgrep and convert matches into grouped result records.

    Args:
        pattern: The regular expression to search for.
        targets: Relative files or directories to search.
        context_lines: Number of surrounding lines to include in each snippet.

    Returns:
        A list of grouped match records.

    Raises:
        RuntimeError: If ``rg`` exits with an unexpected failure code.
    """
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
    """Search with grep and convert matches into grouped result records.

    Args:
        pattern: The regular expression to search for.
        targets: Relative files or directories to search.
        context_lines: Number of surrounding lines to include in each snippet.

    Returns:
        A list of grouped match records.

    Raises:
        RuntimeError: If ``grep`` exits with an unexpected failure code.
    """
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
    """Resolve a relative file path or glob pattern into a sorted file list.

    Args:
        path: A relative file path or glob pattern.

    Returns:
        A sorted list of relative file paths.
    """
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
    """Resolve a search path into files or directories for search commands.

    Args:
        path: A relative path, directory, or glob pattern.

    Returns:
        A list of relative paths suitable for passing to ``rg`` or ``grep``.
    """
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
    """Resolve a single relative path and keep it within the current directory.

    Args:
        path: A relative path provided by the caller.

    Returns:
        The normalized relative path.
    """
    _validate_relative_path_input(path)
    resolved = _ensure_within_cwd(Path(path).resolve())
    return resolved.relative_to(Path.cwd().resolve())


def _validate_relative_path_input(path: str) -> None:
    """Reject absolute and parent-traversing paths before file operations.

    Args:
        path: The user-provided path to validate.

    Raises:
        ValueError: If the path is absolute or attempts to escape the current
            working directory.
    """
    path_obj = Path(path)
    if path_obj.is_absolute() or ".." in path_obj.parts:
        raise ValueError("Paths must stay within the current working directory")


def _ensure_within_cwd(path: Path) -> Path:
    """Ensure a resolved path remains inside the current working directory.

    Args:
        path: A fully resolved filesystem path.

    Returns:
        The same resolved path when it is safe to use.

    Raises:
        ValueError: If the resolved path points outside the current working
            directory.
    """
    cwd = Path.cwd().resolve()

    try:
        path.relative_to(cwd)
    except ValueError as exc:
        raise ValueError(
            "Paths must stay within the current working directory"
        ) from exc

    return path


def _normalize_result_path(path: str) -> str:
    """Normalize search output paths and revalidate them as relative paths.

    Args:
        path: A path string emitted by an external search tool.

    Returns:
        A normalized relative path string rooted at the current directory.
    """
    normalized = path.removeprefix("./")
    return str(_resolve_relative_path(normalized))


def _add_match(
    grouped_matches: dict[str, list[dict[str, Any]]],
    *,
    file_path: str,
    line_number: int,
    context_lines: int,
) -> None:
    """Add one search hit and its snippet to the grouped result mapping.

    Args:
        grouped_matches: Accumulator keyed by file path.
        file_path: Relative path of the file containing the match.
        line_number: One-based line number reported by the search tool.
        context_lines: Number of surrounding lines to include in the snippet.
    """
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
    """Convert grouped match mappings into a stable, sorted result list.

    Args:
        grouped_matches: Matches keyed by relative file path.

    Returns:
        A sorted list of search result dictionaries.
    """
    return [
        {"path": file_path, "matches": matches}
        for file_path, matches in sorted(grouped_matches.items())
    ]


def _build_snippet(path: Path, *, line_number: int, context_lines: int) -> str:
    """Build a numbered context snippet around a matching line.

    Args:
        path: Relative path to the file being summarized.
        line_number: One-based line number of the match.
        context_lines: Number of surrounding lines to include before and after
            the match.

    Returns:
        A newline-delimited snippet with line numbers prefixed.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    start = max(1, line_number - context_lines)
    end = min(len(lines), line_number + context_lines)

    snippet_lines = [
        f"{current_line}: {lines[current_line - 1]}"
        for current_line in range(start, end + 1)
    ]
    return "\n".join(snippet_lines)
