"""Checks on folding a repeated event into one item.

The rule being tested is not "did it fold correctly" — that is a judgement the
scorer measures. It is the narrower one: a restatement the model returns has to
be a line that exists in the input. The model is allowed to decide two lines are
the same event; it is not allowed to quote a line nobody wrote.
"""

from src.restatements import ground_restatements, is_quoted_in, mention_count
from src.schema import JobItem, JobOrganizationResult

SOURCE = """Project: Hollis roof and gutters

2026-08-05 - passed the final roof inspection, the inspector signed off
the roof inspection went through, all good on the sign-off
84 Lumber dropped the gutter stock and downspouts this morning
"""


def item(**overrides):
    base = {
        "item_id": "item_001",
        "category": "inspection",
        "title": "Final roof inspection",
        "summary": "The roof passed its final inspection.",
        "source_excerpt": "passed the final roof inspection, the inspector signed off",
    }
    return JobItem(**{**base, **overrides})


def result_with(*items):
    return JobOrganizationResult(items=list(items), overall_summary="A roof job.")


def test_a_restatement_written_in_the_input_is_kept():
    result = ground_restatements(
        result_with(item(restatements=["the roof inspection went through, all good on the sign-off"])),
        SOURCE,
    )

    assert result.items[0].restatements == [
        "the roof inspection went through, all good on the sign-off"
    ]
    assert not result.warnings


def test_a_restatement_that_is_not_in_the_input_is_dropped():
    # The whole point of the field. A folded line has to be a line.
    result = ground_restatements(
        result_with(item(restatements=["the inspector also checked the gutters"])),
        SOURCE,
    )

    assert result.items[0].restatements == []
    assert any("not written anywhere in the input" in w for w in result.warnings)


def test_the_warning_names_the_item_and_quotes_what_was_dropped():
    result = ground_restatements(
        result_with(item(restatements=["the inspector also checked the gutters"])),
        SOURCE,
    )

    warning = result.warnings[0]
    assert "item_001" in warning
    assert "the inspector also checked the gutters" in warning


def test_quoting_the_items_own_line_back_is_not_a_second_mention():
    excerpt = "passed the final roof inspection, the inspector signed off"
    result = ground_restatements(result_with(item(restatements=[excerpt])), SOURCE)

    assert result.items[0].restatements == []
    assert any("repeats a line already on this item" in w for w in result.warnings)


def test_the_same_restatement_twice_is_recorded_once():
    line = "the roof inspection went through, all good on the sign-off"
    result = ground_restatements(result_with(item(restatements=[line, line])), SOURCE)

    assert result.items[0].restatements == [line]


def test_a_fragment_too_short_to_identify_an_event_is_dropped():
    # "all good" appears in three samples. A match that short is a coincidence,
    # not evidence that two lines describe the same thing.
    result = ground_restatements(result_with(item(restatements=["all good"])), SOURCE)

    assert result.items[0].restatements == []
    assert any("too short" in w for w in result.warnings)


def test_an_item_with_no_restatements_is_left_alone():
    result = ground_restatements(result_with(item()), SOURCE)

    assert result.items[0].restatements == []
    assert not result.warnings


def test_without_the_input_text_nothing_is_dropped_for_being_absent():
    # There is nothing to check against, so inventing a verdict would be worse
    # than keeping what we were given.
    invented = "the inspector also checked the gutters"
    result = ground_restatements(result_with(item(restatements=[invented])))

    assert result.items[0].restatements == [invented]


def test_a_good_and_a_bad_restatement_on_one_item_keep_the_good_one():
    result = ground_restatements(
        result_with(item(restatements=[
            "the roof inspection went through, all good on the sign-off",
            "the inspector also checked the gutters",
        ])),
        SOURCE,
    )

    assert result.items[0].restatements == [
        "the roof inspection went through, all good on the sign-off"
    ]
    assert len(result.warnings) == 1


def test_restatements_do_not_leak_between_items():
    first = item(item_id="item_001", restatements=["the inspector also checked the gutters"])
    second = item(
        item_id="item_002",
        category="delivery",
        source_excerpt="84 Lumber dropped the gutter stock and downspouts this morning",
    )
    result = ground_restatements(result_with(first, second), SOURCE)

    assert result.items[1].restatements == []
    assert all("item_002" not in warning for warning in result.warnings)


def test_is_quoted_in_ignores_spacing_and_case():
    assert is_quoted_in("The Roof   Inspection Went Through", SOURCE)


def test_mention_count_counts_the_item_itself():
    assert mention_count([]) == 1
    assert mention_count(["a"]) == 2
    assert mention_count(None) == 1
