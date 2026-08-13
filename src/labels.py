"""The human-readable name for every machine value, in one place.

These were duplicated between app.py and job_record.py for about an hour and
had already drifted: client_update read "Client" on screen and "Client update"
in the printed record. Nothing broke, which is the problem — the two would have
kept diverging quietly, and the document a contractor keeps would slowly stop
matching the screen they approved it on.

The provider names are deliberately two maps rather than one. The sidebar wants
a label in a column; the record wants a phrase that reads inside a sentence
("Organized by the local rule-based engine"). That is a real difference, so it
is written as two named things instead of two copies that look like a mistake.
"""

from typing import get_args

from .schema import Category

CATEGORY_LABELS = {
    "photo": "Photo",
    "receipt": "Receipt",
    "client_update": "Client",
    "contractor_update": "Site work",
    "inspection": "Inspection",
    "delivery": "Delivery",
    "schedule": "Schedule",
    "issue": "Issue",
    "payment": "Payment",
    "other": "Other",
}

# One colour per category, carried only by the timeline dot. Colour is the
# cheapest way to let someone find the receipts in a long list, and the dot is
# enough of it — tinting whole rows turns a record into a highlighter drawing.
CATEGORY_COLORS = {
    "photo": "#8B5CF6",
    "receipt": "#EA580C",
    "client_update": "#2563EB",
    "contractor_update": "#0F766E",
    "inspection": "#16A34A",
    "delivery": "#D97706",
    "schedule": "#0EA5E9",
    "issue": "#DC2626",
    "payment": "#059669",
    "other": "#94A3B8",
}

# Short, for a label in a column.
PROVIDER_LABELS = {
    "anthropic": "Anthropic Claude",
    "groq": "Groq",
    "local": "Local engine",
}

# Long, for running prose: "Organized by ...".
PROVIDER_PHRASES = {
    "anthropic": "Anthropic Claude",
    "groq": "Groq",
    "local": "the local rule-based engine",
}

CATEGORIES = frozenset(get_args(Category))
