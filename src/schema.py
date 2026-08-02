from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

# Every item has to land in one of these buckets. Anything the model invents
# outside the list fails validation, which is what we want.
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
    item_id: str
    category: Category
    date: Optional[str] = Field(default=None, description="YYYY-MM-DD, or null if absent")
    people: list[str] = Field(default_factory=list)
    location: Optional[str] = None
    amount: Optional[float] = Field(default=None, ge=0)
    currency: Optional[str] = None
    title: str
    summary: str
    action_required: bool = False
    action: Optional[str] = None
    priority: Priority = "medium"
    confidence: Confidence = "medium"
    source_excerpt: str

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value):
        # The model returns "usd" sometimes and "USD" others.
        return value.upper() if value else value


class JobOrganizationResult(BaseModel):
    project_name: Optional[str] = None
    client_name: Optional[str] = None
    property_address: Optional[str] = None
    items: list[JobItem]
    open_actions: list[str] = Field(default_factory=list)
    overall_summary: str
    warnings: list[str] = Field(default_factory=list)
    # Filled in after the call, not by the model. Which engine answered changes
    # how much you should trust the rest of this, so it travels with the result.
    provider: Optional[str] = None
