"""Score the batch outputs against the hand-written expected answers.

The Week 3 number was counted by reading the JSON files, which takes an evening
and cannot be repeated after a prompt change. This does the same count in code.

Three header fields per sample, then five per item. Four of the five are
compared against data/expected. The fifth, source_excerpt, is compared against
the sample text instead, because the exact wording is the model's choice but an
excerpt that is not in the input is a quote it made up.
"""

import argparse
import json
from pathlib import Path

from .text import normalize

HEADER_FIELDS = ["project_name", "client_name", "property_address"]
ITEM_FIELDS = ["category", "date", "action_required", "amount", "source_excerpt"]


def excerpt_is_grounded(excerpt, source):
    """True when the quoted fragment really appears in the sample text."""
    if not excerpt:
        return False
    return normalize(excerpt) in normalize(source)


def amounts_match(expected_item, actual_item):
    """Amount and currency are one field: a number without its currency is wrong."""
    expected_amount = expected_item.get("amount")
    actual_amount = actual_item.get("amount")

    if expected_amount is None or actual_amount is None:
        if expected_amount != actual_amount:
            return False
    elif round(expected_amount, 2) != round(actual_amount, 2):
        return False

    return expected_item.get("currency") == actual_item.get("currency")


def score_item(expected_item, actual_item, source):
    return {
        "category": expected_item["category"] == actual_item.get("category"),
        "date": expected_item["date"] == actual_item.get("date"),
        "action_required": expected_item["action_required"] == actual_item.get("action_required"),
        "amount": amounts_match(expected_item, actual_item),
        "source_excerpt": excerpt_is_grounded(actual_item.get("source_excerpt"), source),
    }


def score_sample(expected, actual, source):
    """Return (correct, total, misses) for one sample."""
    correct = 0
    total = 0
    misses = []

    for field in HEADER_FIELDS:
        total += 1
        if expected.get(field) == actual.get(field):
            correct += 1
        else:
            misses.append(f"{field}: expected {expected.get(field)!r}, got {actual.get(field)!r}")

    expected_items = expected["items"]
    actual_items = actual.get("items", [])

    # Items are lined up by position. If the model split the input differently
    # the leftovers score zero, which is the honest outcome: a timeline with the
    # wrong number of events is wrong even when the words in it are fine.
    for index in range(max(len(expected_items), len(actual_items))):
        label = f"item_{index + 1:03d}"
        total += len(ITEM_FIELDS)

        if index >= len(expected_items):
            misses.append(f"{label}: extra item not in the expected answer")
            continue
        if index >= len(actual_items):
            misses.append(f"{label}: missing, the model did not produce this item")
            continue

        for field, matched in score_item(expected_items[index], actual_items[index], source).items():
            if matched:
                correct += 1
            elif field == "source_excerpt":
                misses.append(f"{label}.source_excerpt: quotes text that is not in the sample")
            else:
                misses.append(
                    f"{label}.{field}: expected "
                    f"{expected_items[index][field]!r}, got {actual_items[index].get(field)!r}"
                )

    return correct, total, misses


def score_all(expected_dir="data/expected", output_dir="outputs", sample_dir="data/samples"):
    expected_path = Path(expected_dir)
    output_path = Path(output_dir)
    sample_path = Path(sample_dir)

    report = []
    for expected_file in sorted(expected_path.glob("*.json")):
        stem = expected_file.stem
        actual_file = output_path / f"{stem}.json"
        sample_file = sample_path / f"{stem}.txt"

        if not actual_file.exists():
            report.append({
                "sample": stem, "correct": 0, "total": 0, "misses": ["no output file, run src.batch first"],
            })
            continue

        correct, total, misses = score_sample(
            json.loads(expected_file.read_text(encoding="utf-8")),
            json.loads(actual_file.read_text(encoding="utf-8")),
            sample_file.read_text(encoding="utf-8"),
        )
        report.append({"sample": stem, "correct": correct, "total": total, "misses": misses})

    return report


def main():
    parser = argparse.ArgumentParser(description="Score the batch outputs against data/expected.")
    parser.add_argument("--expected", default="data/expected")
    parser.add_argument("--output", default="outputs")
    parser.add_argument("--samples", default="data/samples")
    args = parser.parse_args()

    report = score_all(args.expected, args.output, args.samples)

    for row in report:
        print(f"\n{row['sample']}: {row['correct']}/{row['total']}")
        for miss in row["misses"]:
            print(f"  - {miss}")

    correct = sum(row["correct"] for row in report)
    total = sum(row["total"] for row in report)
    clean = sum(1 for row in report if not row["misses"])
    percent = (correct / total * 100) if total else 0

    print(f"\nField accuracy: {correct}/{total} ({percent:.0f}%)")
    print(f"Samples with no errors: {clean}/{len(report)}")


if __name__ == "__main__":
    main()
