"""Construction-industry guardrails, enforced in code (not just the prompt).

Belt-and-suspenders: even a perfectly-worded prompt can be ignored, so we
re-check safety language, never-invent-money, PII and date-grounding here.
Ported from the PHP app's Compliance.php.
"""
from __future__ import annotations

import re

from .dates import date_is_grounded
from .schema import JobItem

SAFETY_WORDS = [
    "injur", "hurt", "accident", "near miss", "osha", "hospital",
    "first aid", "urgent care", "bleeding", "fell off", "shock",
]
PII_RE = re.compile(r"\b(\d{3}[-.\s]\d{3}[-.\s]\d{4}|\d{3}-\d{2}-\d{4}|\d{13,16})\b")

CAN_DO = [
    "Read messy job notes, photo captions, receipts and schedules.",
    "Categorize each item and extract the schema fields.",
    "Copy amounts, dates, quantities and names exactly as written.",
    "Build a chronological timeline and a plain-language job summary.",
    "Flag items that need a human (safety, permits, money without a source).",
]
CANNOT_DO = [
    "Invent, estimate or round money, quantities or dates — return null and flag it.",
    "Give legal, structural-engineering or code-compliance rulings.",
    "Approve payments, sign documents or authorize change orders.",
    "Diagnose OSHA violations authoritatively — flag safety items for review.",
    "Expose personal data (phone, SSN, card numbers) in summaries.",
]


def enforce(item: JobItem, source_text: str) -> JobItem:
    """Apply the hard rules to an item and return it adjusted."""
    lower = source_text.lower()
    flags = set(item.flags)

    # 1) safety language forces a safety flag regardless of category
    if any(w in lower for w in SAFETY_WORDS):
        if item.category in ("other", "progress_update"):
            item.category = "safety_incident"
        flags.add("safety_review")
        item.compliance_notes = item.compliance_notes or (
            "Safety-related language detected. Requires human OSHA/insurance "
            "review before action."
        )

    # 2) money category with no amount -> missing_amount (never fabricate)
    if item.category in ("material_purchase", "change_order") and item.amount is None:
        flags.add("missing_amount")

    # 3) low confidence -> flag for human
    if item.category_confidence < 0.45:
        flags.add("low_confidence")

    # 4) PII scrub in the summary (defense in depth)
    if PII_RE.search(source_text):
        flags.add("possible_pii")
        item.summary = PII_RE.sub("[redacted]", item.summary)

    item.flags = sorted(flags)
    return ground_date(item, source_text)


def ground_date(item: JobItem, source_text: str) -> JobItem:
    """Drop a date that is not written in the item's own text."""
    if item.occurred_at and source_text.strip() and not date_is_grounded(item.occurred_at, source_text):
        dropped = item.occurred_at
        item.occurred_at = None
        flags = set(item.flags)
        flags.add("date_unverified")
        item.flags = sorted(flags)
        item.compliance_notes = item.compliance_notes or (
            f"Dropped a date ({dropped}) not written in this item — most likely "
            f"copied from another line or invented. Verify before use."
        )
    return item
