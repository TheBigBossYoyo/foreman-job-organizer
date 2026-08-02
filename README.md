# 🏗️ Foreman AI Job Organizer

**VTSP · Technical track · Option C — The Job Organizer**

![Tests](https://img.shields.io/badge/tests-84%20passing-2ea44f)
![Accuracy](https://img.shields.io/badge/field%20accuracy-118%2F125%20(94%25)-2ea44f)
![Dates](https://img.shields.io/badge/dates%20correct-22%2F22-2ea44f)
![Python](https://img.shields.io/badge/python-3.14-3776AB)
![Providers](https://img.shields.io/badge/Claude%20→%20Groq%20→%20local-EA580C)

A contractor's job record is not a document. It is a pile — texts at 9pm,
receipts with no date on them, photo captions, a supplier who called and would
not commit to anything.

**This turns the pile into a timeline. And it tells you how often it gets each
field right, which is the part I care most about.**

---

## 👀 What it actually does

Paste this:

```text
Project: Alvarez kitchen renovation
Client: Sofia Alvarez
Address: 18 Cedar Lane

2026-07-21 - Crew completed cabinet removal and disposed of debris.
Receipt: BuildRight, drywall and screws, $142.75.
2026-07-22 - New cabinets delivered in good condition.
Client update: Sofia approved the quartz countertop sample.
```

Get this:

| When | What | | |
|---|---|---|---|
| **21 Jul** | 🏗️ Site work | Cabinet removal | |
| **no date** | 🧾 Receipt | Drywall and screws receipt | **142.75 USD** |
| **22 Jul** | 🚚 Delivery | New cabinet delivery | |
| **no date** | 💬 Client | Quartz countertop sample approval | |

Look at the receipt. It sits directly under a dated line, and it comes back
with **no date** — because its own line never gave one. Getting that right took
four attempts and is the most interesting thing in this repo. The story is in
[How the date problem was solved](#-how-the-date-problem-was-actually-solved).

---

## 🚀 Quick start

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

That's it. **No API key needed to try it** — with no keys at all it falls back
to a local rule-based engine that returns the same JSON shape. It is much worse,
and the app says so in red rather than pretending otherwise.

For real output, copy `.env.example` to `.env` and add a key:

```text
ANTHROPIC_API_KEY=your_key_here     # tried first
GROQ_API_KEY=your_key_here          # the backup
```

> ⚠️ `.env` is gitignored. Never commit a key.

**Other things you can run:**

```bash
python -m src.batch     # organize every sample, write JSON + a CSV log
python -m src.score     # score those outputs against the hand-written answers
pytest                  # 84 tests
```

---

## 🔌 Providers

Three, tried in order. First one that answers wins.

| | Provider | Needs | Used when |
|---|---|---|---|
| 1️⃣ | **Anthropic Claude** | `ANTHROPIC_API_KEY` | Always, when the key is set |
| 2️⃣ | **Groq** | `GROQ_API_KEY` | Anthropic has no key, or its call failed |
| 3️⃣ | **Local rule-based** | nothing | Neither model is reachable |

The local engine is not a stub — it returns the same validated contract, so
nothing downstream knows the difference. But it matches keywords instead of
reading, and the gap is big enough to be worth measuring:

| Engine | Field accuracy |
|---|---|
| Groq | **118/125 (94%)** |
| Local rule-based | **86/150 (57%)** |

The denominator differs because the local engine also splits the stream badly
and invents items that then lose every field. That is the honest size of the
gap, and the reason the fallback is a safety net rather than a mode to demo in.
Every result records which provider produced it.

Set `AI_PROVIDER=anthropic|groq|local` to pin one and skip the chain.

---

## ⚙️ How it works

```
raw text
   │
   ├─ 1. build the prompt      instructions · schema · worked example · missing-data rule
   ├─ 2. call the chain        src/providers.py — Claude → Groq → local
   ├─ 3. slice out the JSON    the reply is not always only JSON
   ├─ 4. validate              src/schema.py — Pydantic, no invented categories
   ├─ 5. ground the dates      src/dates.py — a date must be on the item's own line
   ├─ 6. enforce guardrails    src/guardrails.py — safety · money · PII
   └─ 7. aggregate             src/aggregate.py — timeline, totals, actions (no API call)
```

Steps 5 and 6 are the interesting ones. Everything before them asks the model to
behave; those two check that it did.

---

## 🛡️ The rules it enforces in code

The date work taught this project one thing above all:

> **A rule in the prompt is a request. A rule in the code is a guarantee.**

Two prompt rewrites failed to stop dates being copied between lines. Twenty
lines of code stopped it completely. So the rules that actually matter live in
`src/guardrails.py`, not in the wording:

- 🚨 **Injury language** forces an urgent review flag, whatever the model called it
- 💵 **A receipt or payment with no amount** is flagged, not left looking complete
- 🔒 **Phone numbers and SSNs** are redacted from the summary — and the note says
  plainly that the source excerpt still contains them, because pretending
  otherwise would be worse than not redacting
- 📅 **A date not written on the item's own line** is dropped with a warning

### The missing-data rule

When something is absent or genuinely ambiguous: return `null`, add a warning,
**do not guess**. If even a human would be unsure, flag it rather than commit to
an answer.

---

## 📊 Accuracy

`python -m src.score` compares `outputs/` against `data/expected/` — **125
fields** across 5 samples: three header fields each, plus category, date,
`action_required`, amount and `source_excerpt` for all 22 items.

| Measure | Result |
|---|---|
| Field accuracy | **118/125 (94%)** |
| Samples with no errors | 2/5 |
| Date fields correct | **22/22** ✅ |

Two things worth saying out loud rather than burying:

**The two numbers disagree on purpose.** 94% of fields are right, but only 2 of
5 documents are completely clean, because errors spread thin instead of piling
into one bad sample. A per-document score would be 40% and would also be true.

**Temperature 0 is not the same as deterministic.** Three consecutive runs of
the same five samples scored 117, 118, 118. Treat this as **118 ± 1** — not
precise enough to justify chasing a single-field change.

Measured on Groq, since no Anthropic key was set on the last run. The provider
is recorded in every file in `outputs/`, so any number can be traced to the
engine that produced it.

---

## 🔬 How the date problem was actually solved

Dates were the weakest field, failing two ways: **invented years** (`7/27`
became `2026-07-27`) and **inherited dates** (an undated line taking the date of
the line above). Every number below comes from the same scorer, so they compare
directly.

| Attempt | Result | |
|---|---|---|
| Week 3 baseline | 112/125 (90%) | |
| Rewrote the prompt rule | 115/125 (92%) | ⬆️ |
| Checked the date against the item's **excerpt** | 112/125 (90%) | ⬇️ **worse** |
| Checked the date against the item's **source line** | **118/125 (94%)** | ✅ |

**The prompt fixed half of it.** Spelling out both failure shapes stopped the
invented years. Inheritance did not move at all, and a second rewrite did not
move it either — the model reads a dated line as a heading for the block below.

**My first code fix made it worse, which is the useful part.** I dropped any
date not found in the item's `source_excerpt`. It cost three fields, because the
model quotes `Crew completed cabinet removal` and leaves the `2026-07-21 - ` off
the front. The check could not see dates that were really there and deleted four
correct ones.

**Checking the source line fixed it.** Find the line the quote came from and
read the date off that — the prefix is still there. Inherited dates get dropped
with a warning, real ones survive, and all 22 date fields are now correct.

I kept the failed attempt in this table on purpose. It is what makes the final
design look reasoned rather than lucky.

---

## 🚧 What is still wrong

Seven misses, **none of them dates**.

- **5 are category disagreements**, and some are genuinely arguable — whether
  *"demo done … there is moisture behind it"* is a contractor update or an issue
  is a judgement call. Those judgements are mine, sitting in `data/expected/`.
  If you disagree, the fix is to change the answer key, not the code.
- **2 are missed action flags**, where an item plainly asks for something and
  `action_required` came back `false`. Those are simply wrong.

Categories are the Week 4 target now that dates are done.

---

## 🤝 One app, from two

This repo briefly held two prototypes — this one and a teammate's port of a PHP
web app. They were merged rather than picked between.

| | |
|---|---|
| **Kept from here** | the scorer and answer key, the source-line date check, the Pydantic contract, the batch runner |
| **Taken from the port** | the provider chain with its no-key fallback, guardrails enforced in code, the aggregation layer |
| **Deliberately not taken** | its 13-category schema and its own samples |

That last row is the one I'd defend hardest. Both are reasonable, and adopting
either would have invalidated `data/expected/` and made the new number
incomparable with every earlier measurement. A richer schema is worth having; it
is not worth losing the only measurement chain the project has. Widening the
test set is Week 4 work, done properly by adding samples and their answers
together.

The port is still on the `webapp-python` branch if you want to read the original.

---

## 📁 Repository

```text
Foreman Job Organizer/
├── app.py                  Streamlit interface
├── data/
│   ├── samples/            five made-up job streams
│   └── expected/           hand-written answers — the scorer's ground truth
├── outputs/                generated JSON + results log
├── src/
│   ├── providers.py        Claude → Groq → local, with a no-key engine
│   ├── organizer.py        the core pipeline
│   ├── prompts.py          system prompt, schema, worked example
│   ├── schema.py           Pydantic contract
│   ├── dates.py            the date grounding check
│   ├── guardrails.py       safety · money · PII, enforced in code
│   ├── aggregate.py        timeline, totals, derived actions
│   ├── score.py            field-by-field accuracy
│   ├── batch.py            run the whole folder
│   └── text.py             shared normalisation
├── tests/                  84 tests
└── PRESENTATION.md         slide plan, demo script, Q&A prep
```

---

## 🔐 Privacy

> **Made-up sample data only.** Never use real Foreman customer, employee, or
> company data. Everything in `data/samples/` is invented, and the rule is
> repeated in the app sidebar so it is visible while the tool is in use.

---

<sub>Built for the 2026 Venture &amp; Tech Summer Program. This is a measured
prototype, not a production system.</sub>
