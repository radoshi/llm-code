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
