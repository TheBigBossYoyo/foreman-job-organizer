import json

import pytest

from src import organizer
from src.organizer import JobOrganizerError, extract_json_object, organize_job_stream


def test_plain_json():
    assert extract_json_object('{"project_name": "Roof repair"}') == {
        "project_name": "Roof repair"
    }


def test_strips_markdown_fence():
    reply = '```json\n{"project_name": "Roof repair"}\n```'
    assert extract_json_object(reply)["project_name"] == "Roof repair"


def test_ignores_text_around_the_object():
    reply = 'Sure! Here is the JSON:\n{"project_name": "Roof repair"}\nLet me know if you need changes.'
    assert extract_json_object(reply)["project_name"] == "Roof repair"


def test_no_json_at_all_is_flagged():
    with pytest.raises(JobOrganizerError):
        extract_json_object("I could not process that request.")


def test_broken_json_is_flagged():
    with pytest.raises(JobOrganizerError):
        extract_json_object('{"project_name": "Roof repair",}')


def test_empty_input_is_rejected_before_calling_the_api():
    with pytest.raises(ValueError):
        organize_job_stream("   ")


def test_the_pipeline_drops_a_date_the_item_does_not_state(monkeypatch):
    """An end-to-end check that grounding runs, with the API call stubbed out.

    The excerpts here leave the date prefix out, the way the model really
    writes them, so this exercises the match against the source line.
    """
    stream = (
        "2026-07-23 - tore off the old shingles\n"
        "photo_0102.jpg - felt down, looks clean\n"
    )
    reply = json.dumps({
        "items": [
            {
                "item_id": "item_001",
                "category": "contractor_update",
                "date": "2026-07-23",
                "title": "Tear off",
                "summary": "The old shingles came off.",
                "source_excerpt": "tore off the old shingles",
            },
            {
                "item_id": "item_002",
                "category": "photo",
                "date": "2026-07-23",
                "title": "Felt photo",
                "summary": "A photo of the felt.",
                "source_excerpt": "photo_0102.jpg - felt down, looks clean",
            },
        ],
        "overall_summary": "A roof job.",
        "warnings": [],
    })
    monkeypatch.setattr(
        organizer.providers, "complete", lambda s, u, raw, model=None: (reply, "anthropic", [])
    )

    result = organize_job_stream(stream)

    assert result.items[0].date == "2026-07-23"
    assert result.items[1].date is None
    assert any("item_002" in warning for warning in result.warnings)


def test_the_result_records_which_provider_answered(monkeypatch):
    reply = json.dumps({
        "items": [{
            "item_id": "item_001",
            "category": "other",
            "title": "A thing",
            "summary": "Something happened.",
            "source_excerpt": "a thing happened",
        }],
        "overall_summary": "A job.",
    })
    monkeypatch.setattr(
        organizer.providers, "complete", lambda s, u, raw, model=None: (reply, "groq", [])
    )

    assert organize_job_stream("a thing happened").provider == "groq"


def test_a_skipped_provider_is_reported_in_the_warnings(monkeypatch):
    # The provider field says groq answered. It does not say anthropic was
    # asked first and failed, and that is the part a reader needs.
    reply = json.dumps({
        "items": [{
            "item_id": "item_001",
            "category": "other",
            "title": "A thing",
            "summary": "Something happened.",
            "source_excerpt": "a thing happened",
        }],
        "overall_summary": "A job.",
    })
    monkeypatch.setattr(
        organizer.providers,
        "complete",
        lambda s, u, raw, model=None: (reply, "groq", ["anthropic: 401 invalid api key"]),
    )

    result = organize_job_stream("a thing happened")

    assert "Fell back after anthropic: 401 invalid api key" in result.warnings


def test_a_dead_chain_surfaces_as_a_job_organizer_error(monkeypatch):
    def boom(*args, **kwargs):
        raise organizer.providers.ProviderError("everything is down")

    monkeypatch.setattr(organizer.providers, "complete", boom)

    with pytest.raises(JobOrganizerError):
        organize_job_stream("some text")
