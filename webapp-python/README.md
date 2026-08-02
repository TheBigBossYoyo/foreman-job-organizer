# Job Organizer — Python port (Option C)

A Python/Streamlit port of the team's PHP web-app prototype, contributed as a
subfolder so it lives beside the original Python prototype without touching it.

It takes a contractor's messy job stream (notes, receipts, schedule changes) and
returns a categorized timeline, a job summary, a next-actions checklist, review
flags, and downloadable structured JSON — the same output contract as the web app.

## Why this exists

The team built two Option C prototypes: a deployable PHP/MySQL web app and this
Python/Streamlit stack. This port brings the web app's strongest features to the
Python side so both share one toolkit:

- **Rich schema** — 13 categories, a trade-phase vocabulary, review flags (`src/schema.py`)
- **Guardrails enforced in code** — safety, never-invent-money, PII, and
  **date-grounding** (`src/guardrails.py`, `src/dates.py`)
- **No-API-key fallback** — a rule-based local provider returns the same JSON
  contract so it runs in demo mode (`src/providers.py`)
- **Timeline + summary + next-actions** aggregation (`src/aggregate.py`)
- **Field-by-field accuracy scorer** (`src/score.py`)
- **Anthropic Claude by default**, temperature 0 for reproducible output

## Setup

```bash
cd webapp-python
python -m pip install -r requirements.txt
cp .env.example .env        # add ANTHROPIC_API_KEY (optional — demo mode works without it)
streamlit run app.py
```

## Score the accuracy

```bash
python -m src.score         # field-by-field vs data/answer_key.json
```

## Tests

```bash
pytest                      # runs on the local provider, no API key needed
```

## Layout

```text
webapp-python/
├── app.py                 # Streamlit UI
├── src/
│   ├── schema.py          # Pydantic schema, categories, phases, flags
│   ├── prompts.py         # system prompt + worked example
│   ├── providers.py       # Claude (default) + rule-based local fallback
│   ├── dates.py           # date-grounding
│   ├── guardrails.py      # safety / money / PII / date rules
│   ├── organizer.py       # core pipeline
│   ├── aggregate.py       # timeline + summary + next-actions
│   └── score.py           # accuracy scorer
├── data/
│   ├── answer_key.json    # hand-written answers
│   └── samples/           # made-up job streams
└── tests/
```

Made-up sample data only — never real customer data.
