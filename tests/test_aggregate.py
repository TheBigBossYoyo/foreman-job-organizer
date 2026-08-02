from src.aggregate import (
    derived_actions,
    ordered_items,
    spend_by_currency,
    summarize,
    timeline,
)
from src.schema import JobItem, JobOrganizationResult


def make_item(**overrides):
    base = {
        "item_id": "item_001",
        "category": "contractor_update",
        "title": "An item",
        "summary": "Something happened.",
        "source_excerpt": "something happened",
    }
    return JobItem(**{**base, **overrides})


def make_result(items, open_actions=None):
    return JobOrganizationResult(
        items=items,
        open_actions=open_actions or [],
        overall_summary="A job.",
    )


def test_timeline_orders_by_date():
    rows = timeline([
        make_item(item_id="item_001", date="2026-07-24"),
        make_item(item_id="item_002", date="2026-07-21"),
    ])

    assert [row["date"] for row in rows] == ["2026-07-21", "2026-07-24"]


def test_an_undated_item_stays_between_the_dated_ones_around_it():
    # The receipt sits under the 21st and above the 22nd in the input, so that
    # is when it happened, even though its line carries no date.
    rows = timeline([
        make_item(item_id="item_001", date="2026-07-21", title="Cabinet removal"),
        make_item(item_id="item_002", date=None, title="Receipt"),
        make_item(item_id="item_003", date="2026-07-22", title="Delivery"),
        make_item(item_id="item_004", date=None, title="Client approval"),
    ])

    assert [row["title"] for row in rows] == [
        "Cabinet removal", "Receipt", "Delivery", "Client approval"
    ]


def test_placing_an_undated_item_does_not_give_it_a_date():
    rows = timeline([
        make_item(item_id="item_001", date="2026-07-21", title="Dated"),
        make_item(item_id="item_002", date=None, title="Undated"),
    ])

    assert rows[1]["date"] is None


def test_an_undated_item_before_any_date_stays_at_the_top():
    order = ordered_items([
        make_item(item_id="item_001", date=None, title="Opening note"),
        make_item(item_id="item_002", date="2026-07-21", title="Dated"),
    ])

    assert [item.title for item in order] == ["Opening note", "Dated"]


def test_undated_items_keep_their_input_order():
    rows = timeline([
        make_item(item_id="item_001", date=None, title="First"),
        make_item(item_id="item_002", date=None, title="Second"),
    ])

    assert [row["title"] for row in rows] == ["First", "Second"]


def test_dated_items_still_sort_when_the_model_emits_them_out_of_order():
    order = ordered_items([
        make_item(item_id="item_001", date="2026-07-24", title="Later"),
        make_item(item_id="item_002", date="2026-07-21", title="Earlier"),
    ])

    assert [item.title for item in order] == ["Earlier", "Later"]


def test_currencies_are_totalled_separately():
    # Adding dinars to dollars would invent a number that is not in the input.
    totals = spend_by_currency([
        make_item(item_id="item_001", amount=142.75, currency="USD"),
        make_item(item_id="item_002", amount=100.00, currency="USD"),
        make_item(item_id="item_003", amount=118.90, currency="TND"),
    ])

    assert totals == {"TND": 118.90, "USD": 242.75}


def test_items_with_no_amount_do_not_affect_the_total():
    assert spend_by_currency([make_item(amount=None)]) == {}


def test_a_flagged_item_produces_the_action_it_implies():
    actions = derived_actions([
        make_item(item_id="item_001", title="Hand injury", flags=["safety_review"]),
        make_item(item_id="item_002", title="Paint receipt", flags=["missing_amount"]),
    ])

    assert "Review the safety item: Hand injury" in actions
    assert "Find the missing amount for: Paint receipt" in actions


def test_the_models_own_actions_come_first_and_are_not_duplicated():
    result = make_result(
        [make_item(flags=["safety_review"], title="Hand injury")],
        open_actions=["Call the client back"],
    )

    actions = summarize(result)["open_actions"]

    assert actions[0] == "Call the client back"
    assert len(actions) == len(set(actions))


def test_summarize_counts_what_needs_a_human():
    result = make_result([
        make_item(item_id="item_001", date="2026-07-21", flags=[]),
        make_item(item_id="item_002", date=None, flags=["no_date"]),
        make_item(item_id="item_003", date=None, flags=["no_date", "low_confidence"]),
    ])

    summary = summarize(result)

    assert summary["item_count"] == 3
    assert summary["needs_review"] == 2
    assert summary["undated"] == 2
    assert summary["date_range"] == {"start": "2026-07-21", "end": "2026-07-21"}


def test_summarize_handles_a_job_with_no_dates_at_all():
    summary = summarize(make_result([make_item(date=None)]))

    assert summary["date_range"] == {"start": None, "end": None}
    assert summary["timeline"][0]["date"] is None
