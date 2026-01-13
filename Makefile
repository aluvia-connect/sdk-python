# Makefile for Aluvia Python SDK

.PHONY: help install install-dev test lint format typecheck clean build publish

help:
	@echo "Available commands:"
	@echo "  make install       - Install package"
	@echo "  make install-dev   - Install package with dev dependencies"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make typecheck     - Run type checker"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make build         - Build package"
	@echo "  make publish       - Publish to PyPI"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest -v

test-cov:
	pytest --cov=aluvia_sdk --cov-report=html --cov-report=term

lint:
	black --check aluvia_sdk tests examples
	isort --check aluvia_sdk tests examples

format:
	black aluvia_sdk tests examples
	isort aluvia_sdk tests examples

typecheck:
	mypy aluvia_sdk

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

publish: build
	python -m twine upload dist/*
