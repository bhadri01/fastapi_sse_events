.PHONY: help install install-dev test lint format type-check clean build publish docs

help:  ## Show this help message
	@echo "FastAPI SSE Events - Development Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install package for production
	pip install -e .

install-dev:  ## Install package with dev dependencies
	pip install -e ".[dev]"

test:  ## Run tests with coverage
	pytest tests/ -v --cov=fastapi_sse_events --cov-report=term-missing --cov-report=html

test-fast:  ## Run tests without coverage
	pytest tests/ -v

lint:  ## Run linting checks
	ruff check fastapi_sse_events/ tests/ examples/

format:  ## Format code with ruff
	ruff format fastapi_sse_events/ tests/ examples/

format-check:  ## Check code formatting without making changes
	ruff format --check fastapi_sse_events/ tests/ examples/

type-check:  ## Run type checking with mypy
	mypy fastapi_sse_events/

check-all:  ## Run all checks (lint, format, type-check, test)
	@echo "Running linting..."
	@$(MAKE) lint
	@echo "\nChecking formatting..."
	@$(MAKE) format-check
	@echo "\nType checking..."
	@$(MAKE) type-check
	@echo "\nRunning tests..."
	@$(MAKE) test

clean:  ## Clean build artifacts and cache files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:  ## Build distribution packages
	python -m build

publish-test:  ## Publish to TestPyPI
	python -m twine upload --repository testpypi dist/*

publish:  ## Publish to PyPI
	python -m twine upload dist/*

docs:  ## Serve documentation locally
	@echo "Opening documentation..."
	@python -m http.server 8080 --directory docs

setup-redis:  ## Start Redis using Docker
	docker run -d -p 6379:6379 --name fastapi-sse-redis redis:alpine

stop-redis:  ## Stop Redis container
	docker stop fastapi-sse-redis
	docker rm fastapi-sse-redis

example-quickstart:  ## Run quickstart example
	cd examples/quickstart && uvicorn app:app --reload

example-crm:  ## Run CRM comments example
	cd examples/crm_comments && uvicorn app:app --reload

.DEFAULT_GOAL := help
