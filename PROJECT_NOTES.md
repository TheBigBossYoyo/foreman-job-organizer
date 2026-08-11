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
| Field accuracy | 192/214 (90%) | **240/265 (91%)** |
| Same eight samples | 192/214 | **201/214** |
| Clean samples | 4/8 | 4/10 |

The nine recovered fields are all on 06, which went 13/28 → 22/28. The other
seven samples came out identical field for field, and the original five scored
118/125 for the third run running. The model did not improve. The ruler was
wrong.

Error shape across the ten: **3 segmentation errors, 10 field errors.** That
sentence is the reason for the change — 25 misses reads like 25 problems, and it
is 13.

Every date on an item the model produced is correct (44/47 date fields; the
three losses are items that were never produced).

## The de-duplication question — open

`10_repeated_event` states an inspection twice and a delivery twice, in
different words. The answer key expects four items. The model returned two: it
recognised each restatement and folded it in. That is both segmentation errors
on that sample and most of the gap between 91% and higher.

The key is not obviously right. A foreman reading a timeline probably wants one
inspection, not the same one twice. But nothing asked for de-duplication, it is
not in the prompt, and the model is doing it silently — which means it is also
free to merge two events that only *sound* alike. That is exactly the 06 failure
wearing a friendlier face.

Not decided here. Deciding it means either rewriting the key and documenting
de-duplication as intended, or keeping the key and making the model stop. Both
need a second opinion, and a run of `10` where the two events are genuinely
different to see whether it over-merges.

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
2. **Re-scored and recorded.** 240/265. Done.
4. **Samples 09 and 10.** Added by @vjvidhaan, answer keys written first. Done —
   and 10 produced the de-duplication question above, which is the most
   interesting thing to come out of the week.

## Next

**3. Check item count in code.** Compare items produced against non-header lines
and warn when they disagree by more than one. A detector, not a fix — the merge
on 06 should announce itself in the app, not only in the scorer. Same approach
as date grounding. This is the one still worth doing before the freeze.

**5. action_required.** Three misses. Prompt problem or key problem — decide by
reading, then measure once. Do not re-run until the number looks better.

**7. Stability at 10 runs.** Three runs of eight is thin. Worth doing only if
someone has API budget spare.

**The de-duplication decision.** See above. Needs a person, not a commit.

Build freezes Wednesday.

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
