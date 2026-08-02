# Presentation guide — Foreman AI Job Organizer (Option C)

Written for a **10-minute talk plus 5 minutes of questions**. If you get 5
minutes, cut sections 4 and 7 and shorten the demo to one sample. If you get 15,
expand section 6 and take more questions.

---

## The one sentence

> A contractor's job record arrives as scattered texts, receipts and photo
> captions. This turns that stream into a structured timeline, and I can tell
> you exactly how often it gets each field right.

Say this in the first fifteen seconds. Everything after it is evidence.

**The thing that makes this talk different from the other Option C talks is the
second half of that sentence.** Plenty of people will demo something that looks
good on one input. Very few will put a number on it, and fewer still will show
a change that made the number worse. Lead with the demo, but spend your best
minutes on the measurement.

---

## Slide plan

| # | Slide | Time | Purpose |
|---|---|---|---|
| 1 | Title + one sentence | 0:30 | Frame it |
| 2 | The problem | 1:00 | Why anyone should care |
| 3 | **Live demo** | 3:00 | Show it works |
| 4 | How it works | 1:30 | Show you understand it |
| 5 | **How I know it works** | 2:00 | The differentiator |
| 6 | **The date experiment** | 1:30 | The story that proves rigour |
| 7 | What's left | 0:30 | Honesty + Week 4 |

---

## 1. Title (0:30)

Name, track, host company, Option C. Then the one sentence above. Do not read
the slide.

## 2. The problem (1:00)

Describe the input honestly — this is the part a construction PM will recognise
instantly:

- A text from the client at 9pm asking a question
- A receipt photo with no date on it
- "lopez said he might swing by thursday pm"
- A supplier who called and would not give a firm date

Then the cost: none of that is searchable, nothing is a record, and the details
that matter for billing and disputes live in someone's phone.

**Land this line:** the hard part is not summarising the text. It is knowing
which details are actually in there and which ones you would be inventing.

## 3. Live demo (3:00)

Run it. Do not show a video, and do not show a screenshot if the app can run.

**Script:**

1. `streamlit run app.py`
2. Sidebar → load `03_tricky_bathroom` → **Organize job**
3. While it runs, say what it is about to do: split the stream into items,
   categorize each one, pull out dates and amounts, quote the source line.
4. When it lands, point at three things and only three:
   - **The timeline.** Five items out of eight messy lines.
   - **The review banner.** "N items need a human check" — items with a missing
     date or low confidence are surfaced, not buried.
   - **The warnings.** Read one aloud. This is the missing-data rule working.
5. Expand one item and show the `source_excerpt`. Say: *every extracted fact is
   traceable to the line it came from.*
6. Download the JSON. One click. Say it is the same shape every time, validated
   by Pydantic, so something else could consume it.

**Then do the honest bit.** Load `04_tricky_painting` and point out that the
client name comes back `null`, because the sample never names a client. Say:

> It would have been easy to make it guess "Wilson" from the project title. It
> used to do exactly that. Returning null is the correct answer.

That single moment is worth more than any feature you could add.

## 4. How it works (1:30)

Seven steps, one slide, no code on screen:

1. Take raw text
2. Build the prompt — instructions, schema, worked example, missing-data rule
3. Call the model (Groq, `llama-3.3-70b-versatile`, temperature 0)
4. Slice the JSON out of the reply
5. Validate with Pydantic — categories, types, no negative amounts
6. **Drop any date not written on the item's own source line**
7. Return, or fail with the reason

Two design points worth saying out loud:

- **Temperature 0.** The same input gives the same output twice. Without that,
  the accuracy number moves between runs and means nothing.
- **Step 6 is the interesting one** — that is your next slide.

## 5. How I know it works (2:00)

This is the slide to slow down on.

**Set it up:** "Looks about right" is not a result. So I wrote the answers out
by hand first, then scored against them.

- `data/expected/` — hand-written answers for all 5 samples
- `python -m src.score` — one command, reruns the whole count
- **125 fields**: 3 header fields per sample, then 5 per item across 22 items
- The `source_excerpt` field is checked against the **sample text**, not the
  answer key — the wording is the model's choice, but a quote that is not in
  the input is fabricated

| Measure | Result |
|---|---|
| Field accuracy | **118/125 (94%)** |
| Samples with no errors | 2/5 |
| Date fields correct | **22/22** |

**Say the gap out loud:** 94% of fields are right but only 2 of 5 documents are
completely clean, because errors spread thin instead of piling up in one bad
sample. A per-document number would have been 40% and would also have been true.
Be the person who noticed that.

## 6. The date experiment (1:30)

**This is your strongest slide. Do not cut it.**

Dates were the weakest field, failing two ways: inventing a year (`7/27` became
`2026-07-27`) and inheriting a date from the line above.

| Attempt | Result |
|---|---|
| Baseline | 112/125 (90%) |
| Rewrote the prompt rule | 115/125 (92%) |
| Checked the date against the item's excerpt | **112/125 (90%)** |
| Checked the date against the item's source line | **118/125 (94%)** |

Walk the four rows:

1. **The prompt fixed half of it.** Invented years stopped. Inheritance did not
   move at all — the model reads a dated line as a heading for the block below.
2. **A second prompt rewrite did nothing.** That is when I stopped writing rules
   and started enforcing them.
3. **My first code fix made it worse.** I dropped any date not found in the
   item's `source_excerpt`. It cost three fields, because the model quotes
   `Crew completed cabinet removal` and leaves the `2026-07-21 - ` off the
   front. The check could not see real dates and deleted four correct ones.
4. **Checking the source line fixed it.** Find the line the quote came from and
   read the date off that — the prefix is still there. 22/22 dates correct.

**The line to end on:**

> Two prompt rewrites did not move it. Twenty lines of code fixed it completely.
> A rule the model has to remember is weaker than a rule the pipeline enforces.

If you only land one idea in the whole talk, land that one.

## 7. What's left (0:30)

Seven misses, none of them dates. Five are category disagreements and some are
genuinely arguable — whether "demo done, there is moisture behind it" is a
contractor update or an issue is a judgement call, and that judgement is mine,
sitting in `data/expected/`. If you disagree, the fix is to change the answer
key, not the code.

Two are missed action flags, which are simply wrong. That is the next target.

---

## Questions you should expect

**"Is 94% good?"**
It is good for a first pass on deliberately messy input, and the number matters
less than what it is made of. Every remaining error is either a judgement call
or an action flag. Zero are invented facts, which is the failure mode that would
actually hurt a contractor.

**"Why not just use regex? Dates and dollar amounts are structured."**
Fair for the amounts, and in fact the date check is regex. But the model is
doing the part regex cannot: deciding that "lopez said he might swing by
thursday pm to take a look" is a scheduling item that needs a follow-up. The
useful architecture turned out to be both — model for judgement, code for
verification.

**"What happens if the model returns garbage?"**
Three layers. JSON extraction handles a fenced or prefixed reply. Pydantic
rejects invented categories, wrong types, negative amounts. The batch runner
catches a failure per-sample and keeps going, and it does not leave a
half-written file behind — that is a test, not a claim.

**"How do you know it isn't just memorising your samples?"**
I don't, with five samples. That is the honest answer, and expanding the test
set to 8-10 is the first thing in the Week 4 plan. What I can say is that
temperature is 0, so the runs are reproducible, and the answer key was written
before the outputs were scored.

**"Did you use AI to build this?"**
Yes, and say so plainly. Then show what makes it yours: the commit history walks
through decisions, `PROJECT_NOTES.md` records why each one was made, and you can
explain any line in `src/dates.py` including why the first version was wrong.
The failed attempt in section 6 is the proof — nobody generates a change that
lowers their own score and then keeps it in the write-up.

**"Why Groq and llama rather than GPT or Claude?"**
Free tier, fast, and it does structured JSON output natively. The provider is
one function (`call_groq` in `src/organizer.py`) — swapping it is a small change,
and the prompt and validation would not move.

**"What would you do with more time?"**
In order: more test samples, then the action flags, then a tie-break rule for
the arguable categories written into the prompt and the answer key together.

---

## Do not claim

- **Do not call it production-ready.** It is a measured prototype. Say that.
- **Do not present 94% as an industry benchmark.** It is 125 fields on 5 samples
  you wrote. Say the denominator every time you say the number.
- **Do not compare your number to anyone else's** unless you know their
  denominator. A different answer key is a different exam.
- **Do not claim it handles photos or PDFs.** It takes text.
- **Never show real Foreman data.** Everything in `data/samples/` is invented,
  and the privacy rule is in the README and the app sidebar. Point at it if
  anyone asks.

---

## Pre-flight checklist

Run through this the morning of, not five minutes before.

- [ ] `python -m pytest` → 42 passed
- [ ] `python -m src.score` → 118/125
- [ ] `streamlit run app.py` opens and organizes a sample end to end
- [ ] `.env` has a **working, unexpired** key — test an actual run, not just that
      the file exists
- [ ] Phone hotspot ready in case the venue wifi blocks the API
- [ ] A pre-generated output JSON open in a tab, so a failed API call does not
      end the demo — if you fall back to it, say you are falling back to it
- [ ] Repo link works for whoever you send it to (it is private; collaborators
      must accept the invite first)
- [ ] Laptop charged, notifications off, terminal font size up

**If the live demo fails:** do not debug on stage. Say "the API call is timing
out, here is a run from this morning," open the saved JSON, and keep going. The
measurement slides are the strongest part of the talk anyway, and staying calm
reads better than a fix.
