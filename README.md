# llm-code

![PyPi](https://img.shields.io/pypi/v/llm-code?color=green)
[![Coverage Status](https://coveralls.io/repos/github/radoshi/llm-code/badge.svg?branch=main)](https://coveralls.io/github/radoshi/llm-code?branch=main)

An OpenAI-based CLI coding assistant.

`llm-code` is inspired by
[Simon Willison](https://simonwillison.net/2023/May/18/cli-tools-for-llms/)'s
[`llm`](https://github.com/simonw/llm). It focuses on a simple command-line workflow for
asking an LLM to generate or modify code.

## Requirements

- Python `3.14.3`
- An `OPENAI_API_KEY`
- [`uv`](https://docs.astral.sh/uv/)

## Development setup

```bash
uv sync --all-groups
```

This project uses:

- `uv` for environment and dependency management
- `ruff` for linting and formatting
- `ty` for type checking
- `pytest` for tests
- `just` for common development commands

If you use `pyenv`, `mise`, or another version manager, `.python-version` is set to:

```text
3.14.3
```

## Configuration

`llm-code` requires an OpenAI API key. You can get one from [OpenAI](https://openai.com/).

You can configure it in either of these ways:

1. Set the `OPENAI_API_KEY` environment variable:

```bash
export OPENAI_API_KEY=sk-...
```

2. Use an env file at `~/.llm_code/env`:

```bash
mkdir -p ~/.llm_code
echo "OPENAI_API_KEY=sk-..." > ~/.llm_code/env
```

## Usage

Generate code from scratch:

```bash
uv run llm-code "write a function that takes a list of numbers and returns the sum in python. Add type hints."
```

Pass one or more input files and ask for changes:

```bash
uv run llm-code -i my_file.py "add docstrings to all python functions"
```

Show help:

```bash
uv run llm-code --help
```

## OpenAI parameters

The app reads settings from environment variables and `~/.llm_code/env`.

Examples:

```bash
export MODEL=gpt-4
export TEMPERATURE=0.5
export MAX_TOKENS=2000
```

Or use the convenience flag:

```bash
uv run llm-code -4 "review this code"
```

## Caching

`llm-code` caches responses in a local SQLite database. This makes it easy to replay the
same prompt without making another API call.

Example:

```bash
uv run llm-code "write a function that takes a list of numbers and returns the sum in python. Add type hints."
```

Then, if you want to save the output:

```bash
uv run llm-code "write a function that takes a list of numbers and returns the sum in python. Add type hints." > sum.py
```

## Database

Like `llm`, this project logs requests and responses to a local SQLite database. That is
useful for:

1. Replaying previous queries without calling the API again
2. Inspecting past prompts, responses, and token counts

## Examples

Simple hello world:

```bash
uv run llm-code "write hello world in rust"
```

```rust
fn main() {
    println!("Hello, world!");
}
```

Add docstrings to an existing file:

```bash
uv run llm-code -i out.py "add appropriate docstrings"
```

```python
from typing import List

def sum_numbers(numbers: List[int]) -> int:
    """Return the sum of the given list of numbers."""
    return sum(numbers)
```

Generate tests:

```bash
uv run llm-code -i out.py "write a complete unit test file using pytest"
```

```python
import pytest

from my_module import sum_numbers


def test_sum_numbers():
    assert sum_numbers([1, 2, 3]) == 6
    assert sum_numbers([-1, 0, 1]) == 0
    assert sum_numbers([]) == 0
```

## Development commands

With `just` installed:

```bash
just install
just fmt
just lint
just typecheck
just test
just coverage
just build
just check
```

## TODO

- [x] Add a simple cache to replay the same query
- [x] Add logging to a local SQLite database
- [ ] Add an `--exec` option to execute the generated code
- [ ] Add a `--stats` option to output token counts
- [x] Add `pyperclip` integration to copy to clipboard
