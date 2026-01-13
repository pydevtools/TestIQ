# Makefile for TestIQ

.PHONY: help install test lint format clean build publish

help:
	@echo "TestIQ - Development Commands"
	@echo ""
	@echo "install     - Install package with dev dependencies"
	@echo "test        - Run tests with coverage"
	@echo "test-fast   - Run tests without coverage"
	@echo "lint        - Run ruff linter"
	@echo "format      - Format code with black and ruff"
	@echo "format-check- Check code formatting"
	@echo "clean       - Remove build artifacts and cache files"
	@echo "build       - Build distribution packages"
	@echo "publish-test- Publish to TestPyPI"
	@echo "publish     - Publish to PyPI"
	@echo "demo        - Run TestIQ demo"
	@echo "dev         - Install in development mode"

install:
	uv pip install --system -e ".[dev]"

dev: install

test:
	pytest tests/ -v --cov=testiq --cov-report=term --cov-report=html

test-fast:
	pytest tests/ -v

lint:
	ruff check src/ tests/

format:
	ruff check src/ tests/ --fix
	python -m black src/ tests/

format-check:
	ruff check src/ tests/
	python -m black --check src/ tests/

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf src/*.egg-info
	@echo "Cleaning Python cache..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.py,cover" -delete
	@echo "Cleaning test and coverage artifacts..."
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	@echo "Cleaning temporary files..."
	find . -type f -name "*~" -delete
	find . -type f -name "*.bak" -delete
	@echo "Clean complete!"

build: clean
	@echo "Building package..."
	uv build

publish-test: build
	@echo "Publishing to TestPyPI..."
	@echo "Make sure you have TESTPYPI_TOKEN set"
	uv publish --token $(TESTPYPI_TOKEN) --publish-url https://test.pypi.org/legacy/

publish: build
	@echo "Publishing to PyPI..."
	@echo "Make sure you have PYPI_TOKEN set"
	uv publish --token $(PYPI_TOKEN)

demo:
	python -m testiq.cli demo

# Development helpers
watch-test:
	pytest-watch tests/

coverage-report:
	pytest tests/ --cov=testiq --cov-report=html
	open htmlcov/index.html
