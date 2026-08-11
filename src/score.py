"""Score the batch outputs against the hand-written expected answers.

The Week 3 number was counted by reading the JSON files, which takes an evening
and cannot be repeated after a prompt change. This does the same count in code.

Three header fields per sample, then five per item. Four of the five are
compared against data/expected. The fifth, source_excerpt, is compared against
the sample text instead, because the exact wording is the model's choice but an
excerpt that is not in the input is a quote it made up.

Items used to be lined up by position. That was fine while the model split every
sample the way the answer key did, and misleading as soon as it did not: on
sample 06 the model merged two lines into one item, every later item shifted by
one, and the report showed fifteen wrong fields for one mistake. Position
matching cannot tell those apart, so it hid the shape of the error behind the
size of it.

Items are now aligned before they are compared. The alignment is monotonic —
timeline order is real information and reordering to get a better number would
be cheating — and a slot that pairs with nothing is reported as a segmentation
error rather than being scored against the wrong entry. The denominator does not
move: an unpaired item still costs all five of its fields.
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


# Cost of leaving an item unpaired, in fields. Less than 1, so pairing two items
# that agree on nothing still beats gapping them both — a wrong item and a
# missing item are two errors where one substitution is one. More than 0, so the
# aligner cannot pad the alignment with free gaps.
GAP_PENALTY = -0.5


def align_items(expected_items, actual_items, source):
    """Pair up expected and actual items, keeping them in timeline order.

    Returns a list of (expected_item, actual_item) columns, either side of which
    may be None when an item pairs with nothing.

    Needleman-Wunsch, scored on how many fields a pair agrees on. Monotonic by
    construction: the model can miss an event or invent one, but the order of the
    timeline it does produce is checked, not rearranged to suit the score.
    """
    rows, cols = len(expected_items), len(actual_items)

    # best[i][j] is the score of the best alignment of the first i expected items
    # against the first j actual ones.
    best = [[0.0] * (cols + 1) for _ in range(rows + 1)]
    for i in range(1, rows + 1):
        best[i][0] = best[i - 1][0] + GAP_PENALTY
    for j in range(1, cols + 1):
        best[0][j] = best[0][j - 1] + GAP_PENALTY

    for i in range(1, rows + 1):
        for j in range(1, cols + 1):
            agreed = sum(score_item(expected_items[i - 1], actual_items[j - 1], source).values())
            best[i][j] = max(
                best[i - 1][j - 1] + agreed,
                best[i - 1][j] + GAP_PENALTY,
                best[i][j - 1] + GAP_PENALTY,
            )

    columns = []
    i, j = rows, cols
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            agreed = sum(score_item(expected_items[i - 1], actual_items[j - 1], source).values())
            if best[i][j] == best[i - 1][j - 1] + agreed:
                columns.append((expected_items[i - 1], actual_items[j - 1]))
                i, j = i - 1, j - 1
                continue
        if i > 0 and best[i][j] == best[i - 1][j] + GAP_PENALTY:
            columns.append((expected_items[i - 1], None))
            i -= 1
            continue
        columns.append((None, actual_items[j - 1]))
        j -= 1

    columns.reverse()
    return columns


def score_sample(expected, actual, source):
    """Return (correct, total, misses, shape) for one sample.

    `shape` counts the two kinds of error separately: how many items failed to
    pair at all, and how many fields are wrong inside the pairs that did. One
    merged line is one segmentation error, not fifteen field errors.
    """
    correct = 0
    total = 0
    misses = []
    shape = {"segmentation": 0, "field": 0}

    for field in HEADER_FIELDS:
        total += 1
        if expected.get(field) == actual.get(field):
            correct += 1
        else:
            shape["field"] += 1
            misses.append(f"{field}: expected {expected.get(field)!r}, got {actual.get(field)!r}")

    columns = align_items(expected["items"], actual.get("items", []), source)

    # An unpaired item still costs all five of its fields. The alignment changes
    # which items get compared, not how much a missing event is worth.
    for index, (expected_item, actual_item) in enumerate(columns):
        label = f"item_{index + 1:03d}"
        total += len(ITEM_FIELDS)

        if actual_item is None:
            shape["segmentation"] += 1
            misses.append(f"{label}: missing, the model did not produce this item")
            continue
        if expected_item is None:
            shape["segmentation"] += 1
            misses.append(f"{label}: extra item not in the expected answer")
            continue

        for field, matched in score_item(expected_item, actual_item, source).items():
            if matched:
                correct += 1
                continue

            shape["field"] += 1
            if field == "source_excerpt":
                misses.append(f"{label}.source_excerpt: quotes text that is not in the sample")
            else:
                misses.append(
                    f"{label}.{field}: expected "
                    f"{expected_item[field]!r}, got {actual_item.get(field)!r}"
                )

    return correct, total, misses, shape


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
                "sample": stem, "correct": 0, "total": 0,
                "misses": ["no output file, run src.batch first"],
                "shape": {"segmentation": 0, "field": 0},
            })
            continue

        correct, total, misses, shape = score_sample(
            json.loads(expected_file.read_text(encoding="utf-8")),
            json.loads(actual_file.read_text(encoding="utf-8")),
            sample_file.read_text(encoding="utf-8"),
        )
        report.append({
            "sample": stem, "correct": correct, "total": total,
            "misses": misses, "shape": shape,
        })

    return report


def main():
    parser = argparse.ArgumentParser(description="Score the batch outputs against data/expected.")
    parser.add_argument("--expected", default="data/expected")
    parser.add_argument("--output", default="outputs")
    parser.add_argument("--samples", default="data/samples")
    args = parser.parse_args()

    report = score_all(args.expected, args.output, args.samples)

    for row in report:
        print(f"\n{row['sample']}: {row['correct']}/{row['total']} — {describe_shape(row['shape'])}")
        for miss in row["misses"]:
            print(f"  - {miss}")

    correct = sum(row["correct"] for row in report)
    total = sum(row["total"] for row in report)
    clean = sum(1 for row in report if not row["misses"])
    percent = (correct / total * 100) if total else 0
    shape = {
        "segmentation": sum(row["shape"]["segmentation"] for row in report),
        "field": sum(row["shape"]["field"] for row in report),
    }

    print(f"\nField accuracy: {correct}/{total} ({percent:.0f}%)")
    print(f"Samples with no errors: {clean}/{len(report)}")
    print(f"Error shape: {describe_shape(shape)}")
    if shape["segmentation"]:
        print("  A segmentation error is one event split or merged, and it costs "
              "five fields. Fixing one is worth more than fixing five field errors.")


def describe_shape(shape):
    """'1 segmentation error, 3 field errors', or 'no errors'."""
    parts = [
        f"{count} {name} error{'' if count == 1 else 's'}"
        for name, count in (("segmentation", shape["segmentation"]), ("field", shape["field"]))
        if count
    ]
    return ", ".join(parts) if parts else "no errors"


if __name__ == "__main__":
    main()
