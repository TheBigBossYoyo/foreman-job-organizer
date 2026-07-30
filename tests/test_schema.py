from src.schema import JobOrganizationResult


def test_valid_result():
    result = JobOrganizationResult.model_validate(
        {
            "project_name": "Test project",
            "client_name": None,
            "property_address": None,
            "items": [
                {
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
            ],
            "open_actions": ["Inspect the leak."],
            "overall_summary": "One issue requires inspection.",
            "warnings": [],
        }
    )
    assert result.items[0].category == "issue"
    assert result.items[0].action_required is True
