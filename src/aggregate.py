"""Turn a list of items into the numbers a foreman would actually ask for.

No model involved. Everything here is arithmetic over items that have already
been validated, grounded and guardrailed, so it cannot introduce a fact that was
not already in the result. Adapted from the other prototype in this repo.

Kept separate from the organizer on purpose: this can be re-run over a stored
result without spending another API call.
"""

from .guardrails import needs_review


def timeline(items):
    """Chronological. Undated items sink to the bottom, in the order they came.

    Undated does not mean unimportant — it usually means the source line never
    said when. They stay visible rather than being dropped or guessed at.
    """
    dated = sorted((item for item in items if item.date), key=lambda item: item.date)
    undated = [item for item in items if not item.date]

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
        for item in dated + undated
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
