"""Prompt templates: state the task, inject the schema, show a worked example,
demand JSON-only. Ported from the PHP app's Templates.php.
"""
from __future__ import annotations

import json

from .guardrails import CAN_DO, CANNOT_DO
from .schema import Category, PHASES

CATEGORIES = list(Category.__args__)  # type: ignore[attr-defined]

SYSTEM_PROMPT = (
    "You are the Job Organizer, an assistant for construction contractors. You "
    "read one messy job-site item (a note, photo caption, receipt, schedule "
    "change or text update) and return a single clean JSON object describing it.\n\n"
    "WHAT YOU CAN DO:\n- " + "\n- ".join(CAN_DO) + "\n\n"
    "WHAT YOU MUST NOT DO:\n- " + "\n- ".join(CANNOT_DO) + "\n\n"
    "Return ONLY a valid JSON object. No markdown, no code fences, no commentary."
)

_EXAMPLE = {
    "category": "material_purchase",
    "category_confidence": 0.97,
    "title": "Drywall & screws from Home Depot",
    "summary": 'Purchased 40 sheets of 5/8" drywall and 5 boxes of screws for $842.19.',
    "occurred_at": None,
    "vendor": "Home Depot",
    "amount": 842.19,
    "currency": "USD",
    "materials": ['5/8" drywall', "drywall screws"],
    "labor_hours": None,
    "phase": "drywall",
    "location": None,
    "people": ["Mike"],
    "follow_up_actions": [],
    "tags": ["drywall", "receipt"],
    "flags": [],
    "compliance_notes": None,
    "source_excerpt": "picked up 40 sheets 5/8\" drywall and 5 boxes screws, total $842.19",
}


def build_user_prompt(item_text: str) -> str:
    schema_keys = ", ".join(JobItemKeys())
    return (
        f"Categorize and extract structured data from ONE job item.\n\n"
        f"Allowed categories: {', '.join(CATEGORIES)}\n"
        f"Allowed phases: {', '.join(PHASES)}\n"
        f"Required JSON keys: {schema_keys}\n\n"
        "Rules:\n"
        "- Copy amounts, dates, quantities and names EXACTLY. Never invent them.\n"
        "- If money is implied but no number is given, set amount=null and add "
        '"missing_amount" to flags.\n'
        "- occurred_at must be YYYY-MM-DD or null, and only if the date is written "
        "for THIS item (never inherited from another line).\n"
        '- For any injury/unsafe condition: category="safety_incident" and add '
        '"safety_review" to flags.\n'
        '- For phone/card/SSN numbers, do not repeat them; add "possible_pii".\n\n'
        "WORKED EXAMPLE\n"
        'ITEM: """Home Depot 6/14 - picked up 40 sheets 5/8" drywall and 5 boxes '
        'screws, total $842.19. Mike grabbed it."""\n'
        f"JSON: {json.dumps(_EXAMPLE, ensure_ascii=False)}\n\n"
        "Now do the same for this item. Return ONLY the JSON object:\n"
        f'ITEM:\n"""\n{item_text}\n"""'
    )


def JobItemKeys() -> list[str]:
    from .schema import JobItem
    return list(JobItem.model_fields.keys())
