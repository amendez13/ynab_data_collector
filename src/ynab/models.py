"""Pydantic models for YNAB API data structures."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class YnabBaseModel(BaseModel):
    """Base model with shared serialization helpers."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    def to_dict(self, **kwargs: Any) -> dict[str, Any]:
        """Return a JSON-serializable dict representation."""
        return self.model_dump(mode="json", **kwargs)

    def to_json(self, **kwargs: Any) -> str:
        """Return a JSON string representation."""
        return self.model_dump_json(**kwargs)

    @staticmethod
    def milliunit_to_unit(value: int) -> float:
        """Convert milliunits to a human-readable amount."""
        return value / 1000


class Category(YnabBaseModel):
    """Individual budget category."""

    id: str
    category_group_id: str
    category_group_name: str | None = None
    name: str
    budgeted: int = Field(description="Budgeted amount in milliunits")
    activity: int = Field(description="Activity amount in milliunits")
    balance: int = Field(description="Balance amount in milliunits")

    @property
    def budgeted_amount(self) -> float:
        """Human-readable budgeted amount."""
        return self.milliunit_to_unit(self.budgeted)

    @property
    def activity_amount(self) -> float:
        """Human-readable activity amount (can be negative)."""
        return self.milliunit_to_unit(self.activity)

    @property
    def balance_amount(self) -> float:
        """Human-readable balance amount."""
        return self.milliunit_to_unit(self.balance)

    @property
    def spent_amount(self) -> float:
        """Positive spent amount derived from activity."""
        return abs(self.activity) / 1000


class CategoryGroup(YnabBaseModel):
    """Budget category group."""

    id: str
    name: str
    hidden: bool = False
    categories: list[Category] = Field(default_factory=list)


class MonthDetail(YnabBaseModel):
    """Monthly budget summary."""

    month: date
    income: int = Field(description="Income in milliunits")
    budgeted: int = Field(description="Budgeted in milliunits")
    activity: int = Field(description="Activity in milliunits")
    to_be_budgeted: int = Field(description="To be budgeted in milliunits")
    categories: list[Category] = Field(default_factory=list)

    @property
    def income_amount(self) -> float:
        """Human-readable income amount."""
        return self.milliunit_to_unit(self.income)

    @property
    def budgeted_amount(self) -> float:
        """Human-readable budgeted amount."""
        return self.milliunit_to_unit(self.budgeted)

    @property
    def activity_amount(self) -> float:
        """Human-readable activity amount."""
        return self.milliunit_to_unit(self.activity)

    @property
    def to_be_budgeted_amount(self) -> float:
        """Human-readable to-be-budgeted amount."""
        return self.milliunit_to_unit(self.to_be_budgeted)


class BudgetSummary(YnabBaseModel):
    """Budget metadata."""

    id: str
    name: str
    last_modified_on: str | None = None
    currency_format: dict[str, Any] | None = None


class AccountSummary(YnabBaseModel):
    """Account metadata."""

    id: str
    name: str
    account_type: str = Field(alias="type")
    on_budget: bool = True
    closed: bool = False
    deleted: bool = False
