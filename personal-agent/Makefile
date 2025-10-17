.PHONY: help install setup test run-cli run-daemon run-web clean

help:
	@echo "Personal Agent - Makefile commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install    - Install dependencies"
	@echo "  make setup      - Initial setup (install + create .env)"
	@echo ""
	@echo "Run:"
	@echo "  make run-cli    - Run terminal interface"
	@echo "  make run-daemon - Run background daemon"
	@echo "  make run-web    - Run web UI"
	@echo ""
	@echo "Development:"
	@echo "  make test       - Run tests"
	@echo "  make clean      - Clean generated files"

install:
	pip install -r requirements.txt

setup: install
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file. Please edit it and add your GEMINI_API_KEY"; \
	else \
		echo ".env file already exists"; \
	fi
	mkdir -p data

run-cli:
	python -m src.terminal.cli

run-daemon:
	python -m src.daemon.service

run-web:
	python -m src.web.app

test:
	pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf build dist
