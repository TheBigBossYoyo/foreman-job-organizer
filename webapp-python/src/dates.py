"""Date grounding — only trust a date that is written in the item's own text.

Shared lesson across both team prototypes: a model will carry a date down from
the line above, or invent a year for a bare "7/27". Two prompt rewrites did not
move inheritance; a small code check did. This is the check.
"""
from __future__ import annotations

import re

MONTHS = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]


def date_is_grounded(iso_date: str | None, text: str | None) -> bool:
    """True when an ISO date appears in text in any common written form.

    Accepts 2026-07-23, 7/23, 07-23, 7.23, "July 23" and "23 July". A bare
    "7/23" with no year still counts — the question is whether the model read
    the date off this item, not whether the year was stated.
    """
    if not iso_date or not text:
        return False
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", iso_date)
    if not m:
        return False
    month, day = int(m.group(2)), int(m.group(3))
    t = text.lower()

    if iso_date.lower() in t:
        return True
    if re.search(rf"\b0?{month}\s*[/\-.]\s*0?{day}\b", t):
        return True

    name = MONTHS[month - 1]
    word = rf"(?:{name}|{name[:3]})\.?"
    if re.search(rf"\b{word}\s+0?{day}\b", t):
        return True
    if re.search(rf"\b0?{day}(?:st|nd|rd|th)?\s+(?:of\s+)?{word}", t):
        return True
    return False
