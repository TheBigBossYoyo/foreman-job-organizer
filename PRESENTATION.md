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

Twelve slides, about ten minutes, then questions. One idea per slide.

| Slide | What it covers | Time | Who |
|---|---|---|---|
| 1 | Title and the one sentence | 0:25 | ________ |
| 2 | The problem, on sample 03 | 0:40 | ________ |
| 3 | **LIVE DEMO** | 3:00 | ________ |
| 4 | Inputs and outputs | 0:40 | ________ |
| 5 | The pipeline, module by module | 0:55 | ________ |
| 6 | Date grounding | 0:45 | ________ |
| 7 | Guardrails | 0:35 | ________ |
| 8 | The scorer | 0:45 | ________ |
| 9 | Results | 0:35 | ________ |
| 10 | The date experiment | 0:45 | ________ |
| 11 | The experiment that failed | 0:35 | ________ |
| 12 | Limits and next | 0:30 | ________ |

That totals 10:00 with nothing spare. **Rehearse with a timer from the first
run, not the third.**

**Cut order if you are over.** Take them in this order and stop when you fit:

1. Slide 7 (guardrails) — fold one line of it into slide 5
2. Slide 4 (inputs and outputs) — the demo already showed them
3. The `04_tricky_painting` beat inside the demo, saving 25 seconds
4. Slide 11 (the failed experiment)

**Never cut** slides 6 and 10. Date grounding and the date experiment are the
technical core of the project, and slide 10 is the one that shows you kept a
change that lowered your own score.

Everyone speaks. Fill in the last column before the first rehearsal and do not
change it afterwards.

---

## 1. Title (0:25)

Name, track, host company, Option C. Then the one sentence. Don't read the slide.

## 2. The problem (0:40)

The input:

- A text from the client at 9pm asking a question
- A receipt photo with no date on it
- "lopez said he might swing by thursday pm"
- A supplier who called and would not give a firm date

The cost: none of it is searchable, and the details that matter for billing and
disputes live in someone's phone.

Key line: the hard part is not summarising the text. It is knowing which details
are in there and which ones you would be inventing.

## 3. LIVE DEMO (3:00) — full script

Every figure below was checked against a real run on 12 August. Say the words,
not an improvisation of the words. The demo is the only part of the talk where
improvising costs you the clock.

**Driving:** ________________ has the keyboard. ________________ advances slides.
Both of you rehearse both jobs.

### Set up before you stand (do this while the previous team presents)

- [ ] `python -m streamlit run app.py`, browser at `localhost:8501`
- [ ] Sidebar sample set to **`03_tricky_bathroom.txt`**, **not yet organized**
- [ ] Sidebar providers panel shows **Groq · ACTIVE** (not Local engine)
- [ ] Second browser tab: `docs/screenshots/02-timeline.png`
- [ ] Third tab: `docs/screenshots/04-job-record.png`
- [ ] Browser zoom at 110%, notifications off, laptop on mains

### 0:00 — the input (20 seconds)

Click the **Job stream** expander. Do not read it aloud.

> This is seven lines out of a bathroom renovation. A foreman typed these on a
> phone, on site. There is one date in there, written seven-slash-twenty-seven,
> with no year. There is a photo, which is a filename. Two lines are other
> people talking. And a supplier who would not commit to a date.

### 0:20 — run it (15 seconds)

Click **Organize**. While the spinner runs:

> It is splitting this into separate events, giving each one a category, pulling
> out dates and amounts, and quoting the line every fact came from.

### 0:35 — the header (15 seconds)

Point at `Chen bathroom reno · Maya Chen · 44 Pine Ave`.

> Nothing in that input says "client colon". It took the name out of "client is
> Maya Chen" and the address off the end of the title line.

### 0:50 — the counter (35 seconds) — THE MOMENT

Point at **`5 of 5 · items undated in the source`**.

> Every single item says no date. The only date in that input was
> seven-slash-twenty-seven with no year on it, and the tool refused to turn that
> into a 2026 date.
>
> That refusal is the whole project. Guessing 2026 would have been right most of
> the time, and the times it was wrong would be a contractor arguing about an
> invoice with a date nobody wrote down.

Pause here. This is the line the rest of the talk pays off.

### 1:25 — low confidence (25 seconds)

Point at the **Lopez site visit** row and its `LOW CONFIDENCE` tag.

> "Lopez said he might be able to swing by Thursday PM." The model is not sure
> what that is, and it marks the row instead of filing a booking. That flag came
> from the model. The urgent flag on a safety item does not, and I will come back
> to that.

### 1:50 — the source quotes (25 seconds)

Run a finger down the grey lines under the items.

> Under every row is the line of input it came from. You can check any row
> against the original in about two seconds. That is also how it is scored: the
> quote has to appear in the input text, and a quote that does not is counted as
> invented.

### 2:15 — open actions (20 seconds)

Point at the three checkboxes.

> Three things this job needs a person to do, pulled out of the middle of a text
> thread. On a Friday afternoon that list is the thing a foreman actually wants.

### 2:35 — the job record (25 seconds)

Click **Download job record**, open the file.

> One printable page. Timeline, the quote behind every entry, the outstanding
> work, and the warnings printed on it rather than hidden. It carries the date it
> was made and which engine made it.
>
> Slide two said the details that decide a billing dispute live in someone's
> phone. This is the thing you would attach to an email.

Scroll to the warnings block, then close the tab.

### 3:00 — hand off

Do not open the JSON. Do not open the calendar unless you are under time; if you
are, the calendar beat is below.

---

### Optional beat A — the calendar (25 seconds)

Only if you reach 3:00 with time in hand. Click **Download calendar**, then read
the caption under the button aloud:

> *"0 dated events and 3 to-dos with no due date. Nothing in this job stream said
> when, so nothing was given a day."*

> iCalendar has events and it has to-dos, and a to-do does not need a due date.
> Anything with a real date becomes an event. Everything else becomes a task with
> no deadline. Putting "Thursday PM" in a calendar means choosing a Thursday, and
> that is the one thing this tool will not do.

### Optional beat B — `04_tricky_painting` (25 seconds)

Sidebar → `04_tricky_painting` → **Organize**. Point at the empty client name.

> That sample never names a client. The project is called "wilson interior
> painting", so guessing "Wilson" was sitting right there, and an earlier version
> did exactly that. Coming back empty is the correct answer.

### Optional opening — the phone export

**This replaces the sample-03 opening. Do not do both.** Sidebar → upload
`data/phone_exports/whatsapp_deck_build.txt`, then read the caption:

> Eight messages from three people. Every line in that export has a send time on
> it, and we throw all of them away. One of those messages was sent on the fifth
> and says "building control came round last Tuesday". A send time tells you when
> somebody typed a message, not when the work happened.

Then click **Organize** and continue from the 0:35 beat.

---

### If it breaks

Rehearse both of these once each, out loud.

**It is slow or times out.** Count five seconds. Then:

> The API is timing out — here is the same sample from this morning.

Switch to the `02-timeline.png` tab and carry on with the identical script. The
screenshot is the same sample, so not one word of the demo changes.

**It falls back to the local engine** (red banner, sidebar shows Local engine).
Say it out loud rather than hiding it:

> That is the no-key fallback engine. It matches keywords instead of reading, it
> scores 86 out of 150 against the model's 118 out of 125, and the app says so in
> red rather than letting a bad answer pass for a good one.

Then switch to the screenshot for the rest.

**Never** open a terminal, restart anything, or say "that's odd". You have two
screenshots and a script. Use them and keep the clock.

## 4. Inputs and outputs (0:40)

Two ways in, four ways out, none of the four needing a network.

**In.** Pasted text, or a phone chat export read by `src/phone_import.py`. Say
the thing about timestamps, because it is the same argument as slide 6 and it
lands twice:

> Every line of a WhatsApp export has a send time on it. We throw them away. One
> message in our sample was sent on the fifth and says "building control came
> round last Tuesday". A send time records when somebody typed something, not
> when the work happened.

**Out.** Timeline on screen, JSON, an `.ics` calendar, and a printable job
record. The calendar is the one worth a sentence:

> A written date becomes an event. An action with no date becomes a to-do with
> no due date. On the sample we just ran, that is three to-dos and no events at
> all.

If asked why not Google Calendar directly: the tool would have to resolve
"thursday pm" into a real Thursday to fill one, and it exists to not do that.

## 5. The pipeline (0:55)

Eight stages, and the model runs in one of them. Do not read the slide out; name
the two that matter.

- **`providers.py`** — Anthropic `claude-haiku-4-5`, then Groq
  `llama-3.3-70b`, then a rule-based engine needing no key. `temperature=0`,
  `max_tokens=2000`. `AI_PROVIDER` pins one so the scorer can measure a single
  engine.
- **`schema.py`** — Pydantic. Category is a `Literal` of ten values, so an
  invented category fails validation rather than reaching the screen. `amount`
  is `float, ge=0`.
- **`dates.py` and `guardrails.py`** are stages five and six, and neither asks
  the model for anything.

### If asked about the merge

Two prototypes existed: this one, and a teammate's Python port of a PHP web app.
They were merged rather than chosen between. Kept from here: the scorer, the
answer key, the source-line date check, the Pydantic contract. Taken from there:
the provider chain, guardrails in code, the aggregation layer.

Declined: their 13-category schema, because adopting it would have invalidated
every answer key and made the new score incomparable with every earlier one. Also
declined their split-on-blank-lines chunker, which fused five events into one
item on the dense sample.

## 6. Date grounding (0:45)

The technical core. Four steps, and the third one is the whole trick:

1. Take the item's `source_excerpt`
2. Find the input line it came from, matching in either direction, minimum eight
   characters
3. Test the model's date **against that line**
4. No match: null the date and write a warning naming the item

Six written forms are accepted, down to a bare `7/23` with no year, because the
question is whether the date was read off this line or imported from another.

> The excerpt is the model's rewrite of the line. The line is what the input
> actually said.

## 7. Guardrails (0:35)

Enforced in code after the model has finished, not requested in the prompt.

- Injury words set priority to urgent and move a vague category to `issue`
- A `receipt` or `payment` with no amount is flagged
- Five PII patterns are redacted from title and summary, with a note that the
  source excerpt still holds the original so a human can verify

The one worth saying out loud:

> A missing date is deliberately not flagged. It fired on most items in a real
> job stream, and a warning that appears everywhere stops being read.

## 8. The scorer (0:45)

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

## 9. Results (0:35)

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

## 10. The date experiment (0:45)

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

## 11. The experiment that failed, and 12. Limits (1:05)

24 missed fields, but only **12 mistakes**: 3 segmentation errors and 9 field
errors. A segmentation error is one event merged or dropped and it costs five
fields at once, so the two counts are worth saying separately.

- **The merge on `06`** is still there and still the thing to fix: a progress
  line and an injury line in one item.
- **Two on `10_repeated_event`**, where the model folded each event that was
  stated twice into one item. That one is a disagreement, not a bug — see below.
- **Seven category disagreements**, three arguable and four wrong. Three of the
  four are the same prompt rule over-firing, which is the interesting part.
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
