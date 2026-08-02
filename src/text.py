"""Shared text tidying, so the scorer and the date check compare like with like."""

import re


def normalize(text):
    """Lower-case, straighten curly quotes, and collapse runs of whitespace."""
    text = text.lower()
    for curly, straight in [("‘", "'"), ("’", "'"), ("“", '"'), ("”", '"')]:
        text = text.replace(curly, straight)
    return re.sub(r"\s+", " ", text).strip()
