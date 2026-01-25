"""Tests for YNAB Pydantic models."""

from datetime import date

from src.ynab.models import AccountSummary, BudgetSummary, Category, CategoryGroup, MonthDetail, TransactionDetail


def test_category_parses_valid_data() -> None:
    """Category should parse required fields."""
    category = Category(
        id="cat-1",
        category_group_id="group-1",
        name="Groceries",
        budgeted=12000,
        activity=-5000,
        balance=7000,
    )

    assert category.id == "cat-1"
    assert category.category_group_id == "group-1"
    assert category.name == "Groceries"
    assert category.budgeted == 12000
    assert category.activity == -5000
    assert category.balance == 7000


def test_category_optional_fields_default() -> None:
    """Optional fields should default to None when missing."""
    category = Category(
        id="cat-2",
        category_group_id="group-2",
        name="Dining",
        budgeted=5000,
        activity=-3000,
        balance=2000,
    )

    assert category.category_group_name is None


def test_category_amount_conversions() -> None:
    """Conversion helpers should return human-readable amounts."""
    category = Category(
        id="cat-3",
        category_group_id="group-3",
        name="Rent",
        budgeted=10500,
        activity=-2500,
        balance=8000,
    )

    assert category.budgeted_amount == 10.5
    assert category.activity_amount == -2.5
    assert category.balance_amount == 8.0
    assert category.spent_amount == 2.5


def test_category_group_default_categories_list() -> None:
    """CategoryGroup should default categories to an empty list."""
    group = CategoryGroup(id="group-1", name="Living")

    assert group.categories == []
    assert group.hidden is False


def test_month_detail_parses_full_payload() -> None:
    """MonthDetail should parse dates and nested categories."""
    month = MonthDetail(
        month="2024-02-01",
        income=150000,
        budgeted=120000,
        activity=-90000,
        to_be_budgeted=30000,
        categories=[
            {
                "id": "cat-4",
                "category_group_id": "group-4",
                "name": "Utilities",
                "budgeted": 40000,
                "activity": -35000,
                "balance": 5000,
            }
        ],
    )

    assert month.month == date(2024, 2, 1)
    assert len(month.categories) == 1
    assert month.categories[0].name == "Utilities"
    assert month.income_amount == 150.0
    assert month.to_be_budgeted_amount == 30.0


def test_json_serialization_round_trip() -> None:
    """Models should serialize and deserialize via JSON."""
    summary = BudgetSummary(
        id="budget-1",
        name="Household",
        last_modified_on="2024-02-10T12:00:00Z",
        currency_format={"iso_code": "USD", "decimal_digits": 2},
    )

    payload = summary.to_json()
    restored = BudgetSummary.model_validate_json(payload)

    assert restored == summary


def test_to_dict_returns_json_ready_payload() -> None:
    """to_dict should return JSON-friendly values."""
    month = MonthDetail(
        month=date(2024, 3, 1),
        income=1000,
        budgeted=800,
        activity=-200,
        to_be_budgeted=200,
    )

    payload = month.to_dict()

    assert payload["month"] == "2024-03-01"
    assert payload["income"] == 1000


def test_account_summary_parses_api_payload() -> None:
    """AccountSummary should parse API fields with type alias."""
    account = AccountSummary(
        id="acc-1",
        name="Checking",
        type="checking",
        on_budget=True,
        closed=False,
    )

    assert account.id == "acc-1"
    assert account.name == "Checking"
    assert account.account_type == "checking"
    assert account.on_budget is True


def test_transaction_detail_parses_payload() -> None:
    """TransactionDetail should parse core fields."""
    transaction = TransactionDetail(
        id="tx-1",
        date="2024-01-15",
        amount=-5000,
        payee_name="Grocery Store",
        memo="Weekly groceries",
        cleared="cleared",
        approved=True,
        category_name="Groceries",
        account_id="acc-1",
        account_name="Checking",
    )

    assert transaction.id == "tx-1"
    assert transaction.amount == -5000
    assert transaction.account_name == "Checking"
