# Project decisions

## Chosen build
Option C — Job Organizer.

## Problem statement
Contractors receive job information as scattered messages, receipts, photo
captions, delivery notices and informal updates. This tool turns that into a
structured timeline, lists open actions, and keeps the source excerpt for each
item so a human can check it.

## Input
Plain text containing one or more job updates.

## Output fields
- Project name
- Client name
- Property address
- Categorized timeline items
- Date
- People
- Location
- Amount and currency
- Title and summary
- Action required
- Recommended action
- Priority
- Confidence
- Source excerpt
- Open actions
- Overall summary
- Warnings

## Accuracy rule
An item is correct when its category, extracted facts, action flag and source
excerpt agree with the input, with nothing invented.

## Missing-data rule
Return null and add a warning. Never guess.

## Week 4 status

**Interface** — done. Text box, timeline, open actions, JSON download, sample
picker.

**Scoring** — done. `python -m src.score` prints the field count and the miss
list.

**Test set** — done, 5 to 8.

| Sample | Tests | Result |
|---|---|---|
| 06_safety_incident | injury language, safety guardrail | 13/28 |
| 07_two_currencies | TND and USD in one job | 28/28 |
| 08_dense_stream | no blank lines | 33/33 |

Answer keys written by hand before running the model.

Score: 118/125 (94%) → **192/214 (90%)**. The original five scored 118/125
again in the same run. The whole drop is 06.

**Dates** — done, 22/22 on the original five. `src/dates.py` drops any date not
written on the item's own source line.

The first version compared against `source_excerpt` and dropped the score to
112/125, because the model's quote omits the date prefix. The source line is
what the input said; the excerpt is what the model chose to write.

Two prompt rewrites did not change date inheritance. Twenty lines of code
stopped it. Rules the pipeline enforces beat rules the model is asked to follow.

## The merge

Two prototypes lived in this repo for a day: this one and a teammate's Python
port of a PHP web app. Merged rather than chosen between.

Kept from here: scorer and answer key, source-line date check, Pydantic
contract, batch runner.

Taken from there: provider chain with no-key fallback, guardrails enforced in
code, aggregation layer.

Declined: their 13-category schema and their samples. Adopting either would
have invalidated `data/expected` and made the score incomparable with 112, 115
and 118.

Also declined: their split-on-blank-lines chunker. It fused five events into
one item on a dense sample. None of their own samples could catch it — every
one has a blank line between entries.

## Reproducibility

Temperature 0 is not deterministic. Three consecutive runs of the same five
samples scored 117, 118, 118. A one-field change is noise.

"118 ± 1" only holds while the item count holds. One batch run split
03_tricky_bathroom into six items where ten other runs gave five, by cutting
this line in two:

    7/27 demo done. opened up the shower wall and there is moisture behind it

The scorer matches items by position, so the extra item shifted every later
field and moved the denominator. That run scored the original five at 114/130
(88%) instead of 118/125 (94%). Same code, same input.

Two kinds of variation, different sizes:

- **field noise** — about ±1, what 117/118/118 measured
- **segmentation change** — rare, worth several fields and a moved denominator

`python -m src.stability --runs N` measures both. Item counts held identical
across three runs of all eight samples and six more of 03.

## Week 5 — the scorer, and what it changed

The scorer no longer matches items by position. It aligns them first
(Needleman-Wunsch, scored on field agreement, order preserved) and reports two
kinds of error separately.

| | Before | After |
|---|---|---|
| Samples | 8 | 10 |
| Field accuracy | 192/214 (90%) | **241/265 (91%)** |
| Same eight samples, scorer change alone | 192/214 | **201/214** |
| Clean samples | 4/8 | 4/10 |

The nine recovered fields are all on 06, which went 13/28 → 22/28. The other
seven samples came out identical field for field, and the original five scored
118/125 for the third run running. The model did not improve. The ruler was
wrong.

Error shape across the ten: **3 segmentation errors, 9 field errors.** That
sentence is the reason for the change — 24 misses reads like 24 problems, and it
is 12.

Every date on an item the model produced is correct (44/47 date fields; the
three losses are items that were never produced).

## Category misses — wrong vs arguable

Re-done against the current outputs on 12 August. The first version of this
section was written before the tie-break rules went into the prompt and listed
three misses the rules then fixed — `03` lopez, `09` tile guy and `05` photo are
all correct now and none of them appears in the miss list any more. A triage
that names misses which no longer exist sends the next reader hunting for
nothing, so it is replaced rather than appended to.

Seven category misses. Every one read against the input line, not against the
model's own excerpt.

**Arguable — 3.** No action. Recorded so nobody re-opens them as bugs.

- `03` "7/27 demo done. opened up the shower wall and there is moisture behind
  it" — one line, two events. Key says issue, model says contractor_update.
- `03` "vanity - supplier called, delayed, wouldnt give me a firm date" — key
  delivery, model issue. A delayed delivery is both.
- `06` "still need to hear back from the supply house about capping the strap
  ends" — key contractor_update, model issue. An open safety follow-up.

**Model wrong — 4, and three of them are one rule.**

- `04` "need to confirm bedroom color before we keep going" — key issue, model
  **schedule**. The line is a blocker, not a statement about timing.
- `07` "slab poured, five days to cure before we lay anything" — key
  contractor_update, model **schedule**. The line reports work done; the curing
  time is a note on it.
- `05` "can you send me the revised completion date" — key client_update, model
  **schedule**. The client is asking, so it is a client update whatever it asks
  about.
- `05` "inv 1048 PAID $1,250.00" — key payment, model receipt. Not the rule,
  just wrong: the line says PAID.

### What that pattern means

The `schedule` tie-break added in run B says a line is schedule when its point
is when something will happen. It fixed the two misses it was written for, and
it now accounts for **three of the four wrong categories** — a blocker, a
progress note and a client question, none of which is about timing.

This is sharper than what was recorded at the time. The conclusion then was that
the rules "moved the items they named and shuffled others", inside the ±1 band.
It was not shuffling. The rule was systematically over-applying, and the total
stayed flat because it fixed as many as it broke. A flat score hid a real
regression, which is an argument for reading the miss list and not only the
number.

The precedence qualifier from run C was supposed to stop exactly the `05` case
and did not, which was already recorded and now has a third confirmation.

**Keys changed: none**, in either pass. Two looked wrong until the source line
was read.

## What the tie-break rules did

Two rules went into the prompt: a photo marker at the start of a line wins over
whatever the caption says, and a line about when something happens is schedule
even with no date.

| Run | Prompt | Score | Clean |
|---|---|---|---|
| A | before | 240/265 | 4/10 |
| B | + the two rules | 242/265 | 5/10 |
| C | + client_update takes precedence | **241/265** | 4/10 |

All three named misses were fixed, in both runs after the change. Nothing else
held still. Run B lost a source_excerpt on 06; run C lost a payment on 05 and a
category on 07, and did not fix the thing the qualifier was written for — a
client asking for a completion date is still filed as schedule.

So: the total moved 240 → 242 → 241, which is inside the ±1 already measured for
this set. The rules moved the items they named and shuffled others. Nothing here
justifies claiming the score went up.

This is the date lesson for the third time. Date grounding was moved into code
and has not regressed since. Category rules live in the prompt and hold only on
the examples they quote. The fix, when someone has time, is the same shape:
decide categories in code where the input gives a marker to decide on.

Stopped at run C rather than trying a fourth prompt. Re-rolling until the number
looks better is how a measurement stops meaning anything.

## The de-duplication question — built, measured, reverted

`10_repeated_event` states an inspection twice and a delivery twice, in
different words. The answer key expects four items. The model returned two: it
recognised each restatement and folded it in. That was both segmentation errors
on that sample and most of the gap between 91% and higher.

This was written up as an open question needing a person rather than a commit.
It got one, and the answer is on the branch `restatements-experiment`.

**What was built.** The third option, rather than either side of the argument:
one item per event, with every other wording kept beside it. A `restatements`
field on the item, holding the later wordings as quotes. `src/restatements.py`
checks each one against the input and drops any the input does not support, the
same shape as date grounding — the model proposes the fold, the input decides
whether the line exists. The timeline gained a "said twice" pill and stacked the
folded lines under the line they repeat, so nothing said is off the screen.

**It worked on the sample it was designed for.** `10` went 13/23 to 13/13, both
folds captured and verified, and date grounding still caught the model copying
the inspection's date onto the delivery.

**It broke `08_dense_stream`, which was 33/33 and scored 22/33.** The model used
`restatements` as a bucket for related lines rather than repeated ones:

    crew arrived 7am, stripped the old batts out
      folded: skip delivered same morning, half full by lunch
      folded: found knob and tube wiring in the north bay, stopped work

Those are three events — a start, a delivery and an issue — not one event said
three times. This is the argument the key was making, demonstrated: a model free
to decide what counts as the same event will merge things that are merely
adjacent. It landed on the dense sample, which is also where the other
prototype's blank-line chunker failed.

| | Before | With the fold |
|---|---|---|
| Field accuracy | 241/265 (91%) | 232/255 (91%) |
| `08_dense_stream` | 33/33 | **22/33** |
| `10_repeated_event` | 13/23 | 13/13 |
| Segmentation errors | 3 | 3 |

The headline percentage is unchanged and the tool is worse. Reverted.

**A second finding on the way through.** The first run of the change had the
model quoting `framing crew on site, north wall studs up, Dave cut his forearm
on a strap end` on `06` — two input lines spliced together with a comma, a
string that is nowhere in the sample. Asking it to quote restatements exactly
taught it to build quotes. A rule was added that a `source_excerpt` must be
continuous text from one line, which fixed it. Worth remembering: this project
claims in three places that no remaining error is an invented fact, and one
prompt rule was enough to make that false.

**Kept honest:** the worked example in the prompt rule used "the permit came
through" rather than anything from `data/samples`. Teaching a rule with the text
it will be scored on is not a measurement.

**Where this leaves the question.** The key stays at four items. If someone
picks this up, the fold belongs in code, not in the prompt — decided after the
model returns, by comparing two items against each other, with anything it
rejects surfaced as a warning rather than silently dropped. That is the date
lesson for the fourth time.

## action_required — read, and left alone

The two misses, both the model saying false where the key says true.

- `04` "living room done except touch ups" — **key right, model wrong.** The line
  names outstanding work in its own words. Nothing arguable about it.
- `03` "lopez said he might be able to swing by thursday pm" — **arguable.** The
  key reads an unconfirmed visit as something to chase. The model reads it as
  someone else's intention with nothing asked of the contractor. Both defensible.

**Changed nothing.** One clear miss is not worth a prompt rule, and today's
de-duplication experiment is the strongest evidence yet for why: a rule written
to fix named items fixed them and broke a sample that had been perfect. Rule 7
would need "unfinished work" added to its list, which is exactly the shape of
change that has moved the total inside the noise band every time it has been
tried. The reading is recorded so nobody re-opens it as an unexamined bug.

## The 06 result

The model merged these two lines into a single item titled "Framing progress and
injury":

    2026-08-03 - framing crew on site, north wall studs up
    Dave cut his forearm on a strap end, first aid kit used, he finished the day

Five expected items line up against four actual ones. Under position matching
that read as fifteen wrong fields and 13/28. Aligned, it reads as what it is:
one segmentation error and one category disagreement, 22/28. The merge is still
there and still the thing to fix.

Three things worked in the same sample:

- the safety guardrail fired on the injury and on the photo of the strap, and
  raised both to urgent — not asked for in the prompt
- the model put 2026-08-03 on three items that do not state it; date grounding
  dropped all three with warnings
- the photo of the strap now keeps `action_required: false` while still carrying
  the safety flag, confirmed on a real run. Documentation of a hazard is not
  itself a task; the action lives on the injury line and the capping follow-up

## Done from the plan

1. **Scorer reports error shape.** Aligned instead of positional. Done.
2. **Re-scored and recorded.** 241/265. Done.
4. **Samples 09 and 10.** Added by @vjvidhaan, answer keys written first. Done —
   and 10 produced the de-duplication question above, which is the most
   interesting thing to come out of the week.
6. **Category triage.** Sorted into wrong and arguable, tie-break rules written
   into the prompt, measured. Done, and the result argues against the method.

## Next

**3. Check item count in code.** Superseded — see "This evening". Counting
lines was measured and rejected; coverage replaced it.

**5. action_required.** Done — read, and left alone. See above.

**7. Stability at 10 runs.** Three runs of eight is thin. Worth doing only if
someone has API budget spare. Not done.

**The de-duplication decision.** Done. Built, measured, reverted. See above.

**The line coverage warning.** Still the right next thing and deliberately not
built today. It only adds warnings, but it would want a batch re-run to be worth
anything, and this morning already produced one regression from a change that
looked safe. The freeze is the point. `coverage.py` in the scratchpad notes has
the measured version; `providers.HEADER_PATTERNS` is the header fix it needs.

Build froze Wednesday, 12 August, after the de-duplication experiment came back
and was reverted. `main` was 241/265 with 144 tests.

## After the freeze — three outputs, and why they were allowed

The freeze said bug fixes only, and then three features went in anyway. Worth
recording why, because "we froze and then didn't" is the kind of thing that
should not be discovered later in a commit log.

The de-duplication regression came from changing the **prompt**, which is
upstream of everything: it moves what the model returns, so it moves the score,
the outputs and the tests. These three read a finished result and write a file.
They cannot change a single output and they cannot move 241/265 — verified after
each one. That is a different category of risk from what broke `08` this
morning, and it is the reason the freeze bent rather than broke.

What it does still cost is talk time, which is the real budget now. Ten minutes,
and the packet says running long is the most common failure. All three are demo
beats rather than slides, and all three are the first things to cut.

**1. Calendar export (`src/calendar_export.py`).** A grounded date becomes a
VEVENT; an action with no date becomes a VTODO with no DUE; anything else is
left out. iCalendar already had the right answer, so nothing has to be guessed.
On `03` that is three to-dos and no events, and the page says so in words. This
is the date rule turning up somewhere a reader feels it rather than a claim in a
README.

**2. Job record (`src/job_record.py`).** One printable page per job. This is the
first thing built that answers slide two on its own terms — the details that
decide a dispute live in someone's phone, and JSON does not fix that. Warnings
are printed rather than hidden behind an expander, and the page carries the date
and the engine that produced it. A record that cannot be checked should not be
mistaken for one that can.

**3. Phone import (`src/phone_import.py`).** Reads a WhatsApp export, which is
the shape a job record actually arrives in. The decision worth defending is the
timestamps: an export stamps every line with a send time, and using it would
fill in the dates two thirds of the items lack — wrongly. The sample has a
message sent on the 5th saying "building control came round last tuesday". Send
times say when something was typed, not when it happened. They are reported to
the person importing and never written into the stream.

Its sample lives in `data/phone_exports/`, not `data/samples/`, on purpose: the
scored set stays at ten and the denominator does not move.

The line all three hold: **more ways in and out, no new ways to guess.**

`main` is 241/265 with 212 tests.

## This evening

Last working session before the freeze. Ordered so that stopping early still
leaves the repo in a presentable state.

**1. Line coverage detector.** This replaces "check the item count", which was
tried this afternoon and does not work. Measured on all ten samples: a threshold
of "lines minus items greater than one" catches 10, misses 06 entirely, and
false-fires on 03 and 05. Lines are not events — the answer keys themselves fold
7 lines into 5 items on 03.

What does work is coverage rather than counting: every non-header input line
should be quoted by some item's `source_excerpt`. A merged or dropped event
leaves its own line unquoted. Measured on the same ten, it names the exact
merged line on 06 and both dropped duplicates on 10.

The false positives it currently has are a header bug, not a flaw in the idea:
"client is Maya Chen", "wilson interior painting" and "7 Meadow Court" are
headers that a throwaway regex missed. `providers.HEADER_PATTERNS` already
handles "client is X" — reuse it instead of writing a second one.

That leaves 05 as the only judgement call. "crew going back once the replacement
bolts get here" and the parenthetical note after it are folded by the answer key
too, so folding a continuation line has to count as covered. Write that rule
down rather than tuning a number until 05 goes quiet.

The warning names the lines, not a count. "2 lines are not quoted by any item"
followed by the lines is actionable; a number is not. Advisory only — it does
not change the score, and it is the same shape as date grounding: judge the
input line, not the model's rewrite of it.

Tests: 06 and 10 fire, 01/02/07/08/09 stay quiet. No API calls needed.

**2. Re-run the batch once and confirm the score did not move.** The detector
only adds warnings. If 241/265 moves, something else changed and it needs
finding before the freeze, not after.

**3. action_required — read the two, expect to leave them alone.** "might be
able to swing by thursday pm" and "living room done except touch ups". Both
describe work that is not finished. Today's measurement says a prompt rule fixes
the items it names and shuffles others, so the likely right answer is to change
nothing and record why. Do not spend the evening here.

**4. Update PRESENTATION.md and the deck. Not optional.** If time runs short,
drop 3 and 5, not this. Presenting last week's numbers is the one mistake that
actually costs something. Stale, all confirmed:

| Location | Says | Should say |
|---|---|---|
| Field accuracy | 192/214 (90%) | 241/265 (91%) |
| Clean samples | 4/8 | 4/10 |
| Sample count | 8 | 10 |
| Date fields | 36/38 | 44/47 |
| Test count | 127 | 144 |
| Known errors | 22 misses, 15 from one | 3 segmentation, 9 field |

The talk gets better, not worse. "The number went down and that is the point"
now has a second act: the number went down, then we found the ruler was wrong,
and 06 was being charged fifteen times for one mistake. Fixing the measurement
was worth more than any prompt change tried all week.

**5. Optional: `python -m src.stability --runs 10`.** Only if there is API
budget left after 1 and 2.

### Freeze checklist for tomorrow

- [ ] `python -m pytest` green
- [ ] `python -m src.score` matches the number in the README and the deck
- [ ] `git status` clean, `main` pushed
- [ ] the app starts and organizes one sample end to end

### Off the repo

- **Rotate the Groq key.** Still outstanding. It is in `.env` and gitignored, so
  the repo is fine, but it has been pasted in chat.
- **Confirm the teacher's invite.** A pending invite to `salaidh814perez-alt`
  exists with write access. Neeti has read. Worth checking the account is the
  right one and that write is intended.
- **The de-duplication decision** needs @vjvidhaan, not a commit. Sample 10 is
  the whole argument.

## For the reviewer

- **Sample 10 and de-duplication.** The open question above. Read the key, read
  the output, and say which one should change.
- **`python -m src.stability --runs 10`.** Ten runs of 03 is thin evidence.
- **The aligner is optimistic by construction.** It finds the best monotonic
  pairing, so the score is the kindest reading of a given output. That is the
  right default for measuring the model, but worth knowing before quoting 91%.

## Reviewer follow-ups — resolved

- **06 strap / safety guardrail → fixed the guardrail, kept the key.** The key is
  right: the photo of the strap is documentation, and the action already lives on
  the injury line and the "cap the strap ends" follow-up. The guardrail was
  flipping the photo to `action_required` because `flag_safety` reads the model's
  *summary* (which paraphrases the injury), not the input. `src/guardrails.py` now
  leaves a `photo` item's `action_required` alone. This is the date lesson again —
  judge what the input said, not what the model rewrote. **Verified on a real
  run:** the injury item is `action_required: true`, the photo is `false`, and
  the photo still carries `safety_review` at urgent priority.
- **Samples 09 and 10 added, answer key first.** `09_no_dates` (no dated lines —
  nothing should get a date) and `10_repeated_event` (an inspection and a delivery
  each stated twice, plus a dated line above an undated duplicate so date-grounding
  is exercised). Expected files written before any run; the repeated event is
  expected to appear twice and categorize consistently (de-dup is still a
  non-goal).
- **Stability prints its denominator.** `src/stability.py` now states
  "N runs x M samples = K organizations" and warns when only one sample was used —
  so "ten runs of 03" reads as 10 data points, not a stable number.
- **Category misses (wrong vs arguable): NOT sorted yet.** That needs the live
  `python -m src.score` miss list, which requires a Python env + an API call; it
  was not run in this pass, so the split is left open rather than guessed.
