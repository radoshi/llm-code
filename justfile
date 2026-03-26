# Install all runtime and development dependencies into the project environment.
install:
	@echo "Syncing dependencies with uv..."
	@uv sync --all-groups

# Run the full test suite once.
test:
	@echo "Running tests..."
	@uv run pytest

# Re-run tests automatically when files change.
watch:
	@echo "Watching tests..."
	@uv run ptw -c

# Generate a coverage report in XML format.
coverage:
	@echo "Running tests with coverage..."
	@uv run pytest --cov llm_code --cov-report html

# Lint the codebase with Ruff.
lint:
	@echo "Linting with Ruff..."
	@uv run ruff check .

# Format the codebase with Ruff.
format:
	@echo "Formatting with Ruff..."
	@uv run ruff format .

# Run static type checking with ty.
typecheck:
	@echo "Type checking with ty..."
	@uv run ty check

# Build source and wheel distributions.
build:
	@echo "Building package..."
	@uv build

# Run the default local quality checks.
check: lint typecheck test format
