"""Measure how much the same input moves between identical runs.

PROJECT_NOTES has said "118 ± 1" since Week 3, taken from three scoring runs
that came out 117, 118, 118. That number only describes the runs where the
model split the stream the same way each time.

It does not always. On 03_tricky_bathroom the line

    7/27 demo done. opened up the shower wall and there is moisture behind it

is one item on some runs and two on others. When that happens the item count
changes, the scorer lines items up by position, and every field after the split
shifts by one. A single segmentation difference therefore moves the score by
far more than a single field would, and it moves the denominator too, so the
percentage is not comparable between runs.

This runs each sample several times and reports the spread, so the claim about
reproducibility is measured rather than assumed.

    python -m src.stability --runs 3
    python -m src.stability --runs 5 --sample 03_tricky_bathroom
"""

import argparse
import json
import statistics
from pathlib import Path

from .organizer import organize_job_stream
from .score import score_sample


def run_once(sample_path, expected_path):
    """Organize one sample and score it. Returns (item_count, correct, total)."""
    source = sample_path.read_text(encoding="utf-8")
    result = organize_job_stream(source).model_dump()
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    correct, total, _ = score_sample(expected, result, source)
    return len(result["items"]), correct, total


def measure(runs=3, sample_dir="data/samples", expected_dir="data/expected", only=None):
    """Run every sample `runs` times and collect what changed between them."""
    rows = []

    for sample_path in sorted(Path(sample_dir).glob("*.txt")):
        stem = sample_path.stem
        if only and only != stem:
            continue

        expected_path = Path(expected_dir) / f"{stem}.json"
        if not expected_path.exists():
            continue

        counts, scores, totals = [], [], []
        for _ in range(runs):
            count, correct, total = run_once(sample_path, expected_path)
            counts.append(count)
            scores.append(correct)
            totals.append(total)

        rows.append({
            "sample": stem,
            "item_counts": counts,
            "scores": scores,
            "totals": totals,
            "segmentation_stable": len(set(counts)) == 1,
        })

    return rows


def main():
    parser = argparse.ArgumentParser(description="Measure run-to-run variation.")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--sample", default=None, help="one sample stem, e.g. 03_tricky_bathroom")
    args = parser.parse_args()

    rows = measure(runs=args.runs, only=args.sample)

    print(f"{args.runs} runs per sample\n")
    unstable = []

    for row in rows:
        counts = row["item_counts"]
        scores = row["scores"]
        spread = max(scores) - min(scores)
        mark = " " if row["segmentation_stable"] else "*"
        print(
            f"{mark} {row['sample']:<22} items {counts}  "
            f"scored {scores} of {row['totals']}  spread {spread}"
        )
        if not row["segmentation_stable"]:
            unstable.append(row["sample"])

    print()
    if unstable:
        # This is the finding, not a footnote. A sample that splits differently
        # between runs cannot have a stable percentage, however many times the
        # scorer is re-run.
        print(f"* item count changed between runs: {', '.join(unstable)}")
    else:
        print("Item counts were identical across runs for every sample.")

    all_scores = [score for row in rows for score in row["scores"]]
    if len(all_scores) > 1:
        print(f"Field spread across all runs: {min(all_scores)}-{max(all_scores)} "
              f"per sample, stdev {statistics.stdev(all_scores):.1f}")


if __name__ == "__main__":
    main()
