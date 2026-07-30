from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


Category = Literal[
    "photo",
    "receipt",
    "client_update",
    "contractor_update",
    "inspection",
    "delivery",
    "schedule",
    "issue",
    "payment",
    "other",
]

Priority = Literal["low", "medium", "high", "urgent"]
Confidence = Literal["low", "medium", "high"]


class JobItem(BaseModel):
    item_id: str = Field(description="Stable short identifier such as item_001")
    category: Category
    date: Optional[str] = Field(
        default=None,
        description="ISO date YYYY-MM-DD, or null when absent/uncertain",
    )
    people: list[str] = Field(default_factory=list)
    location: Optional[str] = None
    amount: Optional[float] = Field(default=None, ge=0)
    currency: Optional[str] = Field(
        default=None,
        description="Three-letter currency code such as USD, EUR, GBP",
    )
    title: str
    summary: str
    action_required: bool = False
    action: Optional[str] = None
    priority: Priority = "medium"
    confidence: Confidence = "medium"
    source_excerpt: str = Field(
        description="Short excerpt from the original input supporting this item"
    )

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: Optional[str]) -> Optional[str]:
        return value.upper() if value else value


class JobOrganizationResult(BaseModel):
    project_name: Optional[str] = None
    client_name: Optional[str] = None
    property_address: Optional[str] = None
    items: list[JobItem]
    open_actions: list[str] = Field(default_factory=list)
    overall_summary: str
    warnings: list[str] = Field(default_factory=list)
