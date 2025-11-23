SHELL 			:= /bin/bash
UV 				:= uv
PYPROJECT 		:= pyproject.toml
VENV_DIR 		:= .venv

.PHONY: all clean docs install test

# Export path for script resolution
export PYTHONPATH := $(shell pwd)

help:
	@echo "Available commands:"
	@echo "  make install          - Install dependencies"
	@echo "  make test             - Run all tests"
	@echo "  make test-cov         - Run tests with coverage"
	@echo "  make lint             - Check code style"
	@echo "  make format           - Auto-format code"
	@echo "  make docs             - Build sphinx docs"

install:
	$(UV) sync --extra dev

upgrade:
	$(UV) lock --upgrade
	$(UV) sync --extra dev

uninstall:
	rm -rf $(VENV_DIR)

clean:
	rm -rf build/ dist/ src/*.egg-info **/__pycache__ .coverage .pytest_cache/ .ruff_cache/

test:
	$(UV) run pytest tests/ -v

test-cov:
	$(UV) run pytest tests/ --cov=bin --cov-report=term-missing

lint:
	$(UV) run ruff format --check src tests
	$(UV) run ruff check src tests

format:
	$(UV) run ruff format src tests
	$(UV) run ruff check --select I001 --fix src tests # Only fixes import order

build:
	$(UV) build --sdist --wheel

docs:
	rm -f docs/reference/_autosummary/*.rst
	$(UV) run sphinx-build -b html docs/ build/docs/
