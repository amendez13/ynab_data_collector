# Architecture Documentation

This document describes the technical architecture of YNAB Data Collector.

## Overview

YNAB Data Collector is a CLI application that connects to the YNAB (You Need A Budget) API to extract budget data and export it to various file formats. The application follows a modular architecture with clear separation of concerns.

## How It Works

The CLI loads configuration, then the (planned) YNAB client fetches budget data from the API. Responses are parsed into Pydantic models in `src/ynab/models.py`, which provide validation, typed accessors, and currency conversion helpers. Exporters (planned) will consume these models and write normalized JSON or other formats to disk.

## Dependencies

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | >=2.31.0 | HTTP client for YNAB API communication |
| `pydantic` | >=2.0.0 | Data validation and serialization for API responses |
| `pydantic-settings` | >=2.0.0 | Configuration management with environment variable support |
| `click` | >=8.1.0 | CLI framework for command-line interface |
| `PyYAML` | >=6.0 | YAML configuration file parsing |
| `python-dotenv` | >=1.0.0 | Environment variable loading from .env files |

### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | >=7.4.0 | Testing framework |
| `pytest-cov` | >=4.1.0 | Test coverage reporting |
| `pytest-mock` | >=3.11.0 | Mocking utilities for tests |
| `requests-mock` | >=1.11.0 | HTTP request mocking for API tests |
| `black` | >=23.7.0 | Code formatting |
| `isort` | >=5.12.0 | Import sorting |
| `flake8` | >=6.1.0 | Linting |
| `mypy` | >=1.5.0 | Static type checking |
| `bandit` | >=1.7.5 | Security vulnerability scanning |

### Why These Dependencies?

**requests**: The de facto standard HTTP library for Python. Mature, well-documented, and supports session management for efficient API communication.

**pydantic v2**: Chosen for its performance improvements over v1, native support for JSON serialization, and excellent integration with type hints. Used for:
- Validating API responses
- Defining data models for budget information
- Managing configuration with `pydantic-settings`

**click**: Preferred over argparse for its decorator-based API, automatic help generation, and testability via `CliRunner`. Used by major projects like Flask and AWS CLI.

**requests-mock**: Enables testing API client code without making real HTTP requests, ensuring tests are fast and deterministic.

## System Components

### Component Diagram

```
┌─────────────────┐
│   CLI (main)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│     Config      │────▶│   YNAB Client   │ (planned)
└─────────────────┘     └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │    Models       │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │    Exporters    │ (planned)
                        └─────────────────┘
```

### Configuration Module

**Purpose**: Load and validate application settings from YAML files and environment variables.

**Responsibilities**:
- Load configuration from YAML files
- Load sensitive values (API tokens) from environment variables
- Validate configuration using Pydantic models
- Provide sensible defaults for optional settings

**Key Files**:
- `src/config.py`

**Usage**:
```python
from src.config import load_config

# Load from default path (config/config.yaml)
config = load_config()

# Access settings
print(config.ynab.base_url)      # YNAB API URL
print(config.ynab.budget_id)      # Budget to use
print(config.output_directory)    # Export directory

# API token is loaded from YNAB_API_TOKEN env var
print(config.ynab.api_token)
```

**Configuration Files**:
- `config/config.yaml` - Main configuration (gitignored)
- `config/config.example.yaml` - Template for users
- `.env` - Environment variables (gitignored)
- `.env.example` - Template for environment variables

### YNAB Data Models

**Purpose**: Represent YNAB API responses using typed, validated Pydantic models.

**Responsibilities**:
- Parse YNAB API payloads into Python objects
- Provide human-readable currency conversion helpers (milliunits to units)
- Offer JSON serialization for exporting data downstream

**Key Files**:
- `src/ynab/models.py`
- `src/ynab/__init__.py`

**Usage**:
```python
from src.ynab.models import Category, MonthDetail

category = Category(
    id="cat-1",
    category_group_id="group-1",
    name="Groceries",
    budgeted=10500,
    activity=-2500,
    balance=8000,
)

print(category.spent_amount)  # 2.5
print(category.to_json())     # JSON payload

month = MonthDetail(
    month="2024-02-01",
    income=150000,
    budgeted=120000,
    activity=-90000,
    to_be_budgeted=30000,
)
print(month.to_dict())        # JSON-friendly dict
```

### YNAB Client (Planned)

**Purpose**: Communicate with the YNAB API.

**Key Files**:
- `src/ynab/client.py` (planned)

### Exporters (Planned)

**Purpose**: Export budget data to various file formats.

**Key Files**:
- `src/exporters/json_exporter.py` (planned)

## Data Flow

1. Load configuration from YAML and environment variables.
2. Use the YNAB client to request budget data from the API (planned).
3. Parse API responses into Pydantic models in `src/ynab/models.py`.
4. Export validated model data to files via exporters (planned).

## Design Decisions

### Decision 1: API Token from Environment Variable Only

**Context**: API tokens are sensitive credentials that should never be stored in configuration files that might be accidentally committed to version control.

**Decision**: The YNAB API token is loaded exclusively from the `YNAB_API_TOKEN` environment variable. Even if an `api_token` field appears in the YAML config, it is ignored.

**Consequences**:
- Pro: Prevents accidental credential exposure in git
- Pro: Follows security best practices (12-factor app methodology)
- Con: Requires users to set environment variable separately from config file

### Decision 2: Pydantic for Configuration Validation

**Context**: Configuration needs to be validated, typed, and provide clear error messages for missing or invalid values.

**Decision**: Use Pydantic models (`BaseModel` and `BaseSettings`) for configuration management.

**Consequences**:
- Pro: Type-safe configuration with IDE support
- Pro: Automatic validation with clear error messages
- Pro: Native support for environment variable loading
- Con: Additional dependency (though already needed for data models)

## Performance Considerations

- [Consideration 1]
- [Consideration 2]

## Security Considerations

- **API tokens stored in environment variables**: Never in config files or code
- **Config files gitignored**: `config/config.yaml` and `.env` are in `.gitignore`
- **Example files provided**: `.env.example` and `config.example.yaml` show format without real credentials
- **Pydantic validation**: Rejects malformed configuration before use

## Future Enhancements

- [ ] Enhancement 1
- [ ] Enhancement 2
- [ ] Enhancement 3
