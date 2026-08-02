from src.guardrails import enforce, ground_date
from src.schema import JobItem


def test_safety_language_forces_flag():
    item = JobItem(category="progress_update", category_confidence=0.9, title="saw incident")
    out = enforce(item, "Tony cut his hand and went to urgent care")
    assert out.category == "safety_incident"
    assert "safety_review" in out.flags


def test_never_invent_money_flags_missing_amount():
    item = JobItem(category="material_purchase", category_confidence=0.9, amount=None)
    out = enforce(item, "picked up drywall, no receipt yet")
    assert "missing_amount" in out.flags


def test_low_confidence_flagged():
    item = JobItem(category="other", category_confidence=0.3)
    out = enforce(item, "moved some stuff around")
    assert "low_confidence" in out.flags


def test_pii_redacted():
    item = JobItem(category="other", category_confidence=0.9, summary="call 555-123-4567")
    out = enforce(item, "call 555-123-4567")
    assert "possible_pii" in out.flags
    assert "[redacted]" in out.summary


def test_ungrounded_date_dropped():
    item = JobItem(category="other", category_confidence=0.9, occurred_at="2024-06-14")
    out = ground_date(item, "no date written here")
    assert out.occurred_at is None
    assert "date_unverified" in out.flags


def test_grounded_date_kept():
    item = JobItem(category="inspection", category_confidence=0.9, occurred_at="2024-06-14")
    out = ground_date(item, "inspection 6/14 passed")
    assert out.occurred_at == "2024-06-14"
