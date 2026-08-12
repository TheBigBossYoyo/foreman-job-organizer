# Technical hand-off for the slides

For @neeti0720, for the Scribe write-up and the Friday deck.

Everything below is measured, not estimated. Numbers are from
`python -m src.score` and `python -m pytest` run on 12 August 2026, against the
current `main` (`bdb0649`). If you re-run them and get a different number, see
"Why the number moves" at the bottom before you change a slide.

---

## 1. Which option, and what the tool does

**Option C — the Job Organizer.**

A contractor's job record arrives as scattered texts, receipts, photo captions
and supplier calls. The tool turns that into a structured timeline: every event
categorized and dated, open actions pulled out, and a quote from the source line
attached to each item so a human can check it.

One sentence for a slide:

> It turns a messy contractor job stream into a structured timeline, and we can
> tell you how often it gets each field right.

The second half is the part that separates it from a demo that looks good on one
input.

---

## 2. Input and output

**In:** plain text. One or more job updates pasted into a box. No photos, no
PDFs — it takes text.

**Out:** one validated JSON object, rendered as a timeline on screen.

| | Field | Note |
|---|---|---|
| Header | project name, client name, property address | `null` if the input never says |
| Per item | category | one of a fixed list, rejected by the schema if invented |
| | date | only if written on that item's own line |
| | people, location | |
| | amount + currency | multi-currency, USD and TND both appear in the samples |
| | title, summary | |
| | action_required + the action | |
| | priority, confidence | |
| | source_excerpt | the line it came from |
| | flags | safety_review, possible_pii, low_confidence |
| Whole run | open actions, overall summary, warnings, which provider answered | |

The rule that matters: **if something is absent or ambiguous, it returns `null`
and adds a warning. It does not guess.**

---

## 3. Screenshot

Three, in `docs/screenshots/`, all from a live run with Groq answering:

| File | What it shows |
|---|---|
| `01-app-landing.png` | The app on open — sidebar, provider status, input box |
| `02-timeline.png` | A finished run on `03_tricky_bathroom` — the full timeline |
| `03-warnings.png` | Open actions as checkboxes, and the warnings expanded |

`02-timeline.png` carries a slide on its own. The README in that folder lists
what to point at in it.

---

## 4. A worked example

Input — `data/samples/03_tricky_bathroom.txt`. This is the demo sample, chosen
because almost every line is awkward in a different way:

```text
Chen bathroom reno - 44 Pine Ave
client is Maya Chen

7/27 demo done. opened up the shower wall and there is moisture behind it
photo_0431.jpg - dark staining, lower left of the shower framing
Maya (text): "does the moisture thing push the tile start on friday??"
lopez said he might be able to swing by thursday pm to take a look
vanity - supplier called, delayed, wouldnt give me a firm date
```

Output — seven lines become five items (full JSON in
`outputs/03_tricky_bathroom.json`):

| # | Category | Title | Date | Action |
|---|---|---|---|---|
| 1 | contractor update | Demo completion and moisture issue | none | Investigate the moisture |
| 2 | photo | Shower framing photo | none | — |
| 3 | client update | Tile start date inquiry | none | Reply to the client |
| 4 | schedule | Lopez site visit | none | — (flagged low confidence) |
| 5 | issue | Vanity delivery delay | none | Chase a firm date |

Three things to point at on this slide:

- **`7/27` did not become a date.** The line says `7/27` with no year. Inventing
  `2026-07-27` is exactly the kind of plausible wrong answer that would hurt a
  contractor in a billing dispute, so the date comes back `null` with a warning.
- **"might be able to swing by thursday pm" is flagged low confidence.** The
  model is not sure and says so, rather than filing it as a confirmed booking.
- **Every row traces back.** Each item carries the input line it came from.

The header fields work too: `Chen bathroom reno`, `Maya Chen` and `44 Pine Ave`
are all pulled out of two unlabelled lines at the top.

If you want a second example, `04_tricky_painting` is the one where
`client_name` comes back `null`, because that sample never names a client. It
used to guess "Wilson" from the project title. `null` is the correct answer and
it is worth a sentence.

---

## 5. Accuracy, before and after

`python -m src.score` compares the generated `outputs/` against hand-written
answer keys in `data/expected/`. The keys were written **before** the outputs
were scored. 265 fields across 10 samples: 3 header fields per sample, 5 per
item.

### Where it stands now

| Measure | Result |
|---|---|
| Field accuracy | **241/265 (91%)** |
| Samples with no errors | 4/10 |
| Date fields correct | 44/47 |
| Tests | 144 passing |

Error shape: **3 segmentation errors, 9 field errors.** Those are different
problems and it matters. A segmentation error is one event merged or dropped and
it costs five fields at once. 24 missed fields reads like 24 problems; it is 12.

### The improvement worth putting on a slide

This is the date experiment, and it is the strongest technical result we have.
Dates were failing two ways: inventing a year (`7/27` → `2026-07-27`), and
inheriting a date from the line above.

| Attempt | Score |
|---|---|
| Baseline | 112/125 (90%) |
| Rewrote the prompt rule | 115/125 (92%) |
| Rewrote the prompt again | no change |
| Checked the date against the item's quote (in code) | 112/125 (90%) — worse |
| Checked the date against the item's **source line** (in code) | **118/125 (94%)** |

Four things happened there, and all four are worth saying:

1. The prompt fixed half of it. Invented years stopped. Date inheritance did not
   move at all.
2. A second prompt rewrite did nothing.
3. **The first code fix made it worse.** Dropping any date not inside the item's
   own quote deleted four correct dates, because the model quotes `Crew completed
   cabinet removal` and leaves the `2026-07-21 - ` off the front.
4. Reading the date off the original source line instead fixed it completely.

The line to end on:

> Two prompt rewrites did not move it. Twenty lines of code fixed it completely.
> A rule the model has to remember is weaker than a rule the pipeline enforces.

That claim now has three independent confirmations. The safety guardrail and the
photo-classification fix both went the same way, and a set of category tie-break
rules we tried in the prompt last week moved the total 240 → 242 → 241, which is
inside the noise band. Prompt rules hold on the examples they quote and nowhere
else.

### Careful with this one

You will see **192/214 (90%)** in older notes and in the current
`PRESENTATION.md`. Do **not** present 192/214 → 241/265 as an improvement. It
isn't one, and someone will ask.

Two separate things changed:

- We added samples 09 and 10, so the denominator went from 214 to 265.
- We fixed the scorer. It used to match up items by position, so when the model
  merged two lines into one item on `06_safety_incident`, every item after it was
  compared against the wrong answer and one mistake was charged fifteen times.
  The scorer now aligns items before comparing them.

On the *same eight samples*, that scorer fix alone read 192/214 → **201/214**.
The other seven samples came out identical field for field and the original five
scored 118/125 for the third run running. **The model did not change. The ruler
was wrong.**

Which is a better slide than a fake improvement, honestly. Fixing the
measurement was worth more than any prompt change we tried all week.

---

## 6. Other things worth showing

Ranked by how well they land.

**The date experiment (section 5).** Strongest slide. Do not cut it. It includes
a change that lowered our own score, which we kept in the write-up.

**The provider chain degrades instead of dying.** Anthropic Claude first, then
Groq, then a local rule-based engine that needs no API key at all. The local
engine returns the same validated JSON so nothing downstream changes — but it is
much worse (86/150 against the model's 118/125 on the same samples), the app says
so in red, and every output file records which provider produced it. Good answer
to "what if the API is down during the demo".

**Guardrails enforced in code, not asked for in the prompt.** Injury language
forces a safety review flag and raises the item to urgent whatever the model
called it. A receipt with no amount gets flagged. Phone numbers and card numbers
are redacted from the titles and summaries. These fire regardless of what the
model returns.

**One honest open question.** `10_repeated_event` states an inspection twice and
a delivery twice in different words. The answer key expects four items; the model
returned two, because it silently de-duplicated them. We have not decided who is
right. A foreman probably wants one inspection, not two — but nothing asked the
model to de-duplicate, and a model that merges things that merely *sound* alike
is the `06` failure wearing a friendlier face. It is most of the gap between 91%
and higher. Presenting an undecided question with the argument for both sides is
better than pretending we have no open items.

**The merge, if it comes up.** Two prototypes existed: this one and a teammate's
Python port of a PHP app. They were merged rather than chosen between. Kept from
ours: the scorer, the answer key, the source-line date check. Taken from theirs:
the provider fallback, the code-enforced guardrails, the aggregation layer. We
declined their 13-category schema, because adopting it would have invalidated the
answer key and made the new score incomparable with every earlier one.

**"Did you use AI to build this?"** Yes — and then show what makes it ours. The
commit history walks through the decisions, `PROJECT_NOTES.md` records why, and
section 5 is the proof: nobody generates a change that lowers their own score and
then keeps it in the write-up.

---

## Do not claim

- Not production-ready. It is a prototype.
- 91% is not an industry benchmark. It is 265 fields on 10 samples we wrote
  ourselves. **Say the denominator every time you say the number.**
- Don't compare it to anyone else's number unless you know their denominator.
- It does not handle photos or PDFs. It takes text.
- Everything in `data/samples/` is invented. Never show real Foreman customer,
  employee or company data — that rule is in the README and repeated in the app
  sidebar.

## Why the number moves

Temperature is 0, which is not the same as deterministic. Three consecutive runs
of the same samples scored 117, 118, 118 — so about ±1 on fields. Larger jumps
happen when the model splits or merges a line differently, which moves the item
count and the denominator at once. `python -m src.stability --runs N` measures
both.

So if you re-run it and get 240 or 242, nothing is broken. If you get something
far off, tell me before it goes on a slide.

## Reproducing any of this

```bash
python -m pip install -r requirements.txt
python -m src.batch     # regenerate outputs/ (needs an API key)
python -m src.score     # the accuracy numbers above, no API key needed
python -m pytest        # 144 tests
streamlit run app.py    # the interface
```
