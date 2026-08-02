"""Rules the pipeline enforces, rather than rules the model is asked to follow.

The date work taught this project one thing above all: a rule written into the
prompt is a request, and a rule written into the code is a guarantee. Two prompt
rewrites failed to stop dates being copied between lines; twenty lines of code
stopped it completely.

So the rules that actually matter on a construction job live here. This is the
idea worth taking from the other prototype in this repo, adapted to our schema.

None of these invent anything. They only ever add a flag, raise a priority, or
redact. The one exception is the safety rule, which can move a vague category to
`issue` — and it will not overwrite a specific category the model already chose.
"""

import re

# Words that mean somebody may have been hurt. Deliberately stemmed, so "injury",
# "injured" and "injuries" all match on "injur".
SAFETY_WORDS = [
    "injur", "hurt", "accident", "near miss", "osha", "hospital", "first aid",
    "urgent care", "bleeding", "fell off", "fell from", "electric shock",
]

# A phone number, a US social security number, or a long card-shaped digit run.
PII_PATTERN = re.compile(
    r"\b(\d{3}[-.\s]\d{3}[-.\s]\d{4}|\d{3}-\d{2}-\d{4}|\d{13,16})\b"
)

# Categories where an amount is the point of the item. One of these arriving
# without a number means the number was missed, not that there wasn't one.
MONEY_CATEGORIES = ("receipt", "payment")

# Categories specific enough that the safety rule should leave them alone.
VAGUE_CATEGORIES = ("other", "contractor_update")


def flag_safety(item):
    """Injury language outranks whatever the model decided this item was."""
    text = f"{item.source_excerpt} {item.summary}".lower()
    if not any(word in text for word in SAFETY_WORDS):
        return False

    if item.category in VAGUE_CATEGORIES:
        item.category = "issue"
    item.priority = "urgent"
    item.action_required = True
    item.compliance_notes = item.compliance_notes or (
        "Injury or safety language detected. Needs a human review before any "
        "action, and may carry a reporting obligation."
    )
    return True


def flag_missing_amount(item):
    """A receipt or a payment with no number on it is an incomplete record."""
    return item.category in MONEY_CATEGORIES and item.amount is None


def flag_pii(item):
    """Redact personal data out of the summary, and say that we did."""
    if not PII_PATTERN.search(f"{item.source_excerpt} {item.summary}"):
        return False

    item.summary = PII_PATTERN.sub("[redacted]", item.summary)
    item.compliance_notes = item.compliance_notes or (
        "Possible personal data in the source. It has been redacted from the "
        "summary, but the original text still contains it."
    )
    return True


def enforce(item):
    """Apply every rule to one item and return it. Mutates in place."""
    flags = set(item.flags)

    if flag_safety(item):
        flags.add("safety_review")
    if flag_missing_amount(item):
        flags.add("missing_amount")
    if flag_pii(item):
        flags.add("possible_pii")
    if item.confidence == "low":
        flags.add("low_confidence")
    if item.date is None:
        flags.add("no_date")

    item.flags = sorted(flags)
    return item


def enforce_all(result):
    """Run the rules over every item, and surface a count in the warnings."""
    for item in result.items:
        enforce(item)

    flagged = [item for item in result.items if item.flags]
    if flagged:
        result.warnings.append(
            f"{len(flagged)} of {len(result.items)} items were flagged for review "
            f"by the guardrails."
        )
    return result


def needs_review(item):
    """True when a human should look at this item before it is trusted."""
    return bool(item.flags)
