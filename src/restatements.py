"""Check that a restatement really is another mention, written in the input.

`10_repeated_event` states an inspection twice and a delivery twice, in
different words. The model folded each pair into one item on its own, and the
answer key expected four. Neither was wrong: nobody had decided what the right
answer was when an event is written down more than once.

The decision is one item per event, with the other wordings kept beside it. A
foreman reading a timeline wants one inspection, not the same one twice — but
the second mention is still something that was said, and dropping it silently
is the one habit this project does not have. So the fold is recorded rather
than performed in the dark.

This module is the same shape as dates.py, for the same reason. The model
proposes and the input decides. A restatement that is not actually written in
the input is dropped with a warning, because a quotation of something nobody
said is an invented fact wearing quote marks.
"""

from .text import normalize

# Below this length a fragment matches half the input by accident. "all good"
# appears in three of the ten samples.
MIN_RESTATEMENT = 12


def is_quoted_in(text, source_text):
    """True when this fragment really appears in the input."""
    return normalize(text) in normalize(source_text)


def mention_count(restatements):
    """How many times the event was written down: the item, plus its echoes."""
    return 1 + len(restatements or [])


def ground_restatements(result, source_text=None):
    """Drop any restatement the input does not support. Mutates and returns.

    Three ways to lose one, each of which leaves a warning naming the item:

    - it is not written in the input at all
    - it only repeats the item's own source_excerpt, which is the line the item
      is already made of rather than another mention of it
    - it is too short to identify anything

    A restatement is never promoted back into an item of its own here. If the
    fold was wrong, that is a segmentation error and the scorer's business.
    """
    dropped = []

    for item in result.items:
        if not item.restatements:
            continue

        kept = []
        # The item's own line counts as seen: quoting it back is not a second
        # mention, it is the same one.
        seen = {normalize(item.source_excerpt or "")}

        for raw in item.restatements:
            text = (raw or "").strip()
            key = normalize(text)

            if not key or len(key) < MIN_RESTATEMENT:
                dropped.append((item.item_id, text, "it is too short to identify an event"))
            elif key in seen:
                dropped.append((item.item_id, text, "it repeats a line already on this item"))
            elif source_text and not is_quoted_in(text, source_text):
                dropped.append((item.item_id, text, "it is not written anywhere in the input"))
            else:
                kept.append(text)
                seen.add(key)

        item.restatements = kept

    for item_id, text, reason in dropped:
        result.warnings.append(
            f"{item_id}: dropped a restatement because {reason}: \"{text}\""
        )

    return result
