from __future__ import annotations

import re
from typing import Any


def _money(text: str) -> tuple[float | None, str | None]:
    patterns = [
        (r"\$\s*([\d,]+(?:\.\d{1,2})?)", "USD"),
        (r"€\s*([\d,]+(?:\.\d{1,2})?)", "EUR"),
        (r"£\s*([\d,]+(?:\.\d{1,2})?)", "GBP"),
        (r"([\d,]+(?:\.\d{1,2})?)\s*TND\b", "TND"),
    ]
    for pattern, currency in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return float(match.group(1).replace(",", "")), currency
    return None, None


def organize_without_ai(raw_text: str) -> dict[str, Any]:
    """Rule-based fallback used when no Groq key is available.

    It is intentionally basic. It lets the app and tests run, while clearly
    marking lower-confidence output.
    """
    lines = [line.strip(" -\t") for line in raw_text.splitlines() if line.strip()]
    project_name = None
    client_name = None
    property_address = None
    items: list[dict[str, Any]] = []
    actions: list[str] = []
    warnings = ["Demo mode was used; connect Groq for stronger extraction."]

    for line in lines:
        lower = line.lower()

        if lower.startswith("project:"):
            project_name = line.split(":", 1)[1].strip() or None
            continue
        if lower.startswith("client:"):
            client_name = line.split(":", 1)[1].strip() or None
            continue
        if lower.startswith("address:"):
            property_address = line.split(":", 1)[1].strip() or None
            continue

        category = "other"
        if "receipt" in lower or "$" in line or "€" in line or " tnd" in lower:
            category = "receipt"
        elif "photo" in lower or "image" in lower:
            category = "photo"
        elif "inspection" in lower:
            category = "inspection"
        elif "deliver" in lower or "arrived" in lower:
            category = "delivery"
        elif any(word in lower for word in ("schedule", "reschedule", "monday", "friday")):
            category = "schedule"
        elif any(word in lower for word in ("leak", "broken", "damaged", "scratch", "issue", "missing")):
            category = "issue"
        elif any(word in lower for word in ("paid", "payment", "invoice")):
            category = "payment"
        elif "client" in lower:
            category = "client_update"
        elif any(word in lower for word in ("crew", "foreman", "contractor")):
            category = "contractor_update"

        date_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", line)
        amount, currency = _money(line)

        needs_action = any(
            word in lower
            for word in (
                "broken", "damaged", "scratch", "leak", "missing", "reschedule",
                "confirm", "urgent", "approval", "late", "failed"
            )
        )
        action = f"Review and resolve: {line[:120]}" if needs_action else None
        if action:
            actions.append(action)

        items.append(
            {
                "item_id": f"item_{len(items)+1:03d}",
                "category": category,
                "date": date_match.group(1) if date_match else None,
                "people": [],
                "location": None,
                "amount": amount,
                "currency": currency,
                "title": line[:70],
                "summary": line,
                "action_required": needs_action,
                "action": action,
                "priority": "high" if needs_action else "medium",
                "confidence": "low",
                "source_excerpt": line[:180],
            }
        )

    if not items:
        warnings.append("No usable job items were found.")

    return {
        "project_name": project_name,
        "client_name": client_name,
        "property_address": property_address,
        "items": items,
        "open_actions": actions,
        "overall_summary": (
            f"Organized {len(items)} job update(s), with {len(actions)} open action(s)."
        ),
        "warnings": warnings,
    }
