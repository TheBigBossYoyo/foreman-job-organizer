"""Check that a date the model returned is really written in the item it belongs to.

Week 3 scoring found the model copying a date off the line above: a dated line
gets read as a heading for the block underneath it, and every item in that block
comes back carrying the same date. Rewriting the prompt rule did not move it at
all, so this checks it in code instead.

The rule is narrow on purpose. We are not parsing the date out of the text, only
asking whether the date the model already gave us appears in that item's own
excerpt. If it does not, the model got it from somewhere else and we drop it.
"""

import re
from datetime import date as date_cls

MONTH_NAMES = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]


def parse_iso(value):
    """Return a date for a YYYY-MM-DD string, or None if it is not one."""
    try:
        return date_cls.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def month_pattern(month):
    """A regex fragment matching a month written long or short: july, jul, jul."""
    name = MONTH_NAMES[month - 1]
    return rf"{name[:3]}(?:{name[3:]})?\.?" if name[3:] else rf"{name}\.?"


def date_is_grounded(iso_date, excerpt):
    """True when iso_date is written somewhere in excerpt, in any common form.

    Accepts 2026-07-23, 7/23, 07-23, 7.23, "July 23" and "23 July". A bare
    "7/23" counts even though it carries no year: the point here is whether the
    model read the date off this item or imported it, not whether the year was
    stated.
    """
    parsed = parse_iso(iso_date)
    if parsed is None or not excerpt:
        return False

    text = excerpt.lower()
    if iso_date.lower() in text:
        return True

    month, day = parsed.month, parsed.day

    # 7/23, 07-23, 7.23, with or without a year after it.
    if re.search(rf"\b0?{month}\s*[/\-.]\s*0?{day}\b", text):
        return True

    word = month_pattern(month)
    if re.search(rf"\b{word}\s+0?{day}\b", text):
        return True
    if re.search(rf"\b0?{day}(?:st|nd|rd|th)?\s+(?:of\s+)?{word}", text):
        return True

    return False


def ground_dates(result):
    """Drop any item date that is not written in that item's own excerpt.

    Mutates and returns the result. Every dropped date leaves a warning, so a
    reviewer can see the item lost a date rather than never having had one.
    """
    dropped = []

    for item in result.items:
        if item.date is None:
            continue
        if not date_is_grounded(item.date, item.source_excerpt):
            dropped.append((item.item_id, item.date))
            item.date = None

    for item_id, lost in dropped:
        result.warnings.append(
            f"{item_id}: dropped the date {lost}. It is not written in this "
            f"item's own text, so it was most likely copied from another line."
        )

    return result
