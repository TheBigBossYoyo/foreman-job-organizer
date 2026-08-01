import csv
import json

from src import batch
from src.organizer import JobOrganizerError
from src.schema import JobOrganizationResult


def make_result(summary="ok"):
    return JobOrganizationResult(
        items=[{
            "item_id": "item_001",
            "category": "photo",
            "title": "A photo",
            "summary": "Someone sent a photo.",
            "source_excerpt": "photo attached",
        }],
        open_actions=["Chase the supplier"],
        overall_summary=summary,
        warnings=["No date was given."],
    )


def write_samples(tmp_path, names):
    samples = tmp_path / "samples"
    samples.mkdir()
    for name in names:
        (samples / name).write_text(f"contents of {name}", encoding="utf-8")
    return samples, tmp_path / "outputs"


def test_writes_one_json_per_sample_and_one_log_row(tmp_path, monkeypatch):
    samples, outputs = write_samples(tmp_path, ["a_first.txt", "b_second.txt"])
    monkeypatch.setattr(batch, "organize_job_stream", lambda text: make_result())

    rows = batch.process_folder(samples, outputs)

    assert [row["status"] for row in rows] == ["pass", "pass"]
    assert json.loads((outputs / "a_first.json").read_text(encoding="utf-8"))["overall_summary"] == "ok"
    assert (outputs / "b_second.json").exists()

    with (outputs / "results_log.csv").open(encoding="utf-8") as log:
        logged = list(csv.DictReader(log))

    assert [row["sample"] for row in logged] == ["a_first.txt", "b_second.txt"]
    assert logged[0]["notes"] == "No date was given."
    assert list(logged[0]) == batch.LOG_COLUMNS


def test_one_bad_sample_does_not_stop_the_others(tmp_path, monkeypatch):
    samples, outputs = write_samples(tmp_path, ["a_good.txt", "b_bad.txt"])

    def flaky(text):
        if "b_bad" in text:
            raise JobOrganizerError("the model returned nonsense")
        return make_result()

    monkeypatch.setattr(batch, "organize_job_stream", flaky)

    rows = batch.process_folder(samples, outputs)

    assert [row["status"] for row in rows] == ["pass", "failed"]
    assert "nonsense" in rows[1]["notes"]

    # The good sample still has to land, and the bad one must not leave a
    # half-written file behind for the scorer to pick up later.
    assert (outputs / "a_good.json").exists()
    assert not (outputs / "b_bad.json").exists()


def test_an_empty_folder_still_writes_a_log(tmp_path, monkeypatch):
    samples, outputs = write_samples(tmp_path, [])
    monkeypatch.setattr(batch, "organize_job_stream", lambda text: make_result())

    assert batch.process_folder(samples, outputs) == []
    assert (outputs / "results_log.csv").exists()
