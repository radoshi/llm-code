# AGENTS.md

Guidance for coding agents working in this repository.

## Project

`llm-code` is a small Python CLI coding agent built on `pydantic-ai`.

Core files:
- `src/llm_code/llm_code.py` — CLI entrypoint and Rich status/output
- `src/llm_code/agent.py` — agent construction and tool implementations
- `src/llm_code/settings.py` — config loading and precedence

## Stack

- Python `>=3.14.3,<3.15`
- `uv`, `hatchling`
- `click`, `rich`
- `pydantic`, `pydantic-ai`, `PyYAML`
- `pytest`, `ruff`, `ty`

## Invariants

### CLI
- Entry point: `llm_code.llm_code:main`
- All positional args are joined into one prompt string
- Final model output streams to stdout
- Rich status/progress goes to stderr

### Settings precedence
Keep this order unless the task explicitly changes it:
1. defaults in `Settings`
2. `XDG_CONFIG_HOME/llm_code/config.toml`
3. `~/.config/llm_code/config.toml`
4. nearest `.config.yaml` walking upward from cwd
5. environment variables

Env var names are uppercased setting names.

### Tool safety
For file tools, do not weaken these rules unless explicitly asked:
- no absolute paths
- no `..` traversal
- resolved paths must remain inside cwd
- returned file paths should be relative

### Search
- prefer `rg --json`
- fall back to `grep -R -n -E`
- return matches grouped by file
- each match includes `line_number` and a numbered snippet

### Bash
- `bash` is intentionally unsafe right now
- do not describe it as sandboxed or approved
- if you change it, add tests and update docs

## Style

- use type hints
- keep helpers small
- keep blocking file/subprocess work off the event loop with `asyncio.to_thread(...)`
- keep docstrings concise
- use double quotes
- stay Ruff-compatible
- prefer minimal diffs over broad rewrites

## Tests and checks

When behavior changes, update tests in `tests/`.

Useful commands:
```bash
uv run pytest
uv run ruff check .
uv run ty check
```

## When editing files

If you change:
- `agent.py` → check `tests/test_agent.py`, `tests/test_llm_code.py`, `README.md`
- `settings.py` → check `tests/test_settings.py`, `README.md`
- `llm_code.py` → check `tests/test_llm_code.py`

## Practical rules

- Read `README.md` before large changes
- Preserve current CLI behavior unless asked otherwise
- Do not silently remove cwd/path safety checks
- Do not add dependencies without a clear need
- Do not edit generated or environment files in `dist/`, `.venv/`, caches, or `__pycache__`
- If behavior changes, update tests and docs
