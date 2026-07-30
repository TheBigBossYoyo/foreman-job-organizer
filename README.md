# Foreman AI Job Organizer — Option C

A VTSP technical-track prototype. It takes the running record of a construction
job, the notes and texts and receipts that pile up while the work happens, and
turns it into a timeline you can actually read.

## What it produces

- Project, client, and address metadata
- Categorized timeline items
- Dates, people, locations, and monetary amounts
- Concise summaries and source excerpts
- Open actions, priorities, confidence labels, and warnings
- Downloadable JSON output

## Privacy

Use only made-up sample data. Never use real Foreman customer, employee, or
company data.

## Setup

Install the packages:

```bash
python -m pip install -r requirements.txt
```

Then add a Groq API key. Copy `.env.example` to `.env` and fill it in:

```text
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

`.env` is gitignored. Never commit the key.

Run the app:

```bash
streamlit run app.py
```

## Run the batch processor

Processes every `.txt` in `data/samples`, writes one JSON per sample plus a CSV
results log:

```bash
python -m src.batch
```

## Run tests

```bash
pytest
```

## Repository structure

```text
Foreman Job Organizer/
├── app.py
├── data/
│   └── samples/
├── outputs/
├── src/
│   ├── batch.py
│   ├── organizer.py
│   ├── prompts.py
│   └── schema.py
├── tests/
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Core pipeline

1. Take raw text.
2. Build the prompt: instructions, the schema, a worked example, the missing-data rule.
3. Call Groq.
4. Slice out the JSON object and parse it.
5. Validate required fields and allowed values with Pydantic.
6. Return the result, or raise with the reason it failed.
7. `src/batch.py` runs the whole folder and logs a row per sample.

## Missing-data rule

When something is absent or genuinely ambiguous, return `null` and add a
warning. Do not guess. If even a human would be unsure, flag it for review
rather than committing to an answer.

## Accuracy so far

Rough Week 3 count, scored by reading each output against its source text.
125 fields across the 5 samples:

| Measure | Result |
| --- | --- |
| Field-level accuracy | 116/125 (93%) |
| Samples fully correct, no errors | 1/5 |

The gap between those two numbers is the interesting part: most fields are
right, but only one document is completely clean, because the errors are spread
thin rather than concentrated in one bad sample.

**Weakest field: dates.** 5 of the 9 errors are the model assigning a date that
is not literally in the text. Two kinds:

- Inheriting a date from the line above. In `02_easy_roof` the receipt and photo
  have no date of their own and were given the previous line's date at high
  confidence with no warning. The same shape in `01_easy_kitchen` correctly
  returned `null`, so the behaviour is inconsistent rather than wrong-by-design.
- Inventing a year. `03_tricky_bathroom` says `7/27` and nothing else; the model
  returned `2026-07-27`. The prompt already says to use `null` when the year
  cannot be safely inferred, and it did not follow that here.

Other errors: the client name in `04_tricky_painting` was inferred from the
project title when no client is named, one vendor location was missed, one photo
was categorized as an issue, and one unconfirmed site visit was not flagged as
an action.

Fixing the date rule is the first job in Week 4, and it is the before/after
measurement for the accuracy write-up.
