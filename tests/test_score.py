from src.score import (
    align_items,
    amounts_match,
    describe_shape,
    excerpt_is_grounded,
    normalize,
    score_sample,
)

SOURCE = """Project: Test job
2026-07-21 - Crew removed the old cabinets.
Receipt: BuildRight, screws, $142.75.
"""


def make_docs(expected_items, actual_items):
    """Build a matching expected/actual pair whose header fields all agree."""
    header = {"project_name": "Test job", "client_name": None, "property_address": None}
    return {**header, "items": expected_items}, {**header, "items": actual_items}


def cabinets_expected(**overrides):
    item = {
        "category": "contractor_update",
        "date": "2026-07-21",
        "action_required": False,
        "amount": None,
        "currency": None,
    }
    return {**item, **overrides}


def cabinets_actual(**overrides):
    item = cabinets_expected()
    item["source_excerpt"] = "Crew removed the old cabinets."
    return {**item, **overrides}


def test_normalize_collapses_whitespace_and_curly_quotes():
    assert normalize("  The  “quote”\nwraps ") == 'the "quote" wraps'


def test_excerpt_found_in_the_sample():
    assert excerpt_is_grounded("Crew removed the old cabinets.", SOURCE)


def test_excerpt_still_found_when_the_model_rewraps_it():
    # The model often folds a long quote onto two lines. That is not an error.
    assert excerpt_is_grounded("Crew removed\n  the old cabinets.", SOURCE)


def test_invented_excerpt_is_flagged():
    assert not excerpt_is_grounded("Crew repainted the ceiling.", SOURCE)


def test_empty_excerpt_is_flagged():
    assert not excerpt_is_grounded("", SOURCE)


def test_amount_needs_its_currency_to_match():
    expected = {"amount": 142.75, "currency": "USD"}
    assert amounts_match(expected, {"amount": 142.75, "currency": "USD"})
    assert not amounts_match(expected, {"amount": 142.75, "currency": "EUR"})
    assert not amounts_match(expected, {"amount": None, "currency": "USD"})


def screws_expected(**overrides):
    item = {
        "category": "receipt",
        "date": None,
        "action_required": False,
        "amount": 142.75,
        "currency": "USD",
    }
    return {**item, **overrides}


def screws_actual(**overrides):
    item = screws_expected()
    item["source_excerpt"] = "Receipt: BuildRight, screws, $142.75."
    return {**item, **overrides}


def test_a_correct_sample_scores_full_marks():
    expected, actual = make_docs([cabinets_expected()], [cabinets_actual()])
    correct, total, misses, shape = score_sample(expected, actual, SOURCE)

    assert (correct, total) == (8, 8)
    assert misses == []
    assert shape == {"segmentation": 0, "field": 0}


def test_an_inherited_date_is_counted_wrong():
    expected, actual = make_docs(
        [cabinets_expected(date=None)],
        [cabinets_actual(date="2026-07-21")],
    )
    correct, total, misses, shape = score_sample(expected, actual, SOURCE)

    assert (correct, total) == (7, 8)
    assert "item_001.date" in misses[0]
    assert shape == {"segmentation": 0, "field": 1}


def test_a_missing_item_loses_all_five_of_its_fields():
    expected, actual = make_docs([cabinets_expected(), screws_expected()], [cabinets_actual()])
    correct, total, misses, shape = score_sample(expected, actual, SOURCE)

    assert (correct, total) == (8, 13)
    assert "missing" in misses[0]
    assert shape == {"segmentation": 1, "field": 0}


def test_an_extra_item_loses_all_five_of_its_fields():
    expected, actual = make_docs([cabinets_expected()], [cabinets_actual(), screws_actual()])
    correct, total, misses, shape = score_sample(expected, actual, SOURCE)

    assert (correct, total) == (8, 13)
    assert "extra" in misses[0]
    assert shape == {"segmentation": 1, "field": 0}


# --- alignment ---------------------------------------------------------------

def test_a_dropped_first_item_does_not_shift_the_second_one():
    # The whole point of aligning. Position matching scored the screws receipt
    # against the cabinets answer and reported five wrong fields for one miss.
    expected, actual = make_docs(
        [cabinets_expected(), screws_expected()],
        [screws_actual()],
    )
    correct, total, misses, shape = score_sample(expected, actual, SOURCE)

    assert shape == {"segmentation": 1, "field": 0}
    assert (correct, total) == (8, 13)


def test_the_alignment_keeps_the_timeline_in_order():
    # Two items returned back to front is a real error, not a free reordering.
    # Aligning them out of order would score full marks on a wrong timeline.
    expected, actual = make_docs(
        [cabinets_expected(), screws_expected()],
        [screws_actual(), cabinets_actual()],
    )
    _, _, _, shape = score_sample(expected, actual, SOURCE)

    assert shape["field"] > 0 or shape["segmentation"] > 0


def test_two_items_merged_into_one_is_a_single_segmentation_error():
    merged = cabinets_actual(source_excerpt="Crew removed the old cabinets.")
    expected, actual = make_docs(
        [cabinets_expected(), screws_expected(), cabinets_expected()],
        [merged, cabinets_actual()],
    )
    _, _, _, shape = score_sample(expected, actual, SOURCE)

    assert shape["segmentation"] == 1


def test_an_empty_result_pairs_nothing():
    columns = align_items([cabinets_expected(), screws_expected()], [], SOURCE)

    assert columns == [(cabinets_expected(), None), (screws_expected(), None)]


def test_alignment_of_two_empty_lists_is_empty():
    assert align_items([], [], SOURCE) == []


def test_a_pair_that_agrees_on_nothing_still_pairs():
    # One wrong item is one substitution, not a missing item plus an extra one.
    expected, actual = make_docs(
        [cabinets_expected()],
        [screws_actual(source_excerpt="not in the sample at all", action_required=True)],
    )
    _, _, _, shape = score_sample(expected, actual, SOURCE)

    assert shape["segmentation"] == 0
    assert shape["field"] == 5


def test_describe_shape_reads_as_a_sentence():
    assert describe_shape({"segmentation": 1, "field": 3}) == "1 segmentation error, 3 field errors"
    assert describe_shape({"segmentation": 0, "field": 1}) == "1 field error"
    assert describe_shape({"segmentation": 0, "field": 0}) == "no errors"
