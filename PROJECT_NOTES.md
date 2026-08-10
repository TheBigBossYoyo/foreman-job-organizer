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

## The 06 result

13/28, from one mistake. The model merged these two lines into a single item
titled "Framing progress and injury":

    2026-08-03 - framing crew on site, north wall studs up
    Dave cut his forearm on a strap end, first aid kit used, he finished the day

Five expected items then line up against four actual ones. One error, fifteen
wrong fields.

Two things worked in the same sample:

- the safety guardrail fired on the injury and on the photo of the strap, and
  raised both to urgent — not asked for in the prompt
- the model put 2026-08-03 on three items that do not state it; date grounding
  dropped all three with warnings

## Next

**1. Event segmentation.** Biggest single source of lost fields. One merge on
06 cost fifteen. Nothing in the pipeline checks the item count against the
input. Same class of problem as date inheritance, which was fixed in code.

**2. The scorer cannot tell a merge from fifteen mistakes.** Position matching
was fine at five samples and now hides the shape of the errors. "1 segmentation
error, 3 field errors" is more useful than 13/28. Fix this before tuning any
prompt against these numbers.

**3. Category** — five of the seven misses on the original five. Some are
arguable, not wrong: "demo done, there is moisture behind it" as issue vs
contractor update. Separate wrong from arguable, chase only the wrong ones, and
write the tie-break rule into the prompt and `data/expected` together.

**4. action_required** — missed twice on items that plainly ask for something.

## Tomorrow

Ordered so each commit stands on its own and the risky one comes first.

**1. Make the scorer report error shape.** Detect when the model's item count
differs from the answer key and label it a segmentation error instead of
scoring every later field against the wrong entry. Output becomes
"1 segmentation error, 3 field errors" rather than 13/28.

Do this first. Every number after it changes, and tuning a prompt against the
current scorer would be tuning against a measurement that hides its own errors.

**2. Re-score and record the new numbers.** 192/214 will move once the scorer
stops cascading. Regenerate outputs, update README and this file together.

**3. Check item count in code.** Compare items produced against non-header
lines in the input and warn when they disagree by more than one. Not a fix for
segmentation — a detector, so the merge on 06 shows up as a warning rather than
as a low score. Same approach as date grounding.

**4. Samples 09 and 10.** A stream with no dates at all, and one where the same
event appears twice in different words. Answer key first, before running.

**5. action_required.** Two misses on items that plainly ask for something.
Look at both, decide whether it is a prompt problem or an answer key problem,
then measure. Do not tune and re-run until the number looks better.

**6. Category triage.** Split the five misses into wrong and arguable. For the
arguable ones write the tie-break rule into the prompt and `data/expected`
in the same commit.

**7. Stability at 10 runs.** Current evidence is thin. Update the numbers here
if segmentation moves more often than three-runs-of-eight suggested.

Build freezes Wednesday. Items 1-4 are the ones worth having; 5-7 are optional.

## For the reviewer

- **Re-read the 06 answer key before tuning against it.** The key says the photo
  of the strap is `action_required: false`; the safety guardrail overrides it to
  true. Change the key or the guardrail, and record which and why.
- **Sort the category misses into wrong and arguable.** List is in
  `python -m src.score`.
- **Samples 09 and 10.** Untested: a stream with no dates at all, and one where
  the same event appears twice in different words. Answer key first.
- **`python -m src.stability --runs 10`.** Ten runs of 03 is thin evidence.
