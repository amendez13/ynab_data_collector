# Usage Guide

This guide covers how to run YNAB Data Collector and how to use the current Python APIs.

## CLI Usage (Current)

The CLI entry point is minimal at the moment and prints a greeting. It will be expanded as more features are added.

```bash
python -m src.main
```

## Configuration

The YNAB API token is loaded from the `YNAB_API_TOKEN` environment variable. Other settings live in `config/config.yaml`.

```bash
# macOS/Linux
export YNAB_API_TOKEN="your-token"

# Windows (PowerShell)
$env:YNAB_API_TOKEN="your-token"
```

```yaml
# config/config.yaml
ynab:
  base_url: "https://api.ynab.com/v1"
  budget_id: "last-used"

output_directory: "./output"
```

## Using the YNAB Client

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

print(budgets[0].name)
print(current_month.month)
```

## Error Handling

The client raises custom exceptions for common API failure cases.

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

## Next Steps

- Review `docs/ARCHITECTURE.md` for implementation details.
- See `docs/SETUP.md` if you need to configure your environment.
