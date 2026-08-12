"""Checks on the calendar export.

The interesting assertions are all about what does NOT come out. An undated item
must never acquire a day, and a to-do must never acquire a deadline, because a
calendar is exactly where an invented date would look most convincing.
"""

from datetime import datetime, timezone

from src.calendar_export import (
    LINE_LIMIT,
    counts,
    escape_text,
    fold,
    to_ics,
)
from src.schema import JobItem, JobOrganizationResult

STAMP = datetime(2026, 8, 12, 9, 0, 0, tzinfo=timezone.utc)


def item(**overrides):
    base = {
        "item_id": "item_001",
        "category": "inspection",
        "title": "Final roof inspection",
        "summary": "The roof passed its final inspection.",
        "source_excerpt": "passed the final roof inspection",
    }
    return JobItem(**{**base, **overrides})


def result_with(*items, project="Hollis roof"):
    return JobOrganizationResult(
        project_name=project, items=list(items), overall_summary="A roof job."
    )


def ics(*items, **kwargs):
    return to_ics(result_with(*items, **kwargs), now=STAMP)


# --- what becomes what -------------------------------------------------------

def test_a_dated_item_becomes_an_event_on_that_day():
    text = ics(item(date="2026-08-05"))

    assert "BEGIN:VEVENT" in text
    assert "DTSTART;VALUE=DATE:20260805" in text


def test_a_whole_day_event_ends_the_next_day():
    # DTEND is exclusive. Without this some clients render nothing at all.
    text = ics(item(date="2026-08-05"))

    assert "DTEND;VALUE=DATE:20260806" in text


def test_an_undated_action_becomes_a_todo():
    text = ics(item(date=None, action_required=True, action="Chase the supplier"))

    assert "BEGIN:VTODO" in text
    assert "BEGIN:VEVENT" not in text


def test_an_undated_todo_carries_no_due_date():
    # The whole point. The input never said when, so neither does the calendar.
    text = ics(item(date=None, action_required=True, action="Chase the supplier"))

    assert "DUE" not in text


def test_an_undated_item_with_no_action_is_left_out_entirely():
    # It is a record, not a task. Putting it on a calendar would need a day.
    text = ics(item(date=None, action_required=False))

    assert "BEGIN:VEVENT" not in text
    assert "BEGIN:VTODO" not in text


def test_a_date_the_grounding_step_dropped_never_reaches_the_calendar():
    # src/dates.py sets date to None when it was not on the item's own line.
    # This is the end of that path: no day, no event.
    text = ics(item(date=None, action_required=True, action="Do the thing"))

    assert "DTSTART" not in text


def test_the_demo_sample_shape_is_todos_and_no_events():
    # 03_tricky_bathroom: every item undated, three of them actionable. The
    # calendar is all to-dos and no events, and that is the correct answer.
    text = ics(
        item(item_id="item_001", date=None, action_required=True, action="Investigate"),
        item(item_id="item_002", date=None, action_required=False),
        item(item_id="item_003", date=None, action_required=True, action="Reply"),
        item(item_id="item_004", date=None, action_required=False),
        item(item_id="item_005", date=None, action_required=True, action="Chase"),
    )

    assert text.count("BEGIN:VTODO") == 3
    assert "BEGIN:VEVENT" not in text


def test_counts_report_what_was_left_out():
    result = result_with(
        item(item_id="item_001", date="2026-08-05"),
        item(item_id="item_002", date=None, action_required=True, action="Chase"),
        item(item_id="item_003", date=None, action_required=False),
    )

    assert counts(result) == (1, 1, 1)


# --- the file is a real file -------------------------------------------------

def test_the_calendar_is_wrapped_and_closed():
    text = ics(item(date="2026-08-05"))

    assert text.startswith("BEGIN:VCALENDAR\r\n")
    assert text.rstrip().endswith("END:VCALENDAR")
    assert "VERSION:2.0" in text


def test_every_entry_carries_a_uid_and_a_stamp():
    text = ics(item(date="2026-08-05"))

    assert "UID:hollis-roof-item_001@foreman-job-organizer.invalid" in text
    assert "DTSTAMP:20260812T090000Z" in text


def test_two_items_do_not_share_a_uid():
    text = ics(item(item_id="item_001", date="2026-08-05"),
               item(item_id="item_002", date="2026-08-06"))
    uids = [line for line in text.split("\r\n") if line.startswith("UID:")]

    assert len(uids) == 2 and len(set(uids)) == 2


def test_lines_use_crlf():
    assert "\r\n" in ics(item(date="2026-08-05"))


# --- text that would otherwise break the format ------------------------------

def test_commas_and_semicolons_in_model_text_are_escaped():
    # The title came from a model reading arbitrary input. A bare comma in a
    # TEXT value ends the value early and corrupts everything after it.
    text = ics(item(date="2026-08-05", title="Cabinets arrived, two doors scratched"))

    assert "Cabinets arrived\\, two doors scratched" in text


def test_a_backslash_is_escaped_before_anything_else():
    assert escape_text("a\\b,c") == "a\\\\b\\,c"


def test_newlines_in_a_description_become_the_literal_escape():
    assert "\\n" in escape_text("one\ntwo")


def test_a_long_line_is_folded_and_continues_with_a_space():
    folded = fold("DESCRIPTION:" + "x" * 200)
    parts = folded.split("\r\n")

    assert len(parts) > 1
    assert all(part.startswith(" ") for part in parts[1:])
    assert len(parts[0].encode("utf-8")) <= LINE_LIMIT


def test_folding_never_splits_a_multibyte_character():
    # Counting characters instead of octets breaks on any accented name, and a
    # cut mid-character produces a file no parser will read.
    folded = fold("SUMMARY:" + "é" * 120)

    for part in folded.split("\r\n"):
        part.encode("utf-8").decode("utf-8")
        assert len(part.encode("utf-8")) <= LINE_LIMIT


def test_a_short_line_is_left_alone():
    assert fold("VERSION:2.0") == "VERSION:2.0"


# --- the entry says where it came from ---------------------------------------

def test_the_description_quotes_the_source_line():
    text = ics(item(date="2026-08-05"))

    assert "From the job stream" in text
    assert "passed the final roof inspection" in text


def test_a_flagged_item_says_so_in_the_calendar():
    text = ics(item(date="2026-08-05", flags=["safety_review"]))

    assert "Flagged for review: safety_review" in text
