# Foreman AI Job Organizer — Option C

A VTSP technical-track prototype. It takes the running record of a construction
job, the notes and texts and receipts that pile up while the work happens, and
turns it into a timeline you can actually read.

> **Two prototypes in this repo.** The root is the original Python/Streamlit
> prototype (measurement-focused: scorer, Pydantic schema, `pytest`). A second,
> web-app-derived Python port lives in [`webapp-python/`](webapp-python/) — it
> brings over a richer 13-category schema, code-enforced guardrails (safety,
> never-invent-money, PII, date-grounding), a no-API-key local fallback, and a
> Streamlit UI with a timeline, next-actions and JSON export. See
> [`webapp-python/README.md`](webapp-python/README.md).

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
│   ├── dates.py
│   ├── organizer.py
│   ├── prompts.py
│   ├── schema.py
│   ├── score.py
│   └── text.py
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
6. Drop any date that is not written on the item's own source line (`src/dates.py`).
7. Return the result, or raise with the reason it failed.
8. `src/batch.py` runs the whole folder and logs a row per sample.

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
| Field accuracy | 118/125 (94%) |
| Samples with no errors | 2/5 |
| Date fields correct | 22/22 |

### How the date problem was actually solved

Dates were the weakest field, in two shapes: invented years (`7/27` became
`2026-07-27`) and inherited dates (an undated line took the date of the line
above it). Every number below comes from the same scorer, so they compare
directly.

| Attempt | Result |
| --- | --- |
| Week 3 baseline | 112/125 (90%) |
| Rewrote the prompt rule | 115/125 (92%) |
| Checked the date against the item's excerpt | 112/125 (90%) |
| Checked the date against the item's source line | **118/125 (94%)** |

**The prompt fixed half of it.** Spelling both failure shapes out in rule 3
stopped the invented years. Inheritance did not move at all, and a second
rewrite did not move it either — the model reads a dated line as a heading for
the block underneath it.

**The first code fix made things worse, which is the useful part.** `src/dates.py`
drops any date that is not written in the item it belongs to. Checking that
against the item's `source_excerpt` cost three fields, because the model quotes
`Crew completed cabinet removal` and leaves the `2026-07-21 - ` in front of it
out. The check could not see dates that were really there and deleted four
correct ones.

**Checking the source line instead fixed it.** The excerpt is located back in
the sample text and the date is read off that line, which still has the prefix.
Inherited dates are dropped with a warning; real ones survive. All 22 date
fields are now correct, and the two easy samples went to a perfect score.

### What is still wrong

Seven misses, none of them dates. Five are category disagreements, and some are
genuinely arguable — whether "demo done ... there is moisture behind it" is a
contractor update or an issue is a judgement call. Those judgements live in
`data/expected/` and can be challenged. The other two are missed action flags,
where the item clearly asks for something and `action_required` came back false.

Categories are the Week 4 target now that dates are done.
