.PHONY: install build test test-watch test-cov

install:
	@echo "Installing dependencies..."
	@poetry install

build:
	@echo "Building..."
	@poetry build

test:
	@echo "Running tests..."
	@poetry run pytest

test-watch:
	@echo "Running tests..."
	@poetry run ptw

test-cov:
	@echo "Running tests with coverage..."
	@poetry run pytest --cov llm_code --cov-report term-missing