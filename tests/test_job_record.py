"""Checks on the printable job record.

This is the one output meant to leave the building — attached to an email,
handed to a client, printed for a dispute. So the tests are mostly about what
it must never do: lose a warning, drop a source quote, or render model text as
markup.
"""

from datetime import datetime

from src.job_record import format_date, to_html
from src.schema import JobItem, JobOrganizationResult

WHEN = datetime(2026, 8, 12)


def item(**overrides):
    base = {
        "item_id": "item_001",
        "category": "inspection",
        "title": "Final roof inspection",
        "summary": "The roof passed its final inspection.",
        "source_excerpt": "passed the final roof inspection",
    }
    return JobItem(**{**base, **overrides})


def result_with(*items, **overrides):
    base = {
        "project_name": "Hollis roof",
        "client_name": "Ben Hollis",
        "property_address": "7 Cedar Court",
        "items": list(items) or [item()],
        "overall_summary": "A roof job.",
        "provider": "groq",
    }
    return JobOrganizationResult(**{**base, **overrides})


def html(*items, summary=None, **overrides):
    return to_html(result_with(*items, **overrides), summary=summary, generated=WHEN)


# --- it is a real, self-contained document -----------------------------------

def test_it_is_a_complete_html_document():
    page = html()

    assert page.startswith("<!doctype html>")
    assert page.rstrip().endswith("</html>")
    assert "<title>Job record — Hollis roof</title>" in page


def test_it_needs_nothing_from_the_network():
    # It has to open from an email attachment on a laptop with no wifi.
    page = html()

    assert "http://" not in page
    assert "https://" not in page
    assert "<link" not in page and "<script" not in page


def test_the_styles_are_inlined():
    assert "<style>" in html()


# --- provenance: the things a screenshot would lose --------------------------

def test_it_says_when_it_was_generated():
    assert "Generated 12 August 2026" in html()


def test_it_names_the_engine_that_produced_it():
    assert "Organized by Groq" in html()


def test_the_local_engine_is_named_as_what_it_is():
    # If a keyword-matched result gets printed and posted, the page has to say
    # so. It is much worse than the model and the reader cannot tell by looking.
    assert "the local rule-based engine" in html(provider="local")


def test_every_entry_quotes_the_line_it_came_from():
    page = html(item(source_excerpt="passed the final roof inspection"))

    assert "passed the final roof inspection" in page


def test_it_explains_how_to_check_it():
    page = html()

    assert "quotes the line it came from" in page
    assert "not been reviewed by a person" in page


# --- what it must not hide ---------------------------------------------------

def test_warnings_are_printed_not_hidden():
    # On screen they live behind an expander. In a document that leaves the
    # building they have to be on the page.
    page = html(warnings=["item_002: dropped the date 2026-08-03."])

    assert "What the organizer flagged" in page
    assert "dropped the date 2026-08-03" in page


def test_an_undated_entry_says_so_in_words():
    page = html(item(date=None))

    assert "no date given" in page


def test_the_undated_note_explains_it_was_not_an_accident():
    page = html(item(date=None))

    assert "no date was written on that line" in page


def test_a_flagged_item_carries_its_flag_into_the_document():
    page = html(item(flags=["safety_review"]))

    assert "safety review" in page


def test_an_outstanding_action_is_marked_outstanding():
    page = html(item(action_required=True, action="Chase the supplier"))

    assert "Outstanding: Chase the supplier" in page


# --- model text is never markup ----------------------------------------------

def test_markup_in_a_title_is_escaped():
    page = html(item(title="<script>alert(1)</script>"))

    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page


def test_markup_in_a_warning_is_escaped():
    page = html(warnings=["<img src=x onerror=alert(1)>"])

    assert "<img src=x" not in page


def test_markup_in_the_project_name_is_escaped_in_the_title_tag():
    page = html(project_name="<script>x</script>")

    assert "<title>Job record — &lt;script&gt;" in page


# --- the aggregate's action list wins ----------------------------------------

def test_the_summary_action_list_is_used_when_there_is_one():
    # summarize() has already collapsed duplicates and added the actions the
    # guardrails derived, so it is a better list than the model's own.
    page = html(summary={"open_actions": ["Review the safety item: strap end"]})

    assert "Review the safety item: strap end" in page


def test_the_model_actions_are_used_when_there_is_no_summary():
    page = html(open_actions=["Call the client back"])

    assert "Call the client back" in page


# --- small things ------------------------------------------------------------

def test_a_date_reads_as_a_person_would_write_it():
    assert format_date("2026-08-05") == "5 Aug 2026"


def test_a_missing_date_formats_to_nothing():
    assert format_date(None) == ""


def test_a_job_with_no_client_says_so_rather_than_leaving_a_gap():
    page = html(client_name=None, property_address=None)

    assert "No client or address was given in the source" in page


def test_an_amount_is_shown_with_its_currency():
    page = html(item(category="receipt", amount=142.75, currency="USD"))

    assert "142.75 USD" in page
