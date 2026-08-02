"""Turn a list of items into the numbers a foreman would actually ask for.

No model involved. Everything here is arithmetic over items that have already
been validated, grounded and guardrailed, so it cannot introduce a fact that was
not already in the result. Adapted from the other prototype in this repo.

Kept separate from the organizer on purpose: this can be re-run over a stored
result without spending another API call.
"""

from .guardrails import needs_review


def ordered_items(items):
    """Chronological, with undated items held where the source put them.

    An undated line still says something about when it happened: it sits
    between two dated lines in the input, so it belongs between them. Sinking
    every undated item to the bottom threw that away, and on a stream where
    most lines carry no date it left the list in barely any order at all.

    So an undated item sorts as if it shared the date of the last dated item
    above it. That is an ordering decision only. Its date field stays null and
    it is still shown as undated. We are placing it, not dating it.
    """
    anchor = ""
    keys = {}

    for position, item in enumerate(items):
        if item.date:
            anchor = item.date
        # An undated item before the first date keeps the empty anchor, which
        # sorts ahead of every real date, matching where it appears.
        keys[id(item)] = (anchor, position)

    return sorted(items, key=lambda item: keys[id(item)])


def timeline(items):
    """The rows a reader sees, in the order they should be read."""
    return [
        {
            "date": item.date,
            "category": item.category,
            "title": item.title,
            "summary": item.summary,
            "amount": item.amount,
            "currency": item.currency,
            "flags": item.flags,
        }
        for item in ordered_items(items)
    ]


def spend_by_currency(items):
    """Totals per currency. Adding TND to USD would be a made-up number."""
    totals = {}
    for item in items:
        if item.amount is None:
            continue
        currency = item.currency or "unknown"
        totals[currency] = round(totals.get(currency, 0) + item.amount, 2)
    return dict(sorted(totals.items()))


def derived_actions(items):
    """Actions implied by the items themselves, on top of what the model listed."""
    actions = []

    for item in items:
        label = item.title or item.summary
        if item.action_required and item.action:
            actions.append(item.action)
        if "safety_review" in item.flags:
            actions.append(f"Review the safety item: {label}")
        if "missing_amount" in item.flags:
            actions.append(f"Find the missing amount for: {label}")
        if "possible_pii" in item.flags:
            actions.append(f"Check personal data before sharing: {label}")

    seen = set()
    unique = []
    for action in actions:
        if action not in seen:
            seen.add(action)
            unique.append(action)
    return unique


def summarize(result):
    """One dict with the counts, totals and timeline for the whole job."""
    items = result.items
    dates = sorted(item.date for item in items if item.date)

    counts = {}
    for item in items:
        counts[item.category] = counts.get(item.category, 0) + 1

    return {
        "item_count": len(items),
        "needs_review": sum(1 for item in items if needs_review(item)),
        "undated": sum(1 for item in items if item.date is None),
        "spend": spend_by_currency(items),
        "category_counts": dict(sorted(counts.items(), key=lambda pair: -pair[1])),
        "date_range": {
            "start": dates[0] if dates else None,
            "end": dates[-1] if dates else None,
        },
        "timeline": timeline(items),
        "open_actions": list(dict.fromkeys(result.open_actions + derived_actions(items))),
    }
