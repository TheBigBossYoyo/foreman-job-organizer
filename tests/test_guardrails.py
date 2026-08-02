from src.guardrails import enforce, enforce_all, needs_review
from src.schema import JobItem, JobOrganizationResult


def make_item(**overrides):
    base = {
        "item_id": "item_001",
        "category": "contractor_update",
        "date": "2026-07-21",
        "title": "An item",
        "summary": "Something happened.",
        "source_excerpt": "Something happened on site.",
    }
    return JobItem(**{**base, **overrides})


def test_injury_language_forces_a_safety_review():
    item = enforce(make_item(
        summary="Tony cut his hand and went to urgent care.",
        source_excerpt="tony cut his hand on the tile saw, took him to urgent care",
    ))

    assert "safety_review" in item.flags
    assert item.category == "issue"
    assert item.priority == "urgent"
    assert item.action_required is True
    assert "human review" in item.compliance_notes


def test_a_specific_category_survives_the_safety_rule():
    # The item is still flagged, but calling a hospital receipt an "issue" would
    # lose information the model got right.
    item = enforce(make_item(
        category="receipt",
        amount=240.0,
        summary="Urgent care visit billed to the job.",
        source_excerpt="urgent care $240.00",
    ))

    assert "safety_review" in item.flags
    assert item.category == "receipt"


def test_a_receipt_with_no_amount_is_flagged():
    assert "missing_amount" in enforce(make_item(category="receipt", amount=None)).flags


def test_a_receipt_with_an_amount_is_not_flagged():
    item = enforce(make_item(category="receipt", amount=142.75, currency="USD"))

    assert "missing_amount" not in item.flags


def test_an_ordinary_update_with_no_amount_is_not_flagged():
    # Only categories that are about money should expect a number.
    assert "missing_amount" not in enforce(make_item(category="photo")).flags


def test_a_phone_number_is_redacted_from_the_summary():
    item = enforce(make_item(
        summary="Call Maya on 555-123-4567 about the tile.",
        source_excerpt="maya said call her on 555-123-4567",
    ))

    assert "possible_pii" in item.flags
    assert "555-123-4567" not in item.summary
    assert "[redacted]" in item.summary


def test_the_source_excerpt_is_left_intact_when_pii_is_redacted():
    # We redact what we present, not the evidence. Say so rather than pretend.
    item = enforce(make_item(
        summary="Call Maya on 555-123-4567.",
        source_excerpt="maya said call her on 555-123-4567",
    ))

    assert "555-123-4567" in item.source_excerpt
    assert "still contains it" in item.compliance_notes


def test_low_confidence_is_flagged():
    assert "low_confidence" in enforce(make_item(confidence="low")).flags


def test_a_missing_date_is_not_a_review_flag():
    # Most lines in a real stream carry no date. Flagging them all marked every
    # item for review and made the flag useless.
    item = enforce(make_item(category="photo", date=None, confidence="high"))

    assert item.flags == []
    assert not needs_review(item)


def test_a_clean_item_gets_no_flags():
    item = enforce(make_item(category="photo", date="2026-07-21", confidence="high"))

    assert item.flags == []
    assert not needs_review(item)


def test_enforce_all_counts_the_flagged_items_in_the_warnings():
    result = JobOrganizationResult(
        items=[
            make_item(item_id="item_001", category="receipt", amount=None),
            make_item(item_id="item_002", category="photo", confidence="high"),
        ],
        overall_summary="A job.",
    )

    enforce_all(result)

    assert result.items[0].flags == ["missing_amount"]
    assert result.items[1].flags == []
    assert "1 of 2 items were flagged" in result.warnings[-1]
