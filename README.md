# llm-code

An OpenAI LLM based CLI coding assistant.

`llm-code` is inspired by
[Simon Wilson](https://simonwillison.net/2023/May/18/cli-tools-for-llms/)'s
[llm](https://github.com/simonw/llm) package. It takes a similar approach of developing
a simple tool to create an LLM based assistant that helps write code.

## Installation

```bash
pipx install llm-code
```

## Usage

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

Sum of two numbers with type hints.

```bash
llm-code write a function that takes a list of numbers and returns the sum of the numbers in python. Add type hints.
```

```python
from typing import List

def sum_numbers(numbers: List[int]) -> int:
    return sum(numbers)
```

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
