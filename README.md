# 🏗️ Foreman AI Job Organizer

**VTSP · Technical track · Option C**

![Tests](https://img.shields.io/badge/tests-144%20passing-2ea44f)
![Accuracy](https://img.shields.io/badge/field%20accuracy-241%2F265%20(91%25)-2ea44f)
![Python](https://img.shields.io/badge/python-3.14-3776AB)
![Providers](https://img.shields.io/badge/Claude%20→%20Groq%20→%20local-EA580C)

Turns a messy contractor job stream — texts, receipts, photo captions, supplier
calls — into a structured timeline with open actions and a source quote for
every item.

---

## 👀 Example

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

| When | What | | |
|---|---|---|---|
| **21 Jul** | 🏗️ Site work | Cabinet removal | |
| **no date** | 🧾 Receipt | Drywall and screws receipt | **142.75 USD** |
| **22 Jul** | 🚚 Delivery | New cabinet delivery | |
| **no date** | 💬 Client | Quartz countertop sample approval | |

The receipt sits under a dated line and still comes back with no date, because
its own line never gave one.

---

## 🚀 Running it

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

No API key needed to try it. Without one it falls back to a local rule-based
engine, which is much worse — the app says so in red.

For real output, copy `.env.example` to `.env`:

```text
ANTHROPIC_API_KEY=your_key_here     # tried first
GROQ_API_KEY=your_key_here          # the backup
```

> ⚠️ `.env` is gitignored. Never commit a key.

Also useful:

```bash
python -m src.batch     # organize every sample, write JSON + a CSV log
python -m src.score     # score those outputs against the answer key
pytest                  # 144 tests
```

---

## 🔌 Providers

Three, tried in order. First one that answers wins.

| | Provider | Needs | Used when |
|---|---|---|---|
| 1️⃣ | **Anthropic Claude** | `ANTHROPIC_API_KEY` | Whenever the key is set |
| 2️⃣ | **Groq** | `GROQ_API_KEY` | Anthropic has no key, or its call failed |
| 3️⃣ | **Local rule-based** | nothing | Neither model is reachable |

The local engine returns the same validated JSON, so nothing downstream changes.
It matches keywords instead of reading. On the original five samples it scored
86/150 against the model's 118/125 — a safety net, not a demo.

Pin one with `AI_PROVIDER=anthropic|groq|local`.

---

## ⚙️ Pipeline

```
raw text
   │
   ├─ build the prompt      instructions · schema · worked example · missing-data rule
   ├─ call the chain        src/providers.py
   ├─ slice out the JSON    the reply isn't always only JSON
   ├─ validate              src/schema.py — Pydantic, no invented categories
   ├─ ground the dates      src/dates.py — a date must be on the item's own line
   ├─ enforce guardrails    src/guardrails.py — safety · money · PII
   └─ aggregate             src/aggregate.py — timeline, totals, actions
```

---

## 🛡️ Guardrails

Enforced in `src/guardrails.py`, not asked for in the prompt:

- 🚨 Injury language forces an urgent review flag, whatever the model called it,
  and the timeline shows that item as urgent
- 💵 A receipt or payment with no amount is flagged
- 🔒 Phone numbers, SSNs and card numbers are redacted from titles and summaries;
  the note states that the source excerpt still contains them
- 🔁 A failed provider is named in the warnings
- 📅 A date not written on the item's own line is dropped with a warning

**Missing-data rule:** if something is absent or ambiguous, return `null`, add a
warning, don't guess.

---

## 📊 Accuracy

`python -m src.score` compares `outputs/` against the hand-written answers in
`data/expected/` — 265 fields across 10 samples.

| Measure | Result |
|---|---|
| Field accuracy | **241/265 (91%)** |
| Samples with no errors | 4/10 |
| Date fields correct | **44/47** |

The score also reports the shape of what went wrong: **3 segmentation errors, 9
field errors**. Those are different problems. A segmentation error is one event
merged or dropped and costs five fields at once, so one of them is worth more
than five field errors.

Every date the model put on an item it produced is right. All three date losses
are items it never produced at all.

It was 192/214 before the scorer stopped matching items by position. On the same
eight samples the new scorer read 201/214 — the nine recovered fields were all on
`06_safety_incident`, which was being charged fifteen times for one merged line.
The model did not change. The measurement did.

The original five samples scored 118/125 for the third run in a row.

Temperature is 0, which is not deterministic. Three consecutive runs scored 117,
118, 118 — so ±1 on fields. `python -m src.stability --runs N` measures that,
and the item count alongside it.

Measured on Groq. Every file in `outputs/` records which provider produced it.

### Known errors

24 misses in two kinds.

- **3 segmentation errors.** One merge on `06_safety_incident`, and two on
  `10_repeated_event`, where the model collapsed each event that was stated
  twice into a single item.
- **6 category disagreements**, three of them arguable rather than wrong:
  *"demo done … there is moisture behind it"* as contractor update vs issue.
  That call lives in `data/expected/`.
- **2 missed action flags.** One is a real miss — *"living room done except
  touch ups"* names unfinished work. The other is arguable.

### The de-duplication question, and why the score isn't higher

The two segmentation errors on `10_repeated_event` are a disagreement, not a
bug. That sample states an inspection twice and a delivery twice in different
words; the key expects four items and the model returns two, having folded each
restatement in.

We built the third option — one item per event, keeping the other wording beside
it as a verified quote — and measured it. It fixed `10`, and made the model fold
a skip delivery and a wiring discovery into the line about the crew arriving on
`08_dense_stream`, which had been 33/33 and scored 22/33. Three events, not one
said three times. Reverted; the code is on `restatements-experiment`.

A model free to decide what counts as the same event will merge things that are
merely adjacent. If someone picks this up, the fold belongs in code.

Next: a warning when an input line is quoted by no item, so a merge surfaces
itself, and categories decided in code wherever the input gives a marker.

---

## 📁 Repository

```text
├── app.py                  Streamlit interface
├── data/
│   ├── samples/            ten made-up job streams
│   └── expected/           hand-written answers, the scorer's ground truth
├── outputs/                generated JSON + results log
├── src/
│   ├── providers.py        Claude → Groq → local
│   ├── organizer.py        the core pipeline
│   ├── prompts.py          system prompt, schema, worked example
│   ├── schema.py           Pydantic contract
│   ├── dates.py            date grounding
│   ├── guardrails.py       safety · money · PII
│   ├── aggregate.py        timeline, totals, derived actions
│   ├── score.py            field-by-field accuracy
│   ├── stability.py        how much the same input moves between runs
│   ├── batch.py            run the whole folder
│   └── text.py             shared normalisation
├── tests/                  144 tests
└── PRESENTATION.md         slide plan and demo script
```

---

## 🔐 Privacy

> Made-up sample data only. Never use real Foreman customer, employee or company
> data. Everything in `data/samples/` is invented. The rule is repeated in the
> app sidebar.

<sub>Built for the 2026 Venture &amp; Tech Summer Program. A prototype, not a
production system.</sub>
