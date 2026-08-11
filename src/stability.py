"""Measure how much the same input moves between identical runs.

"118 ± 1" came from three runs that scored 117, 118, 118. It only holds while
the model splits the stream the same way each time, and it does not always. On
03_tricky_bathroom this line is one item on some runs and two on others:

    7/27 demo done. opened up the shower wall and there is moisture behind it

The scorer matches items by position, so an extra item shifts every later field
and changes the denominator. The percentage is then not comparable between runs.

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
    correct, total, _, _ = score_sample(expected, result, source)
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
        # A sample that splits differently between runs cannot have a stable
        # percentage, however many times the scorer is re-run.
        print(f"* item count changed between runs: {', '.join(unstable)}")
    else:
        print("Item counts were identical across runs for every sample.")

    all_scores = [score for row in rows for score in row["scores"]]
    if len(all_scores) > 1:
        print(f"Field spread across all runs: {min(all_scores)}-{max(all_scores)} "
              f"per sample, stdev {statistics.stdev(all_scores):.1f}")

    # Make the denominator explicit. Ten runs of one sample is ten data points;
    # ten runs of eight samples is eighty. State which one the numbers came from.
    total_orgs = sum(len(row["scores"]) for row in rows)
    print(f"\nEvidence base: {args.runs} run(s) x {len(rows)} sample(s) = {total_orgs} organizations.")
    if len(rows) <= 1:
        print("  One sample is thin — drop --sample to measure the whole set.")


if __name__ == "__main__":
    main()
