"""Checks on reading a phone chat export.

The load-bearing test is the one asserting a send date never reaches the job
stream. Everything else is format handling.
"""

from pathlib import Path

from src.phone_import import describe, is_noise, parse_export, parse_line

EXPORT = Path("data/phone_exports/whatsapp_deck_build.txt").read_text(encoding="utf-8")


# --- the decision that matters -----------------------------------------------

def test_no_send_date_reaches_the_job_stream():
    # An export stamps every line with when it was typed. Using that as the
    # event date would be the date-inheritance bug with a new source.
    stream, _ = parse_export(EXPORT)

    for stamp in ("03/08/2026", "04/08/2026", "05/08/2026", "07:14", "09:41"):
        assert stamp not in stream


def test_the_line_that_proves_why():
    # Sent on the 5th, describing something that happened the previous week.
    # If send times were dates, this item would be a week wrong.
    stream, _ = parse_export(EXPORT)

    assert "building control came round last tuesday" in stream
    assert "05/08/2026" not in stream


def test_the_window_is_reported_to_the_person_instead():
    # Thrown away in the stream, kept for the human. Both are deliberate.
    _, stats = parse_export(EXPORT)

    assert stats["first_sent"] == "03/08/2026"
    assert stats["last_sent"] == "05/08/2026"


def test_the_note_says_send_times_were_not_used():
    _, stats = parse_export(EXPORT)

    assert "not used as event dates" in describe(stats)


# --- formatting is fixed, judgement is not -----------------------------------

def test_a_message_that_wrapped_is_rejoined():
    # One message split by the file format, not two events.
    stream, _ = parse_export(EXPORT)

    assert "leave it 3 days before we load it so nothing heavy on it til friday" in stream


def test_two_messages_from_one_person_stay_two_lines():
    # They are obviously one thought. Merging them is the judgement that broke
    # 08_dense_stream, and it is the organizer's call, not the importer's.
    stream, _ = parse_export(EXPORT)

    assert "Priya: skip is here but the driver says he cant get down the side alley" in stream
    assert "Priya: might need to move it round the front" in stream


def test_the_sender_is_kept_because_the_organizer_uses_it():
    stream, _ = parse_export(EXPORT)

    assert stream.startswith("Dan Reyes: morning - posts are in")


# --- noise ------------------------------------------------------------------

def test_the_encryption_notice_is_dropped():
    stream, _ = parse_export(EXPORT)

    assert "end-to-end encrypted" not in stream


def test_media_placeholders_are_dropped():
    # Left in, "<Media omitted>" becomes a photo item about no photo.
    stream, _ = parse_export(EXPORT)

    assert "Media omitted" not in stream


def test_a_deleted_message_is_dropped():
    stream, _ = parse_export(EXPORT)

    assert "This message was deleted" not in stream


def test_the_dropped_lines_are_counted_not_hidden():
    _, stats = parse_export(EXPORT)

    assert stats["dropped"] == 3
    assert "3 lines dropped as app noise" in describe(stats)


def test_is_noise_ignores_case_and_angle_brackets():
    assert is_noise("<Media omitted>")
    assert is_noise("MEDIA OMITTED")
    assert not is_noise("concrete poured")


# --- the real content survives ----------------------------------------------

def test_every_real_message_comes_through():
    stream, stats = parse_export(EXPORT)

    assert stats["messages"] == 8
    assert len(stream.splitlines()) == 8


def test_the_senders_are_listed():
    _, stats = parse_export(EXPORT)

    assert stats["senders"] == ["Dan Reyes", "Priya", "Sara Whitlock"]


def test_an_amount_survives_the_import():
    stream, _ = parse_export(EXPORT)

    assert "86.40" in stream


def test_a_client_question_survives_the_import():
    stream, _ = parse_export(EXPORT)

    assert "is the handrail included in the quote" in stream


# --- the other export shape --------------------------------------------------

def test_the_dashed_format_parses_too():
    # Android and some locales export without brackets.
    stream, stats = parse_export("05/08/2026, 08:01 - Priya: timber delivery pushed to friday")

    assert stream == "Priya: timber delivery pushed to friday"
    assert stats["messages"] == 1


def test_a_twelve_hour_timestamp_parses():
    parsed = parse_line("[05/08/2026, 7:55:19 PM] Dan: concrete poured")

    assert parsed is not None
    assert parsed[1] == "Dan"


def test_a_line_that_is_not_a_message_returns_none():
    assert parse_line("just some text") is None


# --- nothing to read ---------------------------------------------------------

def test_an_empty_export_says_so_rather_than_returning_a_blank_stream():
    stream, stats = parse_export("")

    assert stream == ""
    assert "No messages found" in describe(stats)


def test_a_file_that_is_not_an_export_reports_nothing_found():
    _, stats = parse_export("Project: something\nsome notes\nmore notes")

    assert stats["messages"] == 0
