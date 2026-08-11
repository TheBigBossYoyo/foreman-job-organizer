"""Render checks for the Streamlit page.

app.py was the one file with no test on it, which is awkward given how much of
this project's behaviour a reader only ever meets through it. These run the
page headlessly with Streamlit's own test harness. No model is called: the
button is never clicked, and the result is put into session state directly.

They are deliberately about behaviour that would be wrong rather than merely
different, so ordinary styling changes do not break them.
"""

import json

import pytest
from streamlit.testing.v1 import AppTest

from app import is_restatement
from src.schema import JobOrganizationResult

RESULT = {
    "project_name": "Alvarez kitchen renovation",
    "client_name": "Sofia Alvarez",
    "property_address": "18 Cedar Lane",
    "items": [
        {
            "item_id": "item_001",
            "category": "contractor_update",
            "date": "2026-07-21",
            "title": "Cabinet removal",
            "summary": "The crew took the old cabinets out and cleared the debris.",
            "source_excerpt": "2026-07-21 - Crew completed cabinet removal.",
        },
        {
            "item_id": "item_002",
            "category": "receipt",
            "date": None,
            "amount": 142.75,
            "currency": "USD",
            "title": "Drywall and screws receipt",
            "summary": "Materials bought at BuildRight.",
            "source_excerpt": "Receipt: BuildRight, drywall and screws, $142.75.",
        },
        {
            "item_id": "item_003",
            "category": "receipt",
            "date": None,
            "amount": 118.90,
            "currency": "TND",
            "title": "Primer receipt",
            "summary": "Primer bought locally.",
            "source_excerpt": "paid 118.90 TND for the primer",
        },
    ],
    "open_actions": ["Call the client back"],
    "overall_summary": "A kitchen job.",
    "warnings": ["item_002: no date was written on this line."],
    "provider": "groq",
}


def run_with_result(result=None):
    """Render the page with a finished result already in session state."""
    app = AppTest.from_file("app.py", default_timeout=30)
    app.session_state["result"] = result if result is not None else RESULT
    return app.run()


def page_html(app):
    return "".join(element.value for element in app.markdown)


def test_the_page_renders_with_no_result_and_no_key():
    app = AppTest.from_file("app.py", default_timeout=30).run()

    assert not app.exception


def test_a_result_renders_without_error():
    app = run_with_result()

    assert not app.exception


def test_every_currency_is_shown_not_just_the_first_ones():
    # A dropped total is worse than an ugly one: there is nothing on screen to
    # say a number is missing.
    html = page_html(run_with_result())

    assert "142.75" in html and "usd" in html
    assert "118.90" in html and "tnd" in html


def test_the_timeline_is_in_source_order_with_the_undated_items_in_place():
    html = page_html(run_with_result())
    positions = [html.index(title) for title in
                 ["Cabinet removal", "Drywall and screws receipt", "Primer receipt"]]

    assert positions == sorted(positions)


def test_an_undated_item_says_so_rather_than_showing_a_gap():
    assert "no date" in page_html(run_with_result())


def test_the_local_engine_is_called_out_as_unreliable():
    app = run_with_result({**RESULT, "provider": "local"})

    assert any("keyword" in error.value for error in app.error)


def test_a_model_answer_carries_no_such_warning():
    assert not run_with_result().error


def test_markup_in_model_output_is_escaped_rather_than_rendered():
    # The item text came from a model reading arbitrary pasted input, so it is
    # never markup.
    hostile = {**RESULT, "items": [{
        **RESULT["items"][0],
        "title": "<script>alert(1)</script>",
        "summary": "<img src=x onerror=alert(1)>",
    }]}

    html = page_html(run_with_result(hostile))

    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_each_open_action_gets_its_own_checkbox():
    app = run_with_result()

    assert [box.label for box in app.checkbox] == ["Call the client back"]


def test_the_same_action_listed_twice_is_shown_once():
    # summarize() collapses them, so the page never has to draw a duplicate.
    # Worth pinning: Streamlit raises on duplicate widget keys, and a second
    # identical line would be a job to do twice rather than one job.
    app = run_with_result({**RESULT, "open_actions": ["Call back", "Call back"]})

    assert not app.exception
    assert [box.label for box in app.checkbox] == ["Call back"]


def test_actions_that_differ_each_get_a_checkbox():
    app = run_with_result({**RESULT, "open_actions": ["Call back", "Order tile"]})

    assert [box.label for box in app.checkbox] == ["Call back", "Order tile"]


def test_the_fixture_is_a_valid_result():
    # If this drifts from the real schema the tests above stop meaning anything.
    assert JobOrganizationResult.model_validate(RESULT).items


@pytest.mark.parametrize("summary, excerpt, expected", [
    ("Crew completed cabinet removal", "2026-07-21 - Crew completed cabinet removal.", True),
    ("The crew took the old cabinets out and cleared the debris.",
     "2026-07-21 - Crew completed cabinet removal.", False),
])
def test_a_summary_that_only_repeats_the_source_is_recognised(summary, excerpt, expected):
    assert is_restatement(summary, excerpt) is expected


def test_the_download_payload_is_the_result_that_is_on_screen():
    app = run_with_result()

    assert json.loads(json.dumps(app.session_state["result"])) == RESULT


# --- priority and flags ------------------------------------------------------

def with_first_item(**overrides):
    """RESULT with the first item changed, everything else untouched."""
    items = [{**RESULT["items"][0], **overrides}, *RESULT["items"][1:]]
    return {**RESULT, "items": items}


def test_an_urgent_item_is_marked_as_urgent():
    # The safety guardrail raises injuries to urgent. If the page does not show
    # it, the guardrail may as well not have run.
    # Checked on the row's own class, not on the word: the stylesheet is part of
    # this page too, so "urgent" appears in it either way.
    html = page_html(run_with_result(with_first_item(priority="urgent")))

    assert 'class="jo-row urgent"' in html
    assert '<span class="jo-prio urgent">urgent</span>' in html


def test_an_ordinary_item_gets_no_urgent_styling():
    html = page_html(run_with_result(with_first_item(priority="low")))

    assert 'class="jo-row urgent"' not in html


def test_an_ordinary_priority_is_not_announced():
    # Every item is medium by default. Printing it on all of them is a column
    # of identical words.
    html = page_html(run_with_result(with_first_item(priority="medium")))

    assert "medium" not in html.lower()


def test_a_safety_flag_is_styled_as_an_alarm():
    html = page_html(run_with_result(with_first_item(flags=["safety_review"])))

    assert 'class="jo-flag"' in html


def test_low_confidence_is_shown_but_not_as_an_alarm():
    # It is context. Sharing a style with a possible injury overstates it.
    html = page_html(run_with_result(with_first_item(flags=["low_confidence"])))

    assert "low confidence" in html
    assert 'class="jo-flag quiet"' in html


def test_an_alarm_and_a_quiet_flag_on_one_item_keep_their_own_styles():
    html = page_html(run_with_result(
        with_first_item(flags=["low_confidence", "safety_review"])
    ))

    assert 'class="jo-flag"' in html
    assert 'class="jo-flag quiet"' in html
