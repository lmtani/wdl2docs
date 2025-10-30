.PHONY: help install test test-cov lint format clean migration migrate db-init db-reset dev-setup all

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development setup
install: ## Install dependencies
	uv sync --all-extras

# Code quality
lint: ## Run linting checks (ruff check)
	@echo "🔍 Running linter..."
	uv run ruff check src tests

typecheck: ## Run type checking with mypy
	@echo "🔍 Running type checker..."
	uv run mypy --explicit-package-bases src

format: ## Format code with ruff and autoflake
	@echo "🎨 Formatting code..."
	uv run autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place src tests
	uv run ruff format .

fix: ## Auto-fix linting issues and format code
	@echo "🔧 Auto-fixing issues and formatting..."
	uv run ruff check --fix .
	$(MAKE) format

test: ## Run tests with pytest
	@echo "🧪 Running tests..."
	uv run pytest -v --cov=src tests --cov-report=term

serve: ## Serve generated documentation on localhost
	@echo "🌐 Starting documentation server..."
	python .scripts/serve_docs.py

