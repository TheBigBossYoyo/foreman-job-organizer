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

| # | Section | Deck slides | Time | Who |
|---|---|---|---|---|
| 1 | Title + one sentence | 1 | 0:30 | ________ |
| 2 | The problem | 2 | 1:00 | ________ |
| 3 | **Live demo** | 3 | 3:00 | ________ |
| 4 | How it works | 4, 5 | 1:30 | ________ |
| 5 | How I know it works | 6, 7 | 2:00 | ________ |
| 6 | The date experiment | 8 | 1:30 | ________ |
| 7 | What's left | 9, 10 | 0:30 | ________ |

Everyone speaks — that is a rule, not a preference. Fill in the last column
before the first rehearsal and don't change it after. The deck is the artifact
link in the shared folder; these seven sections map onto its ten slides as
above.

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

## 3. Live demo (3:00) — the script

Rehearse this exact path. Not "roughly this" — this. Everything below was
checked against a real run on 12 August, so every figure named here is what will
actually be on the screen.

**Who drives:** _______________ runs the app. _______________ advances slides.
Both of you should be able to do either.

### Before you stand up

- App already running: `python -m streamlit run app.py`
- Browser at `localhost:8501`, sample **`03_tricky_bathroom.txt`** already
  selected in the sidebar, **not yet organized**
- Sidebar shows **Groq · active**, not Local engine
- `docs/screenshots/02-timeline.png` open in a second tab, behind the browser
- Terminal font up, notifications off

### The path

**1. Show the input first (0:20).** Expand **Job stream**. Do not read it out.
Say:

> Seven lines a foreman actually typed. One date, written "7/27" with no year.
> A photo filename. A text from the client. A supplier who wouldn't commit.

**2. Click Organize (0:15).** While it runs:

> It's splitting this into events, categorising each one, pulling out dates and
> amounts, and quoting the line each fact came from.

**3. The header (0:15).** Point at `Chen bathroom reno · Maya Chen · 44 Pine Ave`.

> Nothing in that input said "client:". It got the name out of "client is Maya
> Chen" and the address off the title line.

**4. The counter — this is the moment (0:35).** Point at **`5 of 5 · items
undated in the source`**.

> Every item says no date. The only date in the input is "7/27" with no year.
> Inventing 2026 there would have been the most plausible thing it could do, and
> it's the exact failure that costs a contractor a billing dispute. Five out of
> five, correctly refused.

**5. The low-confidence flag (0:25).** Point at the **Lopez site visit** row and
its `LOW CONFIDENCE` tag.

> "Lopez said he might be able to swing by Thursday PM." The model isn't sure,
> and it says so on the row instead of filing it as a booking.

**6. The source quotes (0:25).** Sweep a finger down the grey lines under each
item.

> Every row carries the input line it came from. Nothing here is a summary you'd
> have to take on trust — you can check any of it against the original in a
> second. That's also how we score it: a quote that isn't in the input is
> invented, and that's a fail.

**7. Open actions (0:20).** Point at the three checkboxes.

> Three things this job needs a human to do, pulled out of the middle of a text
> thread. That's the part that changes someone's afternoon.

**8. `04_tricky_painting` — the null (0:25).** Sidebar → `04_tricky_painting`
→ **Organize**. Point at the header, where the client name is blank.

> This sample never names a client. The project is "wilson interior painting",
> so guessing "Wilson" was right there — and it used to do exactly that. Coming
> back empty is the correct answer, and it's the behaviour we spent the most
> time on.

Then hand off. **Do not** open the JSON download unless asked; it costs 30
seconds and says less than the screen does.

### Optional beats — cut these first

Two extra things exist and both are good. Neither is worth going over ten
minutes for. Rehearse the talk without them, and add one back only if you land
under time twice in a row.

**9a. The job record (0:30).** Click **Download job record**, open it.

> That's one printable page: the timeline, the quote behind every entry, the
> outstanding work, and the warnings — printed, not hidden. It carries the date
> and which engine produced it. Slide two said the details that decide a billing
> dispute live in someone's phone. That's the thing you'd actually attach to an
> email.

**9b. The calendar (0:25).** Click **Download calendar**, and read the caption
under the button aloud — *"0 dated events, 3 to-dos with no due date. Nothing in
this job stream said when."*

> iCalendar has events and it has to-dos, and a to-do doesn't need a due date.
> So the ones we know the day for are events, and the rest are tasks with no
> deadline. To put "Thursday PM" on a calendar we'd have to pick a Thursday, and
> that's the thing we spent the week teaching it not to do.

**An alternative opening, if you'd rather show real input.** Sidebar → upload
`data/phone_exports/whatsapp_deck_build.txt`. It reads a WhatsApp export, and
the caption says what it did and did not use:

> Every line in that export has a send time on it, and we throw them away. One
> message was sent on the 5th saying "building control came round last tuesday".
> A send time tells you when someone typed it, not when the work happened.

This is the strongest answer to "would this work on real data", but it replaces
the `03` opening rather than adding to it. Pick one; don't do both.

### If it fails

Two failure modes, two responses. Rehearse both once.

- **Slow or timing out.** Wait five seconds, no longer. Then: *"the API's timing
  out — here's a run from this morning"*, switch to the screenshot tab, and keep
  going on the same script. The screenshot shows the same sample, so nothing you
  planned to say changes.
- **Falls back to the local engine** (red banner, sidebar shows Local engine).
  Do not hide it — it's a feature and it's on your slide:
  > That's the no-key fallback. It's keyword matching, it's much worse — 86/150
  > against the model's 118/125 — and the app says so in red rather than letting
  > a bad answer pass for a good one.

  Then switch to the screenshot for the rest of the demo.

**Never debug on stage.** No terminal, no restarting, no "that's odd". You have
a screenshot; use it and keep the clock.

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

- `data/expected/` — hand-written answers for all 10 samples
- `python -m src.score` — one command, reruns the whole count
- **265 fields**: 3 header fields per sample, then 5 per item
- `source_excerpt` is checked against the **sample text**, not the answer key.
  The wording is the model's choice; a quote that isn't in the input is invented.

| Measure | Result |
|---|---|
| Field accuracy | **241/265 (91%)** |
| Samples with no errors | 4/10 |
| Date fields correct | 44/47 |

**The number went down and that is the point.** It was 118/125 (94%) at five
samples. Three harder samples took it to 90%. The original five scored 118/125
again in the same run, so nothing regressed.

**Then the number went down for a second reason, and that one was our fault.**
The scorer matched items by position: item 1 against item 1, item 2 against item
2. When the model merged two lines into one item on `06`, every item after it
was compared against the wrong answer, and one mistake was charged fifteen
times. The scorer now aligns the two lists before comparing them.

On the *same eight samples*, that change alone read 192/214 → **201/214**, with
`06` going 13/28 → 22/28. The other seven came out identical field for field.
The model did not change. The ruler did.

Say this plainly, because it is the strongest thing on the slide: **fixing the
measurement was worth more than any prompt change we tried all week.**

Do **not** present 192/214 → 241/265 as an improvement. Two things moved at
once — the scorer, and the sample count going from 8 to 10. The like-for-like
figure is 192/214 → 201/214.

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

24 missed fields, but only **12 mistakes**: 3 segmentation errors and 9 field
errors. A segmentation error is one event merged or dropped and it costs five
fields at once, so the two counts are worth saying separately.

- **The merge on `06`** is still there and still the thing to fix: a progress
  line and an injury line in one item.
- **Two on `10_repeated_event`**, where the model folded each event that was
  stated twice into one item. That one is a disagreement, not a bug — see below.
- **Six category disagreements**, three of them genuinely arguable.
- **Two missed action flags**, one clear and one arguable.

**The open question, if you have thirty seconds for it.** On `10` the model
silently de-duplicated: the key expects four items, it returned two. We built
the fix — one item per event, with the other wording kept beside it — and it
made the model merge three *distinct* events on the dense sample, which had been
perfect. So we reverted it. The code is on a branch. A model free to decide what
counts as the same event will merge things that are only adjacent, and the fold
belongs in code rather than in the prompt.

That is the same lesson as the dates, for the fourth time.

---

## Questions to expect

**"Is 91% good?"**
Good for a first pass on deliberately messy input, and the number matters less
than what it's made of. No remaining error is an invented fact, which is the
failure mode that would actually hurt a contractor. Then give them the shape:
24 missed fields, 12 mistakes.

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
With ten samples, I don't — that's the honest answer. Temperature is 0 and every
answer key was written by hand before the outputs were scored. Expanding the set
is the obvious next step. Do not argue past this one.

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

**"You wrote the tool and the answer key. Isn't that marking your own homework?"**
Yes, and it's the main weakness of the measurement. Two things keep it honest:
the keys were written before anything was scored, and when we thought a key was
wrong we checked it against the input line rather than changing it. On `05` we
were sure the key was wrong about a photo — the raw line starts with `photo:`,
the key was right, and the model had dropped that prefix from its own quote
before classifying. We nearly edited ground truth to match a wrong answer.

**"What would you do with more time?"**
Decide the de-duplication question properly, in code rather than the prompt.
Then a warning when an input line isn't quoted by any item, so a merge surfaces
itself. Then the action flags, and categories decided in code wherever the input
gives a marker to decide on.

---

## Do not claim

- Not production-ready. It's a prototype.
- 91% is not an industry benchmark. It's 265 fields on 10 samples you wrote. Say
  the denominator every time you say the number.
- Don't compare your number to anyone else's unless you know their denominator.
- It doesn't handle photos or PDFs. It takes text.
- Never show real Foreman data. Everything in `data/samples/` is invented.

---

## Pre-flight checklist

Run this the morning of, not five minutes before.

- [ ] `python -m pytest` → 144 passed
- [ ] `python -m src.score` → 241/265
- [ ] `streamlit run app.py` opens and organizes a sample end to end
- [ ] `.env` has a working, unexpired key — test an actual run
- [ ] Phone hotspot ready in case venue wifi blocks the API
- [ ] `docs/screenshots/02-timeline.png` open in a second browser tab
- [ ] Sidebar reads **Groq · active**, not Local engine
- [ ] Sample `03_tricky_bathroom.txt` loaded and *not yet* organized
- [ ] Two full timed run-throughs done, demo included, both under 10 minutes
- [ ] Repo link works for whoever you send it to (private; collaborators must
      accept the invite first)
- [ ] Laptop charged, notifications off, terminal font size up

**If the live demo fails:** don't debug on stage. Section 3 has the exact words
for both failure modes. Rehearse them once each.
