"""Check that a date the model returned is really written in the item it belongs to.

Week 3 scoring found the model copying a date off the line above: a dated line
gets read as a heading for the block underneath it, and every item in that block
comes back carrying the same date. Rewriting the prompt rule did not move it at
all, so this checks it in code instead.

The rule is narrow on purpose. We are not parsing the date out of the text, only
asking whether the date the model already gave us appears where that item came
from. If it does not, the model got it from somewhere else and we drop it.

The comparison runs against the item's line in the sample, not against its
source_excerpt. The first version of this check used the excerpt and made the
score worse, because the model quotes "Crew completed cabinet removal" and
leaves the "2026-07-21 - " in front of it out. Judging by the excerpt threw away
correct dates. The line the excerpt was taken from still has the prefix.
"""

import re
from datetime import date as date_cls

from .text import normalize

# A source line shorter than this is not enough to identify an item by. Without
# the guard, a stray "ok" line matches almost any excerpt that contains it.
MIN_LINE_MATCH = 8

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


def source_lines_for(excerpt, source_text):
    """The lines of the sample that this excerpt was taken from.

    Usually one line contains the whole excerpt. A quote that runs across a line
    break is the other way round, so we accept containment in both directions.
    """
    target = normalize(excerpt or "")
    if not target:
        return []

    found = []
    for line in source_text.splitlines():
        line_text = normalize(line)
        if not line_text:
            continue
        if target in line_text:
            found.append(line)
        elif len(line_text) >= MIN_LINE_MATCH and line_text in target:
            found.append(line)
    return found


def date_is_grounded_in_source(iso_date, excerpt, source_text):
    """True when the date appears on the sample line this item came from."""
    lines = source_lines_for(excerpt, source_text)
    if not lines:
        # We could not find the item in the sample, so we have nothing better to
        # judge against. Fall back to the excerpt rather than drop a date we
        # cannot actually assess.
        return date_is_grounded(iso_date, excerpt)
    return any(date_is_grounded(iso_date, line) for line in lines)


def ground_dates(result, source_text=None):
    """Drop any item date that is not written where that item came from.

    Mutates and returns the result. Every dropped date leaves a warning, so a
    reviewer can see the item lost a date rather than never having had one.
    """
    dropped = []

    for item in result.items:
        if item.date is None:
            continue

        if source_text:
            keep = date_is_grounded_in_source(item.date, item.source_excerpt, source_text)
        else:
            keep = date_is_grounded(item.date, item.source_excerpt)

        if not keep:
            dropped.append((item.item_id, item.date))
            item.date = None

    for item_id, lost in dropped:
        result.warnings.append(
            f"{item_id}: dropped the date {lost}. It is not written on this "
            f"item's own line, so it was most likely copied from another one."
        )

    return result
