from src.score import amounts_match, excerpt_is_grounded, normalize, score_sample

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


def test_a_correct_sample_scores_full_marks():
    expected, actual = make_docs([cabinets_expected()], [cabinets_actual()])
    correct, total, misses = score_sample(expected, actual, SOURCE)

    assert (correct, total) == (8, 8)
    assert misses == []


def test_an_inherited_date_is_counted_wrong():
    expected, actual = make_docs(
        [cabinets_expected(date=None)],
        [cabinets_actual(date="2026-07-21")],
    )
    correct, total, misses = score_sample(expected, actual, SOURCE)

    assert (correct, total) == (7, 8)
    assert "item_001.date" in misses[0]


def test_a_missing_item_loses_all_five_of_its_fields():
    expected, actual = make_docs([cabinets_expected(), cabinets_expected()], [cabinets_actual()])
    correct, total, misses = score_sample(expected, actual, SOURCE)

    assert (correct, total) == (8, 13)
    assert "missing" in misses[0]


def test_an_extra_item_loses_all_five_of_its_fields():
    expected, actual = make_docs([cabinets_expected()], [cabinets_actual(), cabinets_actual()])
    correct, total, misses = score_sample(expected, actual, SOURCE)

    assert (correct, total) == (8, 13)
    assert "extra" in misses[0]
