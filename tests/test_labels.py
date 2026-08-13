"""Guards on the display names.

These exist because the maps were duplicated between app.py and job_record.py
for about an hour and had already drifted: client_update read "Client" on the
screen and "Client update" in the printed record. Nothing failed, which is why
it needs a test rather than care.

A missing label is worse than a wrong one. The fallback prints the raw value, so
a category added to the schema without a label here reaches a contractor as
"contractor_update" in a document they were asked to sign off.
"""

from src.labels import (
    CATEGORIES,
    CATEGORY_COLORS,
    CATEGORY_LABELS,
    PROVIDER_LABELS,
    PROVIDER_PHRASES,
)


def test_every_schema_category_has_a_label():
    assert CATEGORIES - set(CATEGORY_LABELS) == set()


def test_every_schema_category_has_a_colour():
    assert CATEGORIES - set(CATEGORY_COLORS) == set()


def test_no_label_exists_for_a_category_the_schema_dropped():
    # The other direction. A leftover key is a category someone removed and
    # then forgot, and it hides the fact that the schema moved.
    assert set(CATEGORY_LABELS) - CATEGORIES == set()
    assert set(CATEGORY_COLORS) - CATEGORIES == set()


def test_the_screen_and_the_document_use_the_same_category_names():
    # The actual bug this module was written to end. app.py and job_record.py
    # both import this one map, so the only way they can disagree now is if
    # someone reintroduces a local copy.
    from app import CATEGORY_LABELS as on_screen
    from src.job_record import CATEGORY_LABELS as in_document

    assert on_screen is CATEGORY_LABELS
    assert in_document is CATEGORY_LABELS


def test_the_two_provider_maps_cover_the_same_providers():
    # They are allowed to differ in wording, not in coverage. A provider with a
    # sidebar label but no prose phrase would print its raw key in the record.
    assert set(PROVIDER_LABELS) == set(PROVIDER_PHRASES)


def test_the_provider_phrases_read_inside_a_sentence():
    # This is the reason there are two maps rather than one, so it is worth
    # pinning: the record says "Organized by <phrase>".
    assert PROVIDER_PHRASES["local"] == "the local rule-based engine"
    assert PROVIDER_LABELS["local"] == "Local engine"


def test_no_label_is_blank():
    for mapping in (CATEGORY_LABELS, PROVIDER_LABELS, PROVIDER_PHRASES):
        assert all(value.strip() for value in mapping.values())
