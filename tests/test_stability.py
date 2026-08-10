"""Tests for the run-to-run measurement, and for the test set itself.

No API call happens here: organize_job_stream is replaced with a stub that
returns whatever the test wants, so the arithmetic can be checked without
spending a call or depending on what the model does today.
"""

import json

import pytest

from src import stability
from src.schema import JobOrganizationResult

SAMPLE_DIR = "data/samples"
EXPECTED_DIR = "data/expected"


def fake_result(categories):
    """A result with one item per category given."""
    return JobOrganizationResult.model_validate({
        "project_name": "A job",
        "client_name": None,
        "property_address": None,
        "items": [
            {
                "item_id": f"item_{index + 1:03d}",
                "category": category,
                "title": "An item",
                "summary": "Something happened.",
                "source_excerpt": "something",
            }
            for index, category in enumerate(categories)
        ],
        "overall_summary": "A job.",
    })


def test_a_sample_that_splits_the_same_way_every_run_is_reported_as_stable(monkeypatch, tmp_path):
    sample = tmp_path / "samples"
    expected = tmp_path / "expected"
    sample.mkdir()
    expected.mkdir()
    (sample / "x.txt").write_text("something", encoding="utf-8")
    (expected / "x.json").write_text(json.dumps({
        "project_name": "A job", "client_name": None, "property_address": None,
        "items": [{"category": "other", "date": None, "action_required": False,
                   "amount": None, "currency": None}],
    }), encoding="utf-8")

    monkeypatch.setattr(stability, "organize_job_stream",
                        lambda text: fake_result(["other"]))

    rows = stability.measure(runs=3, sample_dir=str(sample), expected_dir=str(expected))

    assert rows[0]["item_counts"] == [1, 1, 1]
    assert rows[0]["segmentation_stable"] is True


def test_a_sample_that_splits_differently_is_reported_as_unstable(monkeypatch, tmp_path):
    # The finding this module exists for: one extra item shifts every later
    # field, so the score moves far more than a single field would.
    sample = tmp_path / "samples"
    expected = tmp_path / "expected"
    sample.mkdir()
    expected.mkdir()
    (sample / "x.txt").write_text("something", encoding="utf-8")
    (expected / "x.json").write_text(json.dumps({
        "project_name": "A job", "client_name": None, "property_address": None,
        "items": [{"category": "other", "date": None, "action_required": False,
                   "amount": None, "currency": None}],
    }), encoding="utf-8")

    splits = iter([["other"], ["other", "other"], ["other"]])
    monkeypatch.setattr(stability, "organize_job_stream",
                        lambda text: fake_result(next(splits)))

    rows = stability.measure(runs=3, sample_dir=str(sample), expected_dir=str(expected))

    assert rows[0]["item_counts"] == [1, 2, 1]
    assert rows[0]["segmentation_stable"] is False


def test_a_sample_with_no_answer_key_is_skipped_rather_than_scored(monkeypatch, tmp_path):
    sample = tmp_path / "samples"
    expected = tmp_path / "expected"
    sample.mkdir()
    expected.mkdir()
    (sample / "orphan.txt").write_text("something", encoding="utf-8")

    monkeypatch.setattr(stability, "organize_job_stream",
                        lambda text: fake_result(["other"]))

    assert stability.measure(runs=1, sample_dir=str(sample), expected_dir=str(expected)) == []


# --- the test set itself -------------------------------------------------------

def sample_stems():
    from pathlib import Path
    return sorted(path.stem for path in Path(SAMPLE_DIR).glob("*.txt"))


def test_the_test_set_is_the_size_week_4_asked_for():
    assert len(sample_stems()) >= 8


@pytest.mark.parametrize("stem", sample_stems())
def test_every_sample_has_an_answer_key(stem):
    # score_all walks data/expected, so a sample with no key is silently never
    # scored. That is the quietest way for the accuracy number to become wrong.
    from pathlib import Path

    assert (Path(EXPECTED_DIR) / f"{stem}.json").exists()


@pytest.mark.parametrize("stem", sample_stems())
def test_every_answer_key_is_well_formed(stem):
    from pathlib import Path
    from src.schema import Category

    key = json.loads((Path(EXPECTED_DIR) / f"{stem}.json").read_text(encoding="utf-8"))
    allowed = set(Category.__args__)

    assert key["items"], stem
    for item in key["items"]:
        assert item["category"] in allowed, item["category"]
        assert set(item) == {"category", "date", "action_required", "amount", "currency"}
        assert isinstance(item["action_required"], bool)
        if item["amount"] is not None:
            assert item["currency"], "an amount without a currency is half a fact"
