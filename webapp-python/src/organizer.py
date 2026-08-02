"""Core pipeline: raw text -> items -> validate -> guardrails.

One item is: build prompt -> call the provider -> slice out JSON -> validate
against the schema -> enforce guardrails (safety/money/PII/date-grounding).
A whole stream is split into items and each is processed. Mirrors the PHP app's
InferenceEngine.
"""
from __future__ import annotations

import json
import re

from pydantic import ValidationError

from . import guardrails, prompts, providers
from .schema import JobItem


class OrganizerError(RuntimeError):
    """Raised when a model reply can't be parsed or trusted."""


def split_items(stream: str) -> list[str]:
    """Split a pasted stream into individual items (blank-line or new-entry)."""
    text = stream.strip()
    if not text:
        return []
    if re.search(r"\n\s*\n", text):
        parts = re.split(r"\n\s*\n", text)
    else:
        parts = re.split(r"\n(?=\s*(?:[-*•]\s+|\d{1,2}[/\-.]\d{1,2}))", text)
    return [re.sub(r"^\s*[-*•]\s+", "", p).strip() for p in parts if p.strip()]


def _extract_json_object(text: str) -> dict:
    first, last = text.find("{"), text.rfind("}")
    if first == -1 or last == -1 or first >= last:
        raise OrganizerError("Model reply contained no JSON object.")
    try:
        parsed = json.loads(text[first:last + 1])
    except json.JSONDecodeError as exc:
        raise OrganizerError(f"Invalid JSON from model: {exc}")
    if not isinstance(parsed, dict):
        raise OrganizerError("Model returned JSON, but not an object.")
    return parsed


def organize_item(item_text: str) -> JobItem:
    """Turn one raw item into a validated, guardrail-checked JobItem."""
    if not item_text.strip():
        raise ValueError("Item text cannot be empty.")

    raw = providers.complete(prompts.SYSTEM_PROMPT, prompts.build_user_prompt(item_text), item_text)
    parsed = _extract_json_object(raw)
    parsed.setdefault("source_excerpt", item_text[:180])
    try:
        item = JobItem.model_validate(parsed)
    except ValidationError as exc:
        raise OrganizerError(f"Output validation failed:\n{exc}")
    return guardrails.enforce(item, item_text)


def organize_stream(stream: str) -> list[JobItem]:
    """Organize a whole pasted stream into a list of items."""
    items: list[JobItem] = []
    for raw in split_items(stream):
        try:
            items.append(organize_item(raw))
        except (OrganizerError, ValueError):
            continue
    return items
