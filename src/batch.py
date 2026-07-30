import argparse
import csv
from pathlib import Path

from .organizer import JobOrganizerError, organize_job_stream, save_result

LOG_COLUMNS = ["sample", "status", "items", "actions", "notes"]


def process_folder(input_dir="data/samples", output_dir="outputs"):
    """Run every sample through the organizer and write a results log.

    One bad sample must not kill the whole run, so each file is wrapped
    separately and a failure is recorded as a row instead of an exception.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    rows = []
    for sample in sorted(input_path.glob("*.txt")):
        try:
            result = organize_job_stream(sample.read_text(encoding="utf-8"))
            save_result(result, output_path / f"{sample.stem}.json")
            rows.append({
                "sample": sample.name,
                "status": "pass",
                "items": len(result.items),
                "actions": len(result.open_actions),
                "notes": "; ".join(result.warnings),
            })
        except (ValueError, JobOrganizerError) as exc:
            rows.append({
                "sample": sample.name,
                "status": "failed",
                "items": 0,
                "actions": 0,
                "notes": str(exc),
            })

    log_file = output_path / "results_log.csv"
    with log_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=LOG_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    return rows


def main():
    parser = argparse.ArgumentParser(description="Batch-process the sample job streams.")
    parser.add_argument("--input", default="data/samples")
    parser.add_argument("--output", default="outputs")
    args = parser.parse_args()

    rows = process_folder(args.input, args.output)
    for row in rows:
        print(f"{row['sample']}: {row['status']} | {row['items']} items | {row['actions']} actions")


if __name__ == "__main__":
    main()
