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

## Score the outputs

Compares everything in `outputs/` against the hand-written answers in
`data/expected/` and prints the misses:

```bash
python -m src.score
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
│   ├── expected/
│   └── samples/
├── outputs/
├── src/
│   ├── batch.py
│   ├── organizer.py
│   ├── prompts.py
│   ├── schema.py
│   └── score.py
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

`python -m src.score` compares `outputs/` against `data/expected/`. 125 fields
across the 5 samples: three header fields each, then category, date,
action_required, amount and source_excerpt for every one of the 22 items.

| Measure | Result |
| --- | --- |
| Field accuracy | 115/125 (92%) |
| Samples with no errors | 1/5 |

The gap between those two numbers is the interesting part. Most fields are
right, but only one document is completely clean, because the errors spread
thin rather than piling up in one bad sample.

### What the date rule change did

Dates were the weakest field, in two shapes. Rewriting rule 3 to spell both out
fixed one of them and left the other untouched. Both counts below come from the
same scorer, so they are comparable:

| | Before | After |
| --- | --- | --- |
| Field accuracy | 112/125 (90%) | 115/125 (92%) |

- **Invented years: fixed.** `03_tricky_bathroom` says `7/27` and nothing else.
  The model used to return `2026-07-27`. It now returns `null` with a warning.
- **Invented client name: fixed too, unexpectedly.** `04_tricky_painting` names
  no client, and the model used to answer `Wilson` by reading it off the project
  title. Telling it not to fill in years from elsewhere seems to have made it
  more careful about the header fields generally.
- **Inherited dates: not fixed.** In `02_easy_roof` the photo and receipt lines
  still take the date of the dated line above them. `05_mixed_job_stream` does
  it for the photo but not for the invoice on the very next line, so it is not
  even consistent with itself. The model is treating a dated line as a heading
  for the block underneath, and telling it not to has not been enough.

### What is still wrong

Ten misses. Three are the inherited dates above. Four are category
disagreements, and some of those are genuinely arguable, such as whether
"demo done ... there is moisture behind it" is a contractor update or an issue.
Those judgements live in `data/expected/` and can be challenged. The rest are
missed action flags.

Inheritance is the Week 4 target, and it will need something other than another
sentence in the prompt.
