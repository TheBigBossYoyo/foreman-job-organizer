"""The structured-output contract — the single source of truth.

Ported from the PHP app's Schema.php: a richer taxonomy than a plain
categorizer, a trade-phase vocabulary, and an explicit set of review flags so
downstream code (guardrails, UI, scorer) all agree on the shape.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

Category = Literal[
    "progress_update",
    "material_purchase",
    "delivery",
    "labor_log",
    "schedule_change",
    "inspection",
    "issue_or_delay",
    "safety_incident",
    "change_order",
    "client_communication",
    "permit_or_compliance",
    "photo_documentation",
    "other",
]

# Human labels + an emoji, mirroring the web app's chips.
CATEGORY_LABELS: dict[str, str] = {
    "progress_update": "🏗️ Progress Update",
    "material_purchase": "🧾 Material Purchase",
    "delivery": "🚚 Delivery",
    "labor_log": "⏱️ Labor / Time Log",
    "schedule_change": "📅 Schedule Change",
    "inspection": "✅ Inspection",
    "issue_or_delay": "⚠️ Issue / Delay",
    "safety_incident": "🦺 Safety Incident",
    "change_order": "📝 Change Order",
    "client_communication": "💬 Client Communication",
    "permit_or_compliance": "📋 Permit / Compliance",
    "photo_documentation": "📷 Photo Documentation",
    "other": "📦 Other",
}

PHASES = [
    "site_prep", "demolition", "foundation", "framing", "roofing", "plumbing",
    "electrical", "hvac", "insulation", "drywall", "painting", "flooring",
    "cabinetry", "landscaping", "inspection", "cleanup", "general",
]

# Flags that mean "a human should look at this before trusting it".
REVIEW_FLAGS = {
    "safety_review", "missing_amount", "low_confidence",
    "possible_pii", "needs_human", "date_unverified",
}

Flag = Literal[
    "safety_review", "missing_amount", "low_confidence",
    "possible_pii", "needs_human", "date_unverified",
]


class JobItem(BaseModel):
    category: Category = "other"
    category_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    title: str = ""
    summary: str = ""
    occurred_at: Optional[str] = Field(default=None, description="YYYY-MM-DD or null")
    vendor: Optional[str] = None
    amount: Optional[float] = Field(default=None, ge=0)
    currency: Optional[str] = "USD"
    materials: list[str] = Field(default_factory=list)
    labor_hours: Optional[float] = Field(default=None, ge=0)
    phase: Optional[str] = None
    location: Optional[str] = None
    people: list[str] = Field(default_factory=list)
    follow_up_actions: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    flags: list[Flag] = Field(default_factory=list)
    compliance_notes: Optional[str] = None
    source_excerpt: str = ""

    @field_validator("currency")
    @classmethod
    def _upper_currency(cls, v):
        return v.upper() if v else v

    def needs_review(self) -> bool:
        return bool(REVIEW_FLAGS.intersection(self.flags))


class JobResult(BaseModel):
    project_name: Optional[str] = None
    client_name: Optional[str] = None
    property_address: Optional[str] = None
    items: list[JobItem] = Field(default_factory=list)
    open_actions: list[str] = Field(default_factory=list)
    overall_summary: str = ""
    warnings: list[str] = Field(default_factory=list)
