.PHONY: install build test test-watch coverage publish

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

coverage:
	@echo "Running tests with coverage..."
	@poetry run pytest --cov llm_code --cov-report term-missing

publish:
	@echo "Publishing..."
	@poetry publish --build