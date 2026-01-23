# Usage Guide

This guide covers how to run YNAB Data Collector and how to use the Python APIs.

## CLI Reference

The CLI is available as `ynab-collector` (from `pyproject.toml` scripts) or `python -m src.main`.

### Export Budget Data

Export the current month's budget data to JSON:

```bash
ynab-collector export [OPTIONS]
```

**Options**
- `-o, --output PATH` - Output file path. Defaults to `<output_directory>/<budget-name>-YYYY-MM-DD.json`.
- `-b, --budget-id ID` - Budget ID to export. Defaults to `ynab.budget_id` from config (or `last-used`).
- `-f, --format [json]` - Output format (currently only `json`).

Examples:

```bash
# Export default budget to default location
ynab-collector export

# Export with custom output path
ynab-collector export --output ./my-budget.json

# Export specific budget
ynab-collector export --budget-id abc123-def456
```

### List Available Budgets

```bash
ynab-collector budgets
```

This command displays budget names and IDs for use with `--budget-id`.

### Show Version

```bash
ynab-collector version
# or
ynab-collector --version
```

### Global Options

These options apply to any command:

- `-c, --config PATH` - Config file path (default: `config/config.yaml`)
- `-v, --verbose` - Enable verbose output
- `-q, --quiet` - Suppress non-error output
- `--no-color` - Disable colored output

Examples:

```bash
# Use a custom config file
ynab-collector -c ./config/custom.yaml export

# Enable verbose logging
ynab-collector -v export
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `YNAB_API_TOKEN` | Yes | YNAB Personal Access Token (always loaded from env) |

```bash
# macOS/Linux
export YNAB_API_TOKEN="your-token"

# Windows (PowerShell)
$env:YNAB_API_TOKEN="your-token"
```

### Config File

`config/config.yaml` is optional. If it does not exist, defaults are used.

```yaml
ynab:
  base_url: "https://api.ynab.com/v1"
  budget_id: "last-used"

output_directory: "./output"
```

### Output Path Defaults

If `--output` is not provided, the CLI writes to:

```
<output_directory>/<budget-name>-YYYY-MM-DD.json
```

`budget-name` is derived from the budget name with spaces replaced by underscores and lowercased.

## Output Format

The JSON export includes metadata, summary totals, and categories:

```json
{
  "metadata": {
    "exported_at": "2024-01-15T12:00:00+00:00",
    "source": "YNAB API",
    "budget_name": "My Budget",
    "month": "2024-01"
  },
  "summary": {
    "total_budgeted": 2800.0,
    "total_spent": 2650.5,
    "total_available": 149.5
  },
  "categories": [
    {
      "group": "Monthly Bills",
      "name": "Rent",
      "budgeted": 1500.0,
      "spent": 1500.0,
      "available": 0.0
    }
  ]
}
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (configuration, API, or export failure) |

## Using the YNAB Client (Python)

```python
from src.config import load_config
from src.ynab import YnabClient

config = load_config()
client = YnabClient(
    api_token=config.ynab.api_token,
    base_url=config.ynab.base_url,
)

budgets = client.get_budgets()
current_month = client.get_current_month(config.ynab.budget_id)
```

## Using the JSON Exporter (Python)

```python
from src.exporters import JsonExporter

exporter = JsonExporter(pretty=True)
output_path = exporter.export(current_month, budgets[0].name, "output/budget.json")
print(f"Exported to: {output_path}")
```

## Error Handling

The client raises custom exceptions for common API failure cases:

```python
from src.ynab import (
    YnabAuthError,
    YnabNotFoundError,
    YnabRateLimitError,
    YnabNetworkError,
    YnabResponseError,
)

try:
    client.get_budgets()
except YnabAuthError:
    print("Invalid API token")
except YnabRateLimitError:
    print("Rate limit exceeded")
except YnabNotFoundError:
    print("Budget not found")
except YnabNetworkError:
    print("Network error")
except YnabResponseError:
    print("Invalid JSON payload")
```
