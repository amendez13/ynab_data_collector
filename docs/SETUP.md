# Setup Guide

This guide walks you through setting up YNAB Data Collector for development or usage.

## Prerequisites

- Python 3.10 or higher
- pip (Python package installer)
- git

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/amendez13/ynab_data_collector.git
cd ynab_data_collector
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows
```

### 3. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

## YNAB API Token Setup

1. Open the YNAB developer settings page:
   - https://app.ynab.com/settings/developer
2. Create a Personal Access Token.
3. Export it as an environment variable:

```bash
export YNAB_API_TOKEN="your_token_here"
```

You can also store this in a `.env` file (see `.env.example`) if you prefer not to export it every session.

## Configure the Application

Copy the example config and adjust as needed:

```bash
cp config/config.example.yaml config/config.yaml
```

The application only reads the following keys:

```yaml
ynab:
  base_url: "https://api.ynab.com/v1"
  budget_id: "last-used"

output_directory: "./output"
```

If `config/config.yaml` is missing, defaults are used and the CLI still runs as long as `YNAB_API_TOKEN` is set.

## Verify Installation

```bash
# Show CLI help
python -m src.main --help

# List budgets (verifies API access)
python -m src.main budgets

# List accounts
python -m src.main accounts
```

## Development Setup

### Install Pre-commit Hooks

```bash
pre-commit install
pre-commit run --all-files
```

### IDE Setup

#### VS Code

Recommended extensions:
- Python
- Pylance
- Black Formatter
- isort

Settings (`.vscode/settings.json`):

```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

#### PyCharm

1. Set Python interpreter to `./venv/bin/python`
2. Enable Black formatter
3. Enable isort for imports

## Troubleshooting

**Virtual environment not activated**

```bash
source venv/bin/activate
```

**Dependencies not installed**

```bash
pip install -r requirements.txt
```

**Configuration file not found**

```bash
cp config/config.example.yaml config/config.yaml
```

**Missing API token**

```bash
export YNAB_API_TOKEN="your_token_here"
```

## Getting Help

- Review `docs/INDEX.md`
- See `docs/USAGE.md` for CLI examples
- Check `docs/CI.md` for test automation details
