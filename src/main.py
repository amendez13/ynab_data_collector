"""CLI interface for YNAB Data Collector."""

from __future__ import annotations

import sys
from datetime import datetime
from typing import TYPE_CHECKING, Optional

import click

from src.config import Config, ConfigError, load_config
from src.exporters import JsonExporter
from src.exporters.json_exporter import ExportError
from src.ynab.client import YnabClient
from src.ynab.exceptions import YnabApiError, YnabAuthError, YnabNotFoundError
from src.ynab.models import AccountSummary, BudgetSummary, MonthDetail

if TYPE_CHECKING:
    from pathlib import Path

__version__ = "0.1.0"


class Context:
    """CLI context object for sharing state between commands."""

    def __init__(self, config_path: str, verbose: bool, quiet: bool, no_color: bool) -> None:
        self.config_path = config_path
        self.verbose = verbose
        self.quiet = quiet
        self.no_color = no_color
        self._config: Optional[Config] = None
        self._client: Optional[YnabClient] = None

    @property
    def config(self) -> Config:
        """Lazy-load configuration."""
        if self._config is None:
            self._config = load_config(self.config_path)
        return self._config

    @property
    def client(self) -> YnabClient:
        """Lazy-load YNAB client."""
        if self._client is None:
            self._client = YnabClient(
                api_token=self.config.ynab.api_token,
                base_url=self.config.ynab.base_url,
            )
        return self._client

    def echo(self, message: str, fg: Optional[str] = None, err: bool = False) -> None:
        """Print a message, respecting quiet and color settings."""
        if self.quiet:
            return
        if self.no_color:
            click.echo(message, err=err)
        else:
            click.secho(message, fg=fg, err=err)

    def echo_success(self, message: str) -> None:
        """Print a success message in green."""
        self.echo(message, fg="green")

    def echo_error(self, message: str) -> None:
        """Print an error message in red to stderr."""
        self.echo(message, fg="red", err=True)

    def echo_info(self, message: str) -> None:
        """Print an info message in blue."""
        self.echo(message, fg="blue")

    def echo_verbose(self, message: str) -> None:
        """Print a verbose message in dim text."""
        if self.verbose and not self.quiet:
            self.echo(message, fg="bright_black")


pass_context = click.make_pass_decorator(Context)


@click.group()
@click.version_option(version=__version__, prog_name="ynab-collector")
@click.option(
    "--config",
    "-c",
    "config_path",
    type=click.Path(exists=False),
    default="config/config.yaml",
    help="Path to configuration file.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Enable verbose output.",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    default=False,
    help="Suppress all output except errors.",
)
@click.option(
    "--no-color",
    is_flag=True,
    default=False,
    help="Disable colored output.",
)
@click.pass_context
def cli(
    ctx: click.Context,
    config_path: str,
    verbose: bool,
    quiet: bool,
    no_color: bool,
) -> None:
    """YNAB Data Collector - Export your budget data."""
    ctx.obj = Context(config_path, verbose, quiet, no_color)


def _load_config_or_exit(ctx: Context) -> Config:
    """Load configuration or exit with error."""
    try:
        config = ctx.config
        ctx.echo_verbose(f"Loaded configuration from: {ctx.config_path}")
        return config
    except ConfigError as e:
        ctx.echo_error(f"Configuration error: {e}")
        sys.exit(1)


def _fetch_budgets_or_exit(ctx: Context) -> list[BudgetSummary]:
    """Fetch budgets from API or exit with error."""
    try:
        return ctx.client.get_budgets()
    except YnabAuthError:
        ctx.echo_error("Authentication failed. Check your YNAB_API_TOKEN.")
        sys.exit(1)
    except YnabApiError as e:
        ctx.echo_error(f"YNAB API error: {e}")
        sys.exit(1)


def _fetch_month_data_or_exit(ctx: Context, budget_id: str) -> MonthDetail:
    """Fetch month data from API or exit with error."""
    try:
        return ctx.client.get_current_month(budget_id)
    except YnabAuthError:
        ctx.echo_error("Authentication failed. Check your YNAB_API_TOKEN.")
        sys.exit(1)
    except YnabNotFoundError:
        ctx.echo_error(f"Budget not found: {budget_id}")
        sys.exit(1)
    except YnabApiError as e:
        ctx.echo_error(f"YNAB API error: {e}")
        sys.exit(1)


def _fetch_accounts_or_exit(ctx: Context, budget_id: str) -> list[AccountSummary]:
    """Fetch accounts from API or exit with error."""
    try:
        return ctx.client.get_accounts(budget_id)
    except YnabAuthError:
        ctx.echo_error("Authentication failed. Check your YNAB_API_TOKEN.")
        sys.exit(1)
    except YnabApiError as e:
        ctx.echo_error(f"YNAB API error: {e}")
        sys.exit(1)


def _resolve_budget_name(budget_id: str, budgets: list[BudgetSummary]) -> str:
    """Resolve budget name from ID or return default."""
    if budget_id == "last-used" and budgets:
        return budgets[0].name
    for b in budgets:
        if b.id == budget_id:
            return b.name
    return "Unknown Budget"


def _build_output_path(budget_name: str, output_directory: Path) -> str:
    """Build default output path for export."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    safe_name = budget_name.replace(" ", "_").lower()
    return str(output_directory / f"{safe_name}-{date_str}.json")


def _display_budget(budget: BudgetSummary, no_color: bool) -> None:
    """Display a single budget entry."""
    if no_color:
        click.echo(f"  {budget.name}")
        click.echo(f"    ID: {budget.id}")
    else:
        click.secho(f"  {budget.name}", fg="cyan", bold=True)
        click.secho(f"    ID: {budget.id}", fg="bright_black")
    if budget.last_modified_on:
        modified = budget.last_modified_on[:10]
        if no_color:
            click.echo(f"    Last modified: {modified}")
        else:
            click.secho(f"    Last modified: {modified}", fg="bright_black")
    click.echo()


def _display_account(account: AccountSummary, no_color: bool) -> None:
    """Display a single account entry."""
    status = "on budget" if account.on_budget else "off budget"
    if account.closed:
        status = f"{status}, closed"
    if no_color:
        click.echo(f"  {account.name}")
        click.echo(f"    ID: {account.id}")
        click.echo(f"    Type: {account.account_type}")
        click.echo(f"    Status: {status}")
    else:
        click.secho(f"  {account.name}", fg="cyan", bold=True)
        click.secho(f"    ID: {account.id}", fg="bright_black")
        click.secho(f"    Type: {account.account_type}", fg="bright_black")
        click.secho(f"    Status: {status}", fg="bright_black")
    click.echo()


@cli.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output file path. Defaults to output/<budget>-<date>.json",
)
@click.option(
    "--budget-id",
    "-b",
    default=None,
    help="Budget ID to export. Defaults to 'last-used'.",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["json"], case_sensitive=False),
    default="json",
    help="Output format (currently only json is supported).",
)
@pass_context
def export(
    ctx: Context,
    output: Optional[str],
    budget_id: Optional[str],
    output_format: str,  # noqa: ARG001 - reserved for future format support
) -> None:
    """Export current month budget data."""
    ctx.echo_info("Starting budget export...")

    config = _load_config_or_exit(ctx)
    budget_id = budget_id or config.ynab.budget_id

    ctx.echo_verbose("Fetching budgets from YNAB API...")
    budgets = _fetch_budgets_or_exit(ctx)
    ctx.echo_verbose(f"Found {len(budgets)} budget(s)")

    budget_name = _resolve_budget_name(budget_id, budgets)
    ctx.echo_verbose(f"Fetching current month data for budget: {budget_name}")
    month_data = _fetch_month_data_or_exit(ctx, budget_id)

    if output is None:
        output = _build_output_path(budget_name, config.output_directory)

    ctx.echo_verbose(f"Exporting to: {output}")

    try:
        exporter = JsonExporter(pretty=True)
        output_path = exporter.export(month_data, budget_name, output)
        ctx.echo_success(f"Budget exported to: {output_path}")
    except ExportError as e:
        ctx.echo_error(f"Export failed: {e}")
        sys.exit(1)


@cli.command()
@pass_context
def budgets(ctx: Context) -> None:
    """List available budgets."""
    ctx.echo_info("Fetching budgets...")
    _load_config_or_exit(ctx)

    budget_list = _fetch_budgets_or_exit(ctx)

    if not budget_list:
        ctx.echo("No budgets found.")
        return

    ctx.echo_success(f"Found {len(budget_list)} budget(s):\n")

    for budget in budget_list:
        _display_budget(budget, ctx.no_color)


@cli.command()
@pass_context
def accounts(ctx: Context) -> None:
    """List available accounts for the configured budget."""
    ctx.echo_info("Fetching accounts...")
    config = _load_config_or_exit(ctx)

    accounts_list = _fetch_accounts_or_exit(ctx, config.ynab.budget_id)

    if not accounts_list:
        ctx.echo("No accounts found.")
        return

    ctx.echo_success(f"Found {len(accounts_list)} account(s):\n")

    for account in accounts_list:
        _display_account(account, ctx.no_color)


@cli.command()
def version() -> None:
    """Show version information."""
    click.echo(f"ynab-collector version {__version__}")


def main() -> None:  # pragma: no cover
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
