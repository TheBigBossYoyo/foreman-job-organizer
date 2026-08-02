"""Turn a set of items into a tidy timeline + job summary + next-actions.

Deterministic (no AI), so it is always reliable. Mirrors the PHP app's
Aggregator/Chain.
"""
from __future__ import annotations

from .schema import CATEGORY_LABELS, REVIEW_FLAGS, JobItem


def timeline(items: list[JobItem]) -> list[dict]:
    """Chronological; undated items sink to the bottom in input order."""
    dated = [it for it in items if it.occurred_at]
    undated = [it for it in items if not it.occurred_at]
    dated.sort(key=lambda it: it.occurred_at or "")
    return [
        {
            "date": it.occurred_at,
            "category": it.category,
            "title": it.title,
            "summary": it.summary,
            "amount": it.amount,
            "flags": it.flags,
        }
        for it in dated + undated
    ]


def next_actions(items: list[JobItem]) -> list[str]:
    """Follow-ups plus the actions implied by safety / missing-money flags."""
    actions: list[str] = []
    for it in items:
        actions.extend(a for a in it.follow_up_actions if a.strip())
        title = it.title or it.summary or "item"
        if "safety_review" in it.flags:
            actions.append(f"Review safety item: {title}")
        if "missing_amount" in it.flags:
            actions.append(f"Add the missing cost for: {title}")
    # dedupe, keep order
    seen: set[str] = set()
    out: list[str] = []
    for a in actions:
        if a not in seen:
            seen.add(a)
            out.append(a)
    return out[:12]


def summarize(items: list[JobItem]) -> dict:
    total_spend = round(sum(it.amount for it in items if it.amount), 2)
    total_labor = round(sum(it.labor_hours for it in items if it.labor_hours), 2)
    spend_by_cat: dict[str, float] = {}
    materials: dict[str, int] = {}
    phases: set[str] = set()
    safety, review = [], 0
    for it in items:
        if it.amount:
            spend_by_cat[it.category] = round(spend_by_cat.get(it.category, 0) + it.amount, 2)
        for m in it.materials:
            materials[m] = materials.get(m, 0) + 1
        if it.phase:
            phases.add(it.phase)
        if it.category == "safety_incident" or "safety_review" in it.flags:
            safety.append(it.title or it.summary)
        if it.needs_review():
            review += 1

    dates = sorted(it.occurred_at for it in items if it.occurred_at)
    n = len(items)
    phase_list = ", ".join(sorted(p.replace("_", " ") for p in phases)) or "general work"
    narrative = f"Organized {n} job update{'' if n == 1 else 's'} covering {phase_list}."
    if total_spend:
        narrative += f" Recorded spend of ${total_spend:,.2f}."
    if total_labor:
        narrative += f" {total_labor:.1f} labor hours logged."
    if safety:
        narrative += f" ⚠ {len(safety)} safety item(s) need human review."

    return {
        "item_count": n,
        "total_spend": total_spend,
        "total_labor_hours": total_labor,
        "spend_by_category": [
            {"category": c, "label": CATEGORY_LABELS.get(c, c), "amount": a}
            for c, a in sorted(spend_by_cat.items(), key=lambda kv: -kv[1])
        ],
        "materials_tally": dict(sorted(materials.items(), key=lambda kv: -kv[1])),
        "phases_touched": sorted(phases),
        "date_range": {"start": dates[0] if dates else None, "end": dates[-1] if dates else None},
        "safety_flags": safety,
        "needs_review": review,
        "timeline": timeline(items),
        "next_actions": next_actions(items),
        "narrative": narrative,
    }
