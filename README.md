# llm-code

`llm-code` is a small command-line coding agent built on top of
[pydantic-ai](https://ai.pydantic.dev/).

The current goal is simple: run an agent from your terminal, let it inspect and modify
files in the current project, and stream the model's response back to stdout.

## What it does

Today, the CLI is intentionally minimal:

```bash
uv run llm_code "write hello world"
```

Everything after `llm_code` is treated as the prompt. The tool loads configuration,
constructs an agent, and streams the result to the terminal.

The agent currently has access to a few local tools:

- `read`: read a file or glob of files under the current working directory
- `write`: write a single file under the current working directory
- `search`: search files by regex, using `rg` when available and `grep` as a fallback
- `bash`: execute a shell command in the current working directory

## Architecture overview

The codebase is deliberately split into a few small modules.

### `src/llm_code/llm_code.py`

This is the CLI entrypoint.

It is responsible for:

- parsing the command line with `click`
- loading settings
- joining the remaining CLI arguments into a single prompt string
- building the runtime agent
- streaming the final output to the terminal with `rich`

### `src/llm_code/settings.py`

This module handles configuration loading and precedence.

Current settings precedence is:

1. built-in defaults
2. user config from `XDG_CONFIG_HOME/llm_code/config.toml`
3. fallback user config from `~/.config/llm_code/config.toml`
4. nearest project config found by walking upward for `.config.yaml`
5. environment variables

In other words, project config overrides user config, and environment variables override
both.

At the moment, settings are modeled with a small `pydantic` model.

### `src/llm_code/agent.py`

This module builds the `pydantic_ai.Agent` and registers its tools.

The agent currently uses:

- a fixed instruction string
- a configurable model name from settings
- `Thinking(effort="high")`

It also contains the implementation details for the agent tools.

#### Tool design

The current tools are local-first and cwd-scoped.

- file reads, writes, and searches are restricted to the current working directory
- absolute paths and `..` traversal are rejected for file-oriented tools
- search results are normalized back to relative paths

Tool summary:

- `read(path)`
  - accepts a relative path or glob
  - returns a mapping of file paths to file contents
- `write(path, content)`
  - writes one file
  - creates parent directories as needed
- `search(pattern, path=".", context_lines=2)`
  - searches with `rg --json` when available
  - falls back to `grep -R -n -E`
  - returns grouped matches with a small numbered context snippet
- `bash(command)`
  - executes a shell command with `shell=True`
  - returns `returncode`, `stdout`, and `stderr`

The `bash` tool is intentionally permissive right now and should be treated as unsafe.

## Testing

Tests live in `tests/`.

Current coverage focuses on:

- settings precedence and config loading
- file tool behavior
- search behavior, including `rg` fallback to `grep`
- path safety for read/write/search
- bash command execution

Run tests with:

```bash
uv run pytest
```

## Development

Install dependencies:

```bash
uv sync --all-groups
```

Run the CLI:

```bash
uv run llm_code "summarize this repository"
```

Run lint and tests:

```bash
uv run ruff check src tests
uv run pytest
```

## Status

This project is in an early, exploratory stage.

The current implementation is intentionally small so the core architecture is easy to
change:

- simple CLI
- simple settings model
- one agent module
- local tools with lightweight tests

## TODO

- improve the system prompt and overall agent behavior
- add better tool result formatting so prompts stay compact
- add truncation and size limits for large file reads and large search results
- add stdin and richer project-context input modes
- add better search filtering and more useful snippets
- add structured logging / execution traces for debugging agent runs
- add streaming or incremental feedback for long-running tool calls
- add approval flows for dangerous tool use
- add timeouts for shell execution
- add output truncation for shell execution
- add command allow/deny rules for shell execution
- add explicit approval before executing shell commands
- add sandboxing for shell commands
- add no-network execution mode for shell commands
- add stronger filesystem isolation beyond starting in the current working directory
