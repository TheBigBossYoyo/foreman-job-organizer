import pytest
from pydantic import ValidationError

from src.schema import JobOrganizationResult


def make_result(**item_overrides):
    item = {
        "item_id": "item_001",
        "category": "issue",
        "date": None,
        "people": [],
        "location": None,
        "amount": None,
        "currency": None,
        "title": "Leak",
        "summary": "A leak was reported.",
        "action_required": True,
        "action": "Inspect the leak.",
        "priority": "high",
        "confidence": "high",
        "source_excerpt": "Leak reported",
    }
    item.update(item_overrides)
    return {
        "project_name": "Test project",
        "items": [item],
        "open_actions": ["Inspect the leak."],
        "overall_summary": "One issue requires inspection.",
        "warnings": [],
    }


def test_valid_result():
    result = JobOrganizationResult.model_validate(make_result())
    assert result.items[0].category == "issue"
    assert result.items[0].action_required is True


def test_currency_is_upper_cased():
    result = JobOrganizationResult.model_validate(make_result(currency="tnd", amount=118.9))
    assert result.items[0].currency == "TND"


def test_invented_category_is_rejected():
    with pytest.raises(ValidationError):
        JobOrganizationResult.model_validate(make_result(category="weather_delay"))


def test_negative_amount_is_rejected():
    with pytest.raises(ValidationError):
        JobOrganizationResult.model_validate(make_result(amount=-40))


def test_missing_summary_is_rejected():
    payload = make_result()
    del payload["overall_summary"]
    with pytest.raises(ValidationError):
        JobOrganizationResult.model_validate(payload)
