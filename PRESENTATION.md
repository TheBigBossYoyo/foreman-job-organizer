# Presentation guide — Foreman AI Job Organizer (Option C)

10-minute talk, 5 minutes of questions. At 5 minutes: cut sections 4 and 7, one
demo sample only. At 15: expand section 6, take more questions.

---

## The one sentence

> A contractor's job record arrives as scattered texts, receipts and photo
> captions. This turns that into a structured timeline, and I can tell you how
> often it gets each field right.

Say it in the first fifteen seconds. The second half is what separates this from
a demo that looks good on one input.

---

## Slide plan

| # | Slide | Time |
|---|---|---|
| 1 | Title + one sentence | 0:30 |
| 2 | The problem | 1:00 |
| 3 | Live demo | 3:00 |
| 4 | How it works | 1:30 |
| 5 | How I know it works | 2:00 |
| 6 | The date experiment | 1:30 |
| 7 | What's left | 0:30 |

---

## 1. Title (0:30)

Name, track, host company, Option C. Then the one sentence. Don't read the slide.

## 2. The problem (1:00)

The input:

- A text from the client at 9pm asking a question
- A receipt photo with no date on it
- "lopez said he might swing by thursday pm"
- A supplier who called and would not give a firm date

The cost: none of it is searchable, and the details that matter for billing and
disputes live in someone's phone.

Key line: the hard part is not summarising the text. It is knowing which details
are in there and which ones you would be inventing.

## 3. Live demo (3:00)

Run it live. No video, no screenshot unless the app won't start.

1. `streamlit run app.py`
2. Sidebar → load `03_tricky_bathroom` → **Organize**
3. While it runs, say what it's doing: split into items, categorize, extract
   dates and amounts, quote the source line.
4. Point at three things:
   - **The timeline** — five items out of eight messy lines
   - **The flags** — items needing a human check are surfaced, not buried
   - **The warnings** — read one aloud
5. Show a `source_excerpt`. Every extracted fact traces to the line it came from.
6. Download the JSON. Same shape every time, validated by Pydantic.

Then load `04_tricky_painting` and point out that the client name comes back
`null`, because the sample never names a client:

> It would have been easy to make it guess "Wilson" from the project title. It
> used to do exactly that. Returning null is the correct answer.

## 4. How it works (1:30)

One slide, no code:

1. Take raw text
2. Build the prompt — instructions, schema, worked example, missing-data rule
3. Call the provider chain — Anthropic, then Groq, then no model at all
4. Slice the JSON out of the reply
5. Validate with Pydantic — categories, types, no negative amounts
6. Drop any date not written on the item's own source line
7. Enforce safety / missing-amount / PII rules in code
8. Aggregate timeline and totals — no second API call

Three points:

- **The chain degrades instead of dying.** Anthropic down → Groq. Both
  unreachable → a rule-based engine that needs no key and returns the same JSON.
  That engine is much worse, the app says so in red, and every result records
  which provider answered.
- **Temperature 0** — with the caveat in section 5.
- **Steps 6 and 7 are the interesting ones.**

### If asked about the merge

Two prototypes: yours and a teammate's port of a PHP web app. Merged rather than
chosen between. Kept from yours: scorer, answer key, source-line date check.
Taken from theirs: provider fallback, code-enforced guardrails, aggregation.

You declined their 13-category schema because adopting it would have invalidated
the answer key and made the new score incomparable with every earlier one.

## 5. How I know it works (2:00)

Slow down here.

"Looks about right" is not a result. The answers were written out by hand first,
then scored against.

- `data/expected/` — hand-written answers for all 8 samples
- `python -m src.score` — one command, reruns the whole count
- **214 fields**: 3 header fields per sample, then 5 per item
- `source_excerpt` is checked against the **sample text**, not the answer key.
  The wording is the model's choice; a quote that isn't in the input is invented.

| Measure | Result |
|---|---|
| Field accuracy | **192/214 (90%)** |
| Samples with no errors | 4/8 |
| Date fields correct | 36/38 |

**The number went down and that is the point.** It was 118/125 (94%) at five
samples. Three harder samples took it to 90%. The original five scored 118/125
again in the same run, so nothing regressed.

**Then the harder thing.** Temperature 0 is not deterministic. Three consecutive
runs scored 117, 118, 118. Larger swings happen when the model splits a line
into two items instead of one — every later item then matches the wrong answer
and the denominator moves. `python -m src.stability` measures both.

Volunteering this before anyone asks also protects you: if someone re-runs it
and gets a different number, you already said so.

## 6. The date experiment (1:30)

Strongest slide. Don't cut it.

Dates failed two ways: inventing a year (`7/27` → `2026-07-27`) and inheriting a
date from the line above.

| Attempt | Result |
|---|---|
| Baseline | 112/125 (90%) |
| Rewrote the prompt rule | 115/125 (92%) |
| Checked the date against the item's excerpt | **112/125 (90%)** |
| Checked the date against the item's source line | **118/125 (94%)** |

1. **The prompt fixed half of it.** Invented years stopped. Inheritance did not
   move — the model reads a dated line as a heading for the block below.
2. **A second prompt rewrite did nothing.**
3. **The first code fix made it worse.** Dropping any date not in the item's
   `source_excerpt` cost three fields, because the model quotes `Crew completed
   cabinet removal` and leaves the `2026-07-21 - ` off the front. The check
   deleted four correct dates.
4. **Checking the source line fixed it.** Find the line the quote came from and
   read the date off that. 22/22.

End on:

> Two prompt rewrites did not move it. Twenty lines of code fixed it completely.
> A rule the model has to remember is weaker than a rule the pipeline enforces.

## 7. What's left (0:30)

22 misses, 15 of them from one mistake: on `06_safety_incident` the model merged
a progress line and an injury line into one item. Items match by position, so
everything after it scored against the wrong entry.

The rest: five category disagreements, some genuinely arguable, and two missed
action flags.

Next: event splitting, and a scorer that can tell one merge from fifteen
mistakes.

---

## Questions to expect

**"Is 90% good?"**
Good for a first pass on deliberately messy input, and the number matters less
than what it's made of. No remaining error is an invented fact, which is the
failure mode that would actually hurt a contractor.

**"Why not just use regex?"**
Fair for amounts, and the date check *is* regex. The model does the part regex
can't: deciding that "lopez said he might swing by thursday pm to take a look"
is a scheduling item needing follow-up. Model for judgement, code for
verification.

**"What if the model returns garbage?"**
Three layers. JSON extraction handles a fenced or prefixed reply. Pydantic
rejects invented categories, wrong types, negative amounts. The batch runner
catches a failure per-sample and keeps going without leaving a half-written file.

**"How do you know it isn't memorising your samples?"**
With eight samples, I don't — that's the honest answer. Temperature is 0 and the
answer key was written before the outputs were scored. Expanding to 10 is the
next item.

**"Did you use AI to build this?"**
Yes. Then show what makes it yours: the commit history walks through decisions,
`PROJECT_NOTES.md` records why, and you can explain any line in `src/dates.py`
including why the first version was wrong. Section 6 is the proof — nobody
generates a change that lowers their own score and keeps it in the write-up.

**"Which model?"**
Anthropic Claude first, Groq as backup, rule-based engine below both.
`src/providers.py` is the whole abstraction. The measured numbers were run on
Groq, and every output file records which provider produced it.

**"What if the API is down during the demo?"**
It falls to the next provider. If everything is unreachable it returns a valid
result from the local engine, marked in red as keyword-matched. Tested path.

**"What would you do with more time?"**
Event splitting, then the scorer, then the action flags, then a tie-break rule
for the arguable categories written into the prompt and answer key together.

---

## Do not claim

- Not production-ready. It's a prototype.
- 90% is not an industry benchmark. It's 214 fields on 8 samples you wrote. Say
  the denominator every time you say the number.
- Don't compare your number to anyone else's unless you know their denominator.
- It doesn't handle photos or PDFs. It takes text.
- Never show real Foreman data. Everything in `data/samples/` is invented.

---

## Pre-flight checklist

Run this the morning of, not five minutes before.

- [ ] `python -m pytest` → 127 passed
- [ ] `python -m src.score` → 192/214
- [ ] `streamlit run app.py` opens and organizes a sample end to end
- [ ] `.env` has a working, unexpired key — test an actual run
- [ ] Phone hotspot ready in case venue wifi blocks the API
- [ ] A pre-generated output JSON open in a tab. If you fall back to it, say so
- [ ] Repo link works for whoever you send it to (private; collaborators must
      accept the invite first)
- [ ] Laptop charged, notifications off, terminal font size up

**If the live demo fails:** don't debug on stage. Say "the API call is timing
out, here's a run from this morning", open the saved JSON, keep going.
