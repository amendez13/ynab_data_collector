# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A CLI app that connects to a user's YNAB and fetches data into different file formats.

**Core workflow**: [Describe the main workflow of your application]

## Constraints and Best Practices

* This project is documentation-driven. Before starting work, read:
  * README.md
  * docs/INDEX.md
* After finishing any task, update relevant documentation given changes in codebase.
* Pre-commit checks must pass before committing. If pre-commit doesn't run, investigate and fix.
** pyproject.toml, ci.yml and pre-commit-config.yaml have to have the same configuration so local pre-commit and CI checks behave in the same way.
** Any code quality exceptions must be properly documented with a comment in code.
* Branch naming: `feature/description`, `fix/description`, `docs/description`
* Commit messages: Use conventional commits (feat:, fix:, docs:, refactor:, test:, chore:)

## Architecture

### Technology Stack
- **Python**: 3.10+
- **requests**: HTTP client for YNAB API communication
- **pydantic**: Data validation, settings management, and model serialization
- **click**: CLI framework for building the command-line interface
- **PyYAML**: Configuration file parsing
- **python-dotenv**: Environment variable management

### Key Components
1. **Configuration Module** (`src/config.py`):
   - Loads settings from YAML files and environment variables
   - API tokens loaded from `YNAB_API_TOKEN` env var (never from files)
   - Uses Pydantic for validation and type safety

2. **YNAB Client** (planned: `src/ynab/client.py`):
   - HTTP client for YNAB API communication
   - Handles authentication and error responses

3. **Exporters** (planned: `src/exporters/`):
   - Export budget data to various formats (JSON, CSV, etc.)

### Processing Strategy
- [Describe your main processing approach]
- Error handling and recovery
- Logging and monitoring

## Development Commands

### Initial Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Copy and configure settings
cp config/config.example.yaml config/config.yaml
# Edit config/config.yaml with your settings
```

### Running Tests

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Run all tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_main.py
```

### Common Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Update dependencies
pip install --upgrade -r requirements.txt

# Run linting
black src/
isort src/
flake8 src/
mypy src/

# Run security checks
bandit -r src/ -ll

# Deactivate virtual environment when done
deactivate
```

### Running the Application

```bash
# Activate virtual environment
source venv/bin/activate

# Run main application
python -m src.main
```
