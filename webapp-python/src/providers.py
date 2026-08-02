"""Provider abstraction: Anthropic Claude (default) + a rule-based local fallback.

Mirrors the PHP app's ModelFactory/BaseLLM/LocalLLM. When no ANTHROPIC_API_KEY
is set, the local rule-based provider returns the SAME JSON contract so the app
still works offline (demo mode). Quality is lower — that gap is what the scorer
measures.
"""
from __future__ import annotations

import json
import os
import re

from .schema import PHASES

DEFAULT_MODEL = "claude-haiku-4-5-20251001"

VENDORS = [
    "Home Depot", "Lowes", "Lowe's", "Sherwin Williams", "Ferguson",
    "ABC Supply", "Ace Hardware", "Menards", "84 Lumber",
]
MATERIALS = [
    "drywall", "lumber", "plywood", "paint", "concrete", "rebar", "insulation",
    "tile", "shingles", "pvc", "copper", "screws", "nails", "studs", "cabinets",
    "flooring", "grout", "wire",
]
KEYWORD_RULES = [
    ("safety_incident", ["injur", "cut his", "cut her", "hurt", "accident", "near miss", "urgent care", "hospital", "first aid"]),
    ("inspection", ["inspection", "inspector", "passed", "signed the card"]),
    ("permit_or_compliance", ["permit", "code compliance", "variance", "zoning", "lien"]),
    ("change_order", ["change order", "wants to add", "upgrade to", "extra cost", "add a"]),
    ("delivery", ["delivery", "delivered", "dropped off", "arrived", "dumpster"]),
    ("material_purchase", ["receipt", "bought", "purchased", "picked up", "invoice for", "home depot", "lowes", "84 lumber"]),
    ("schedule_change", ["reschedul", "pushing", "moving", "delayed to", "postpon", "rain", "move to"]),
    ("labor_log", ["labor hours", "crew of", "on site", "worked", "hrs", "hours", "timesheet"]),
    ("client_communication", ["client", "homeowner", "owner", "texted", "emailed", "called"]),
    ("photo_documentation", ["photo", "picture", "pic of", "before pictures", "after pictures"]),
    ("issue_or_delay", ["problem", "issue", "rot", "leak", "mistake", "delay", "behind schedule", "water damage"]),
]


def active_provider() -> str:
    """'claude' when a key is present, else the local rule-based fallback."""
    forced = os.getenv("AI_PROVIDER", "").strip().lower()
    if forced in ("claude", "local"):
        return "claude" if (forced == "claude" and os.getenv("ANTHROPIC_API_KEY")) else "local"
    return "claude" if os.getenv("ANTHROPIC_API_KEY") else "local"


def complete(system: str, user: str, item_text: str) -> str:
    """Return a raw JSON string for one item from the active provider."""
    if active_provider() == "claude":
        return _complete_claude(system, user)
    return _complete_local(item_text)


def _complete_claude(system: str, user: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    model = os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)
    resp = client.messages.create(
        model=model,
        max_tokens=1200,
        temperature=0,  # reproducible output, so the accuracy number is stable
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")


# --- local rule-based fallback (no API) ---------------------------------------

def _parse_amount(s: str):
    m = re.search(r"\$\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)", s)
    if m:
        return float(m.group(1).replace(",", ""))
    m = re.search(r"(?<![/:\d])([0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]{1,2})?|[0-9]+\.[0-9]{2})(?!\d)", s)
    return float(m.group(1).replace(",", "")) if m else None


def _find_date(s: str):
    m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", s)
    if m:
        return m.group(1)
    m = re.search(r"\b(\d{1,2})[/\-](\d{1,2})(?:[/\-](\d{2,4}))?\b", s)
    if m:
        y = m.group(3) or "2024"
        if len(y) == 2:
            y = "20" + y
        return f"{int(y):04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return None


def _find_vendor(s: str):
    for v in VENDORS:
        if v.lower() in s.lower():
            return v
    m = re.search(r"\b(?:from|at)\s+([A-Z][A-Za-z&'.]+(?:\s[A-Z][A-Za-z&'.]+){0,2})", s)
    return m.group(1).strip() if m else None


def _classify(low: str) -> tuple[str, float]:
    for cat, needles in KEYWORD_RULES:
        if any(n in low for n in needles):
            return cat, 0.8
    return "other", 0.35


def _complete_local(item_text: str) -> str:
    low = item_text.lower()
    cat, conf = _classify(low)
    amount = _parse_amount(item_text)
    materials = [m for m in MATERIALS if m in low]
    phase = next((p for p in PHASES if p != "general" and p.replace("_", " ") in low), None)
    labor = None
    lm = re.search(r"(\d+(?:\.\d+)?)\s*(?:hrs?|hours?)\b", item_text, re.I)
    if lm:
        labor = float(lm.group(1))
    item = {
        "category": cat,
        "category_confidence": conf,
        "title": " ".join(item_text.split()[:8]),
        "summary": re.split(r"(?<=[.!?])\s", item_text)[0][:180],
        "occurred_at": _find_date(item_text),
        "vendor": _find_vendor(item_text),
        "amount": amount,
        "currency": "USD",
        "materials": materials,
        "labor_hours": labor,
        "phase": phase,
        "location": None,
        "people": [],
        "follow_up_actions": [],
        "tags": materials[:6],
        "flags": [],
        "compliance_notes": None,
        "source_excerpt": item_text[:180],
    }
    return json.dumps(item, ensure_ascii=False)
