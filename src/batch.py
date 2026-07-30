from __future__ import annotations

import argparse
import csv
from pathlib import Path

from .organizer import JobOrganizerError, organize_job_stream, save_result


def process_folder(
    input_dir: str | Path = "data/samples",
    output_dir: str | Path = "outputs",
    *,
    demo_mode: bool | None = None,
) -> list[dict[str, str]]:
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    for sample in sorted(input_path.glob("*.txt")):
        try:
            result = organize_job_stream(
                sample.read_text(encoding="utf-8"),
                demo_mode=demo_mode,
            )
            save_result(result, output_path / f"{sample.stem}.json")
            rows.append(
                {
                    "sample": sample.name,
                    "status": "pass",
                    "items": str(len(result.items)),
                    "actions": str(len(result.open_actions)),
                    "notes": "; ".join(result.warnings),
                }
            )
        except (ValueError, JobOrganizerError) as exc:
            rows.append(
                {
                    "sample": sample.name,
                    "status": "failed",
                    "items": "0",
                    "actions": "0",
                    "notes": str(exc),
                }
            )

    with (output_path / "results_log.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["sample", "status", "items", "actions", "notes"],
        )
        writer.writeheader()
        writer.writerows(rows)

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch-process Foreman sample files.")
    parser.add_argument("--input", default="data/samples")
    parser.add_argument("--output", default="outputs")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Force no-key rule-based demo mode.",
    )
    args = parser.parse_args()

    rows = process_folder(args.input, args.output, demo_mode=True if args.demo else None)
    for row in rows:
        print(
            f"{row['sample']}: {row['status']} | "
            f"{row['items']} items | {row['actions']} actions"
        )


if __name__ == "__main__":
    main()
