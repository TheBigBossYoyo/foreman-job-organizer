import pytest

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
