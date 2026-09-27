# Foreman AI Job Organizer

VTSP, Technical track, Option C.

Turns a messy contractor job stream (texts, receipts, photo captions,
supplier calls) into a structured timeline with open actions and a source
quote for every item.

## Team

This is a two-person build. I (Youssef) wrote the pipeline, the schema, the
date-grounding check, and the scorer. My teammate, **@vjvidhaan**, built a
parallel prototype early on with the provider chain (Claude, then Groq, then
a local fallback with no key required) and guardrails enforced in code
rather than left to the prompt; we merged that into this version instead of
picking one over the other. He also added two of the ten test samples
(repeated events, and a sample with no dates at all) with their answer keys,
and a guardrails fix so a documentation photo doesn't get wrongly flagged as
needing action.

## Example

In:

```text
Project: Alvarez kitchen renovation
Client: Sofia Alvarez
Address: 18 Cedar Lane

2026-07-21 - Crew completed cabinet removal and disposed of debris.
Receipt: BuildRight, drywall and screws, $142.75.
2026-07-22 - New cabinets delivered in good condition.
Client update: Sofia approved the quartz countertop sample.
```

Out:

| When | What | Note | Amount |
|---|---|---|---|
| 21 Jul | Site work | Cabinet removal | |
| no date | Receipt | Drywall and screws receipt | 142.75 USD |
| 22 Jul | Delivery | New cabinet delivery | |
| no date | Client | Quartz countertop sample approval | |

The receipt sits under a dated line and still comes back with no date,
because its own line never gave one: we ground every date to the line it
actually appears on, not the item above it.

## Running it

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

No API key is needed to try it. Without one it falls back to a local
rule-based engine, which is noticeably worse, and the app says so.

For real output, copy `.env.example` to `.env` and add a key:

```text
ANTHROPIC_API_KEY=your_key_here     # tried first
GROQ_API_KEY=your_key_here          # backup
```

`.env` is gitignored, so don't commit a key.

Also useful:

```bash
python -m src.batch     # organize every sample, write JSON + a CSV log
python -m src.score     # score those outputs against the answer key
pytest                  # 225 tests
```

## Providers

Three, tried in order, first one that answers wins: **Anthropic Claude** (if
`ANTHROPIC_API_KEY` is set), then **Groq** (if Claude has no key or its call
failed), then a **local, rule-based** fallback that needs nothing. The local
engine returns the same validated JSON shape, so nothing downstream cares
which one ran; it's a safety net, not something we'd want to demo. It
matches keywords instead of reading, and scores far lower than either model
on our own accuracy check. You can pin one provider with
`AI_PROVIDER=anthropic|groq|local`.

## Pipeline

The input goes through: building the prompt (instructions, schema, a worked
example, the missing-data rule) → the provider chain (`src/providers.py`) →
pulling the JSON out of the reply (it isn't always only JSON) → validating it
against a Pydantic schema (`src/schema.py`, no invented categories) →
grounding dates so a date has to appear on the item's own line
(`src/dates.py`) → guardrails for safety, money, and PII
(`src/guardrails.py`) → aggregating into a timeline with totals and open
actions (`src/aggregate.py`).

## Guardrails

Enforced in code, not just asked for in the prompt: injury language forces
an urgent flag no matter what category the model picked; a receipt or
payment with no amount is flagged; phone numbers, SSNs, and card numbers are
redacted from titles and summaries (the note says the source excerpt still
has them); a failed provider is named in the warnings; and a date not
written on the item's own line is dropped with a warning attached.

Missing-data rule: if something is absent or ambiguous, we return `null` and
add a warning rather than guess.

## Accuracy

`python -m src.score` compares `outputs/` against hand-written answers in
`data/expected/`: 265 fields across 10 samples.

| Measure | Result |
|---|---|
| Field accuracy | 241/265 (91%) |
| Samples with no errors | 4/10 |
| Date fields correct | 44/47 |

The 24 misses split into two different kinds of problem: 3 segmentation
errors (one event merged or dropped, which costs several fields at once) and
9 field errors (a single wrong value). We track them separately because a
flat total can hide one getting worse while another gets better; that
happened once, when a new tie-break rule fixed two miscategorized items and
silently broke three others.

Temperature is 0, which isn't fully deterministic: repeated runs of the same
samples move by a field or two between runs. `python -m src.stability --runs
N` measures that spread. Everything above was measured on Groq; every file
in `outputs/` records which provider actually produced it.

More detail on individual misses and the tradeoffs behind them is in
`PROJECT_NOTES.md`.

## What comes out

Four things, all offline: no account, no network call besides the model API,
nothing to sign into.

- The timeline, on screen, with a source quote on every row.
- JSON, the validated result, the same shape every run.
- A calendar (`.ics`): a date that was actually written becomes an event on
  that day; an action with no date becomes a to-do with no due date;
  anything that's neither is left out, rather than guessed at.
- A job record, one printable page with the timeline, quotes, warnings, and
  which engine produced it.

## What can go in

Plain pasted text, or a phone chat export. `src/phone_import.py` reads a
WhatsApp-style export, rejoins messages the export format wrapped across
multiple lines, and strips the app's own noise. It deliberately ignores the
export's send timestamps, since using them would fill in dates for items
that never actually stated one, which is exactly the kind of invention
`src/dates.py` exists to prevent.

## Privacy

All sample data is made up. We never used real Foreman customer, employee,
or company data. Everything in `data/samples/` is invented, and the app
sidebar repeats that rule.

This was built for the 2026 Venture & Tech Summer Program. It's a prototype
for a technical-track assignment, not a production tool.
