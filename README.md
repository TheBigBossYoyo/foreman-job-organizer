# Foreman AI Job Organizer — Option C

A VTSP technical-track prototype. It takes the running record of a construction
job, the notes and texts and receipts that pile up while the work happens, and
turns it into a timeline you can actually read.

Built by merging two prototypes: this one, which was measurement-first, and a
web-app-derived port that had the better runtime engineering. What survived from
each is set out in [One app, from two](#one-app-from-two). The port itself is
still on the `webapp-python` branch if you want to read the original.

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

Then add a key. Copy `.env.example` to `.env` and fill it in:

```text
ANTHROPIC_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
```

`.env` is gitignored. Never commit a key.

**You do not need either one.** With no keys at all the app still runs on the
local rule-based engine — see [Providers](#providers).

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

## Providers

Three, tried in order. The first one that answers wins.

| Order | Provider | Needs | Used when |
| --- | --- | --- | --- |
| 1 | Anthropic Claude | `ANTHROPIC_API_KEY` | Always, when the key is set |
| 2 | Groq | `GROQ_API_KEY` | Anthropic has no key, or its call failed |
| 3 | Local rule-based | nothing | Neither model is reachable |

The local engine is not a stub. It returns the same validated JSON contract, so
nothing downstream knows the difference — but it matches keywords instead of
reading, and it is much worse. Scored the same way as everything else:

| Engine | Field accuracy |
| --- | --- |
| Groq | 118/125 (94%) |
| Local rule-based | 86/150 (57%) |

The denominator differs because the local engine also splits the stream badly,
inventing items that then lose every field. That is the honest size of the gap,
and it is the argument for the fallback being a safety net rather than a mode
anyone should demo in. The app says so in red when a run falls through to it,
and every result records which provider answered.

Set `AI_PROVIDER=anthropic|groq|local` to pin one and skip the chain. The scorer
uses this to measure a single engine rather than whichever one happened to
answer.

## Repository structure

```text
Foreman Job Organizer/
├── app.py
├── data/
│   ├── expected/
│   └── samples/
├── outputs/
├── src/
│   ├── aggregate.py
│   ├── batch.py
│   ├── dates.py
│   ├── guardrails.py
│   ├── organizer.py
│   ├── prompts.py
│   ├── providers.py
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
3. Call the provider chain (`src/providers.py`), falling back on failure.
4. Slice out the JSON object and parse it.
5. Validate required fields and allowed values with Pydantic.
6. Drop any date that is not written on the item's own source line (`src/dates.py`).
7. Enforce the safety, missing-amount and PII rules (`src/guardrails.py`).
8. Return the result, or raise with the reason it failed.
9. `src/aggregate.py` derives the timeline and totals, with no further API call.
10. `src/batch.py` runs the whole folder and logs a row per sample.

## One app, from two

This repo briefly held two prototypes. They were merged rather than picked
between, because each had something the other did not.

**Kept from this one:** the scorer and the hand-written answer key, the
source-line date check, the Pydantic contract, the batch runner.

**Taken from the port:** the provider chain with its no-key fallback, guardrails
enforced in code rather than asked for in the prompt, and the aggregation layer.

**Deliberately not taken:** its 13-category schema and its own samples. Both are
reasonable, but adopting either would have invalidated `data/expected/` and made
the accuracy number incomparable with every earlier measurement. Widening the
test set is Week 4 work, done by adding samples and their answers together.

The port also split a stream on blank lines only, which fused five events into
one item on a dense sample. That bug is not in this pipeline.

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

Measured on Groq, since no Anthropic key was set when this was last run. The
provider is recorded in every file in `outputs/`, so a number can always be
traced to the engine that produced it.

**On reproducibility.** Temperature is 0, but that is not the same as
deterministic. Three consecutive runs of the same five samples scored 117, 118
and 118, so treat this as 118 ± 1 field. It is not precise enough to justify
chasing a single-field change, which is worth knowing before reading too much
into the table below.

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
