"""Field-by-field accuracy scorer against a hand-written answer key.

Runs each answer-key item through the pipeline and scores it field by field, so
the accuracy number can be re-run after any prompt/code change instead of
eyeballed. Mirrors both the PHP app's evaluate.php and the sibling src/score.py.

    python -m src.score
"""
from __future__ import annotations

import json
from pathlib import Path

from .organizer import organize_item

ANSWER_KEY_PATH = Path(__file__).resolve().parent.parent / "data" / "answer_key.json"


def score(answer_key: list[dict]) -> dict:
    checked = correct = 0
    misses: list[str] = []
    for entry in answer_key:
        item = organize_item(entry["raw"])
        for field, want in entry["expect"].items():
            checked += 1
            if field == "flag":
                ok = want in item.flags
            elif field == "amount":
                ok = item.amount is not None and abs(item.amount - float(want)) < 0.01
            elif field == "vendor":
                ok = bool(item.vendor) and str(want).lower() in item.vendor.lower()
            else:
                ok = str(getattr(item, field, None) or "") == str(want)
            if ok:
                correct += 1
            else:
                got = item.flags if field == "flag" else getattr(item, field, None)
                misses.append(f"  - [{entry['raw'][:40]}] {field}: expected {want!r}, got {got!r}")
    pct = round(100 * correct / checked, 1) if checked else 0.0
    return {"checked": checked, "correct": correct, "accuracy": pct, "misses": misses}


def load_answer_key() -> list[dict]:
    return json.loads(ANSWER_KEY_PATH.read_text(encoding="utf-8"))


def main() -> None:
    key = load_answer_key()
    result = score(key)
    print(f"Job Organizer (Python) — accuracy on {len(key)} answer-key items\n")
    print(f"Field accuracy: {result['correct']}/{result['checked']} ({result['accuracy']}%)")
    if result["misses"]:
        print("Misses:")
        print("\n".join(result["misses"]))
    else:
        print("No misses.")


if __name__ == "__main__":
    main()
