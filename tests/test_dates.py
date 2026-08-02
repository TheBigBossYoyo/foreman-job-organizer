from src.dates import date_is_grounded, ground_dates, parse_iso
from src.schema import JobOrganizationResult


def make_result(items):
    return JobOrganizationResult(
        items=items,
        overall_summary="A job.",
        warnings=["An existing warning."],
    )


def make_item(item_id, date, excerpt):
    return {
        "item_id": item_id,
        "category": "delivery",
        "date": date,
        "title": "An item",
        "summary": "Something happened.",
        "source_excerpt": excerpt,
    }


def test_parse_iso_rejects_anything_that_is_not_a_date():
    assert parse_iso("2026-07-23") is not None
    assert parse_iso("7/23") is None
    assert parse_iso(None) is None


def test_iso_date_written_in_the_excerpt():
    assert date_is_grounded("2026-07-23", "2026-07-23 - the shingles arrived")


def test_slashed_date_counts_even_without_a_year():
    # "7/23" is the form that made the model invent a year. It still proves the
    # date was read off this line, which is all this check is asking.
    assert date_is_grounded("2026-07-23", "7/23 shingles arrived on site")


def test_leading_zeros_and_other_separators():
    assert date_is_grounded("2026-07-23", "07-23 delivery landed")
    assert date_is_grounded("2026-07-23", "7.23 delivery landed")


def test_month_written_as_a_word():
    assert date_is_grounded("2026-07-23", "July 23 - crew finished the felt")
    assert date_is_grounded("2026-07-23", "jul 23 - crew finished the felt")
    assert date_is_grounded("2026-07-23", "23 July - crew finished the felt")
    assert date_is_grounded("2026-07-23", "23rd of July - crew finished")


def test_a_different_day_in_the_same_month_is_not_a_match():
    assert not date_is_grounded("2026-07-23", "7/24 the crew came back")


def test_an_inherited_date_is_not_grounded():
    # The date lives on the line above, not in this item's excerpt.
    assert not date_is_grounded("2026-07-23", "photo_0102.jpg - felt down, looks clean")


def test_empty_excerpt_is_not_grounded():
    assert not date_is_grounded("2026-07-23", "")


def test_ground_dates_clears_the_inherited_one_and_keeps_the_real_one():
    result = make_result([
        make_item("item_001", "2026-07-23", "7/23 - tore off the old shingles"),
        make_item("item_002", "2026-07-23", "photo_0102.jpg - felt down, looks clean"),
    ])

    ground_dates(result)

    assert result.items[0].date == "2026-07-23"
    assert result.items[1].date is None


def test_a_dropped_date_leaves_a_warning_naming_the_item():
    result = make_result([
        make_item("item_002", "2026-07-23", "photo_0102.jpg - felt down"),
    ])

    ground_dates(result)

    assert len(result.warnings) == 2
    assert "item_002" in result.warnings[1]
    assert "2026-07-23" in result.warnings[1]


def test_items_that_never_had_a_date_are_left_alone():
    result = make_result([make_item("item_001", None, "vanity is delayed")])

    ground_dates(result)

    assert result.items[0].date is None
    assert result.warnings == ["An existing warning."]
