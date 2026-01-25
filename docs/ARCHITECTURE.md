# Architecture Documentation

This document describes the technical architecture of YNAB Data Collector.

## Overview

YNAB Data Collector is a CLI application that connects to the YNAB (You Need A Budget) API to extract
budget data and export it to JSON. The application follows a modular architecture with clear separation
of concerns between configuration, API access, data modeling, and export.

## How It Works

1. The CLI loads configuration from `config/config.yaml` (if present) and environment variables.
2. `YnabClient` initializes an HTTP session with the YNAB API token.
3. The CLI calls YNAB endpoints to fetch budgets and current month data.
4. Responses are validated and parsed into Pydantic models.
5. The exporter transforms the models into a normalized JSON payload and writes it to disk.

## Component Diagram

```
┌─────────────────┐
│   CLI (main)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│     Config      │────▶│   YNAB Client   │
└─────────────────┘     └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │     Models      │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │    Exporters    │
                        └─────────────────┘
```

## Data Flow Diagram

```
CLI (click)
  │
  ├── load_config()
  │     └── YnabSettings (env)
  │
  ├── YnabClient.get_budgets()
  │     └── GET /budgets
  │
  ├── YnabClient.get_current_month()
  │     └── GET /budgets/{budget_id}/months/current
  │
  └── JsonExporter.export()
        └── output/<budget-name>-YYYY-MM-DD.json
```

## Dependency Diagram (Modules)

```
src/main.py
  ├── src/config.py
  ├── src/ynab/client.py
  │     └── src/ynab/models.py
  └── src/exporters/json_exporter.py
        └── src/ynab/models.py
```

## CLI Module

**Purpose**: Provide a user-friendly command-line interface for budget data extraction.

**Responsibilities**:
- Parse command-line arguments and options
- Coordinate configuration loading, API calls, and data export
- Display colored status output and error messages
- Exit with appropriate codes for failures

**Key Files**:
- `src/main.py`

**Commands**:
- `ynab-collector export` - Export current month budget data to JSON
- `ynab-collector budgets` - List available budgets
- `ynab-collector version` - Show version information

## Configuration Module

**Purpose**: Load and validate application settings from YAML files and environment variables.

**Key Files**:
- `src/config.py`

**Behavior**:
- Reads `config/config.yaml` if present
- Loads `YNAB_API_TOKEN` from environment variables
- Applies defaults for `base_url`, `budget_id`, and `output_directory`

## YNAB API Integration

**Purpose**: Communicate with the YNAB API and return validated models.

**Key Files**:
- `src/ynab/client.py`
- `src/ynab/exceptions.py`

**Endpoints Used**:
- `GET /budgets` - List budgets
- `GET /budgets/{budget_id}/accounts` - List accounts
- `GET /budgets/{budget_id}/months/current` - Fetch current month data

**Authentication**:
- Uses `Authorization: Bearer <token>` header
- Token is loaded from `YNAB_API_TOKEN`

**Error Mapping**:
- `401` → `YnabAuthError`
- `404` → `YnabNotFoundError`
- `429` → `YnabRateLimitError`
- `>= 400` → `YnabApiError`
- Network exceptions → `YnabNetworkError`
- Invalid JSON → `YnabResponseError`

## Data Models

**Purpose**: Represent YNAB API responses using typed, validated Pydantic models.

**Key Files**:
- `src/ynab/models.py`

**Highlights**:
- Parses YNAB API payloads into `AccountSummary`, `BudgetSummary`, `MonthDetail`, and `Category` models
- Provides milliunit-to-unit conversion helpers
- Ignores extra fields from the API to remain forward compatible

## Exporters

**Purpose**: Export budget data to various file formats.

**Key Files**:
- `src/exporters/json_exporter.py`

**Current Export Format**:
- JSON file with `metadata`, `summary`, and `categories`
- Pretty-printed output by default
- Creates parent directories when needed

## Error Handling Strategy

- The CLI catches configuration, API, and export errors and exits with code `1`.
- API errors are converted to domain-specific exceptions in `YnabClient`.
- The CLI uses consistent, user-friendly error messages for common failures.

## Performance Considerations

- Uses a `requests.Session` to reuse connections across API calls.
- Export path computation and JSON serialization are in-memory and linear to data size.
- The export workflow makes two API calls per run (`/budgets` and `/months/current`).

## Security Considerations

- API tokens are only loaded from environment variables (never from config files).
- Sensitive configuration files (`config/config.yaml`, `.env`) are gitignored.
- Error messages avoid printing secrets.

## Future Enhancements

- Support exporting historical months and date ranges
- Add CSV export support
- Add optional caching for budgets and category metadata
- Add structured logging and optional debug traces
