# 🏗️ Foreman AI Job Organizer

**VTSP · Technical track · Option C**

![Tests](https://img.shields.io/badge/tests-107%20passing-2ea44f)
![Accuracy](https://img.shields.io/badge/field%20accuracy-118%2F125%20(94%25)-2ea44f)
![Python](https://img.shields.io/badge/python-3.14-3776AB)
![Providers](https://img.shields.io/badge/Claude%20→%20Groq%20→%20local-EA580C)

A contractor's job record is not a document. It's a pile — texts at 9pm,
receipts with no date on them, photo captions, a supplier who called and
wouldn't commit to anything.

This turns the pile into a timeline.

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
its own line never gave one. Inheriting that date would be inventing a fact.

---

## 🚀 Running it

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

No API key needed to try it — without one it falls back to a local rule-based
engine. That engine is much worse and the app says so in red.

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
pytest                  # 107 tests
```

---

## 🔌 Providers

Three, tried in order. First one that answers wins.

| | Provider | Needs | Used when |
|---|---|---|---|
| 1️⃣ | **Anthropic Claude** | `ANTHROPIC_API_KEY` | Whenever the key is set |
| 2️⃣ | **Groq** | `GROQ_API_KEY` | Anthropic has no key, or its call failed |
| 3️⃣ | **Local rule-based** | nothing | Neither model is reachable |

The local engine returns the same validated JSON, so nothing downstream knows
the difference. It matches keywords instead of reading, and it scores 86/150
against the model's 118/125. It's a safety net, not something to demo.

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

- 🚨 Injury language forces an urgent review flag, whatever the model called it
- 💵 A receipt or payment with no amount is flagged rather than left looking complete
- 🔒 Phone numbers, SSNs and card numbers are redacted from titles and
  summaries — the note says the source excerpt still contains them
- 🔁 A provider that fails is named in the warnings, so a fallback can't pass
  for a choice
- 📅 A date not written on the item's own line is dropped with a warning

**Missing-data rule:** when something is absent or ambiguous, return `null`, add
a warning, don't guess.

---

## 📊 Accuracy

`python -m src.score` compares `outputs/` against the hand-written answers in
`data/expected/` — 125 fields across 5 samples.

| Measure | Result |
|---|---|
| Field accuracy | **118/125 (94%)** |
| Samples with no errors | 2/5 |
| Date fields correct | **22/22** ✅ |

94% of fields are right but only 2 of 5 documents are completely clean, because
the errors spread thin instead of piling into one bad sample.

Temperature is 0, which isn't the same as deterministic — three consecutive runs
scored 117, 118, 118. Call it 118 ± 1.

Measured on Groq. Every file in `outputs/` records which provider produced it.

### Known errors

Seven misses, none of them dates.

- **5 category disagreements.** Some are arguable — whether *"demo done … there
  is moisture behind it"* is a contractor update or an issue is a judgement
  call, and that judgement lives in `data/expected/`.
- **2 missed action flags**, where an item plainly asks for something and
  `action_required` came back `false`.

Categories are next.

---

## 📁 Repository

```text
├── app.py                  Streamlit interface
├── data/
│   ├── samples/            five made-up job streams
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
│   ├── batch.py            run the whole folder
│   └── text.py             shared normalisation
├── tests/                  107 tests
└── PRESENTATION.md         slide plan and demo script
```

---

## 🔐 Privacy

> Made-up sample data only. Never use real Foreman customer, employee, or company
> data. Everything in `data/samples/` is invented, and the rule is repeated in the
> app sidebar.

<sub>Built for the 2026 Venture &amp; Tech Summer Program. A measured prototype,
not a production system.</sub>
