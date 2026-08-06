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

# Phone numbers, US social security numbers, and card-shaped digit runs.
# People write these the way they write them, not the way a regex would like:
# (555) 123-4567 and 4111 1111 1111 1111 are the common forms, and an earlier
# version of this pattern matched neither.
PII_PATTERN = re.compile(
    r"\(\d{3}\)\s*\d{3}[-.\s]\d{4}"        # (555) 123-4567
    r"|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b"    # 555-123-4567, 555.123.4567
    r"|\b\d{3}-\d{2}-\d{4}\b"              # social security number
    r"|\b\d{4}(?:[-\s]\d{4}){3}\b"         # 4111 1111 1111 1111
    r"|\b\d{13,16}\b"                      # the same card with nothing between
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
    """Redact personal data out of what we wrote, and say that we did.

    The title gets the same treatment as the summary. It is the largest line on
    an item and is always on screen, so redacting only the summary left the
    number sitting in bold above the note promising it had been removed.

    The source excerpt is deliberately left alone. It is the evidence for the
    item and altering it would make the record less checkable, so the note says
    plainly that the original still has the number in it.
    """
    if not PII_PATTERN.search(f"{item.source_excerpt} {item.summary} {item.title}"):
        return False

    item.summary = PII_PATTERN.sub("[redacted]", item.summary)
    item.title = PII_PATTERN.sub("[redacted]", item.title)
    item.compliance_notes = item.compliance_notes or (
        "Possible personal data in the source. It has been redacted from the "
        "title and summary, but the original text still contains it."
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

    # A missing date is deliberately not a flag. Most lines in a real job
    # stream never carry one, so flagging them marked every item for review and
    # made the flag mean nothing. The date is already visible on the item, and a
    # date that was dropped by grounding already writes its own warning.

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
