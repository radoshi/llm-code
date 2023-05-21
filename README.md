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

  Ask for code completion from OpenAI's chat models.

Options:
  -i, --inputs TEXT  Glob of input files.
  --help             Show this message and exit.
```

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

- [ ] Add a simple cache to replay the same query.
- [ ] Add an `--exec` option to execute the generated code.
- [ ] Add a `--stats` option to output token counts.
- [ ] Add logging to a local sqllite db.
