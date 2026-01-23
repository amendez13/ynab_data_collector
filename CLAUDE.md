# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A CLI app that connects to a user's YNAB and exports budget data to JSON.

**Core workflow**:
1. Load configuration from `config/config.yaml` (if present) and environment variables.
2. Initialize `YnabClient` with the API token.
3. Fetch budgets and current month data from the YNAB API.
4. Parse responses into Pydantic models.
5. Export normalized JSON via `JsonExporter`.

## Constraints and Best Practices

- This project is documentation-driven. Before starting work, read:
  - `README.md`
  - `docs/INDEX.md`
- After finishing any task, update relevant documentation given changes in codebase.
- Pre-commit checks must pass before committing. If pre-commit doesn't run, investigate and fix.
- `pyproject.toml`, `.github/workflows/ci.yml`, and `.pre-commit-config.yaml` must align so local and CI checks match.
- Any code quality exceptions must be documented with a comment in code.
- Branch naming: `feature/description`, `fix/description`, `docs/description`
- Commit messages: Use conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`)

## Architecture

### Technology Stack
- **Python**: 3.10+
- **requests**: HTTP client for YNAB API communication
- **pydantic + pydantic-settings**: Data validation and configuration management
- **click**: CLI framework
- **PyYAML**: YAML configuration parsing
- **python-dotenv**: Optional `.env` loading

### Test/Dev Dependencies
- **pytest / pytest-cov / pytest-mock**: Testing and coverage
- **requests-mock**: Mock YNAB API responses in tests
- **black / isort / flake8 / mypy**: Code quality tools
- **bandit / pip-audit**: Security checks

### Key Components
1. **CLI** (`src/main.py`): Click commands, config loading, error handling, and export workflow.
2. **Configuration** (`src/config.py`): Loads YAML + env vars, validates settings, sets defaults.
3. **YNAB Client** (`src/ynab/client.py`): HTTP wrapper for YNAB endpoints with error translation.
4. **Models** (`src/ynab/models.py`): Pydantic models and milliunit helpers.
5. **Exporters** (`src/exporters/json_exporter.py`): Builds and writes JSON output.

### Processing Strategy
- CLI resolves config, budgets, and month data in sequence.
- API errors map to custom exceptions and user-friendly CLI messages.
- JSON export formats metadata, summary totals, and categories.

## Development Commands

### Initial Setup

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows

pip install -r requirements.txt
pip install -r requirements-dev.txt

pre-commit install

cp config/config.example.yaml config/config.yaml
```

### Running Tests

```bash
pytest
pytest --cov=src --cov-report=term-missing
pytest tests/test_main.py
```

### Common Commands

```bash
# Linting
black src/
isort src/
flake8 src/
mypy src/

# Security checks
bandit -r src/ -ll
pip-audit --requirement requirements.txt
```

### Running the Application

```bash
python -m src.main --help
```
