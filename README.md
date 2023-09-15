# llm-code

![PyPi](https://img.shields.io/pypi/v/llm-code?color=green)
[![Coverage Status](https://coveralls.io/repos/github/radoshi/llm-code/badge.svg?branch=main)](https://coveralls.io/github/radoshi/llm-code?branch=main)

---

An OpenAI LLM based CLI coding assistant.

`llm-code` is inspired by
[Simon Wilson](https://simonwillison.net/2023/May/18/cli-tools-for-llms/)'s
[llm](https://github.com/simonw/llm) package. It takes a similar approach of developing
a simple tool to create an LLM based assistant that helps write code.

## Installation

```bash
pipx install llm-code
```

## Configuration

`llm-code` requires an OpenAI API key. You can get one from [OpenAI](https://openai.com/).

You can set the key in a few different ways, depending on your preference:

1. Set the `OPENAI_API_KEY` environment variable.

```bash
export OPENAI_API_KEY = sk-...
```

2. Use an env file in ~/.llm_code/env

```bash
mkdir -p ~/.llm_code
echo "OPENAI_API_KEY=sk-..." > ~/.llm_code/env
```

## Usage

`llm-code` is meant to be simple to use. The default prompts should be good enough. There are two broad modes:

1. Generage some code from scratch.

```bash
llm-code write a function that takes a list of numbers and returns the sum of the numbers in python. Add type hints.
```

2. Give in some input files and ask for changes.

```bash
llm-code -i my_file.py add docstrings to all python functions.
```

```bash
llm-code --help
```

```
Usage: llm-code [OPTIONS] [INSTRUCTIONS]...

  Coding assistant using OpenAI's chat models.

  Requires OPENAI_API_KEY as an environment variable. Alternately, you can set
  it in ~/.llm_code/env.

Options:
  -i, --inputs TEXT  Glob of input files. Use repeatedly for multiple files.
  -cb, --clipboard   Copy code to clipboard.
  -nc, --no-cache    Don't use cache.
  -4, --gpt-4        Use GPT-4.
  --version          Show version.
  --help             Show this message and exit.
```

## Changing OpenAI parameters

Any of the OpenAI parameters can be changed using environment variables. GPT-4 is one exception: you can also set it using `-4` for convenience.

```bash
export MAX_TOKENS=2000
export TEMPERATURE=0.5
export MODEL=gpt-4
```

or

```bash
llm-code -4 ...
```

## Caching

A common usage pattern is to examine the output of a model and either accept it, or continue to play around with the prompts. When "accepting" the output, a common thing is to append it to a file, or copy it to the clipboard (using `pbcopy` on a mac, for example.). To facilitate this workflow of inspection and acceptance, `llm-code` caches the output of the model in a local sqlite database. This allows you to replay the same query without having to hit the OpenAI API.

```bash
llm-code 'write a function that takes a list of numbers and returns the sum of the numbers in python. Add type hints.'
```

Following this, assuming you like the output:

```bash
llm-code 'write a function that takes a list of numbers and returns the sum of the numbers in python. Add type hints.' > sum.py
```

## Database

Borrowing simonw's excellent idea of logging things to a local sqlite, as demonstrated in [`llm`](https://github.com/simonw/llm), `llm-code` also logs all queries to a local sqlite database. This is useful for a few reasons:

1. It allows you to replay the same query without having to hit the OpenAI API.
2. It allows you to see what queries you've made in the past with responses, and number of tokens used.

## Examples

Simple hello world.

```bash
llm-code write hello world in rust
```

```rust
fn main() {
    println!("Hello, world!");
}
```

---

Sum of two numbers with type hints.

```bash
llm-code write a function that takes a list of numbers and returns the sum of the numbers in python. Add type hints.
```

```python
from typing import List

def sum_numbers(numbers: List[int]) -> int:
    return sum(numbers)
```

---

Lets assume that we stuck the output of the previous call in `out.py`. We can now say:

```bash
llm-code -i out.py add appropriate docstrings
```

```python
from typing import List

def sum_numbers(numbers: List[int]) -> int:
    """Return the sum of the given list of numbers."""
    return sum(numbers)
```

---

Or we could write some unit tests.

```bash
llm-code -i out.py write a complete unit test file using pytest.
```

```python
import pytest

from typing import List
from my_module import sum_numbers


def test_sum_numbers():
    assert sum_numbers([1, 2, 3]) == 6
    assert sum_numbers([-1, 0, 1]) == 0
    assert sum_numbers([]) == 0
```

## TODO

- [X] Add a simple cache to replay the same query.
- [X] Add logging to a local sqllite db.
- [ ] Add an `--exec` option to execute the generated code.
- [ ] Add a `--stats` option to output token counts.
- [X] Add `pyperclip` integration to copy to clipboard.