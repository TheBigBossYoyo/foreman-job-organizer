# Project decisions

## Chosen build
Option C — Job Organizer.

## Problem statement
Contractors receive job information through scattered messages, receipts, photo
captions, delivery notices, and handwritten-style updates. This tool turns that
messy stream into a structured timeline, highlights open actions, and preserves
supporting excerpts so a human can review the result quickly.

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
An item is considered correct when its category, extracted facts, action flag,
and source excerpt agree with the input without invented information.

## Missing-data rule
Return null and add a warning. Never guess.

## Week 4 plan
Interface: done early. app.py has the text box, the timeline, the open actions
and the JSON download, plus a sample picker and a flag on any item with a
missing date or low confidence.

Scoring: done. `python -m src.score` gives the field count and the miss list, so
the number can be rerun after every prompt change instead of recounted.

Test set: done, 5 to 8. Each new one probes something the first five never did —
06 injury language, 07 two currencies in one job, 08 a stream with no blank
lines. Answers written by hand before the model ran, same as the first five.

The number went from 118/125 (94%) to 192/214 (90%). That is the test set
working. The original five scored 118/125 again in the same run, so nothing
regressed; the drop is entirely 06 at 13/28, and 07 and 08 came back clean at
28/28 and 33/33 first time.

Dates: done. 22/22 correct. The code check in src/dates.py drops any date that
is not written on the item's own source line. Worth remembering that the first
version compared against source_excerpt and lowered the score to 112/125,
because the model's quote leaves the date prefix out. The excerpt is what the
model chose to write; the source line is what the input actually said, and only
the second one can settle whether a date was really there.

The wider lesson: two prompt rewrites did not move inheritance at all, and
twenty lines of code fixed it completely. Rules the model has to remember are
weaker than rules the pipeline enforces.

## The merge

Two prototypes lived in this repo for a day: this one and a teammate's Python
port of a PHP web app. Merged rather than chosen between.

Kept from here: the scorer and answer key, the source-line date check, the
Pydantic contract, the batch runner. Taken from there: the provider chain with
its no-key fallback, guardrails enforced in code, the aggregation layer.

Declined on purpose: their 13-category schema and their samples. Both are
defensible, and adopting either would have invalidated data/expected and made
the number incomparable with 112, 115 and 118. A richer schema is worth having;
it is not worth losing the only measurement chain the project has.

Their split-on-blank-lines chunker was the other thing left behind. It fused
five events into one item on a dense sample, and no test of theirs could catch
it because every one of their own samples has a blank line between entries.

## Reproducibility

Temperature 0 is not deterministic. Three consecutive runs of the same five
samples scored 117, 118, 118, so a one-field change is noise and should not be
reported as an improvement.

"118 ± 1" turns out to describe only the runs where the model splits the stream
the same way each time, and it does not always. One batch run split
03_tricky_bathroom into six items where ten other runs gave five, by cutting

    7/27 demo done. opened up the shower wall and there is moisture behind it

into two. The scorer lines items up by position, so one extra item shifted
every later field and changed the denominator as well: that run scored the
original five at 114/130 (88%) rather than 118/125 (94%). Nothing about the
model or the code was different.

So there are two kinds of variation and they are not the same size:

- field noise, about ±1, which is what 117/118/118 measured
- segmentation change, rare but worth several fields and a moved denominator

`python -m src.stability --runs N` measures both. Item counts held identical
across three runs of all eight samples, and six more of 03. Call it uncommon
rather than fixed.

## The 06 result

06_safety_incident scored 13/28, which looks catastrophic and is one mistake.
The model merged

    2026-08-03 - framing crew on site, north wall studs up
    Dave cut his forearm on a strap end, first aid kit used, he finished the day

into a single item titled "Framing progress and injury". Five expected items
then line up against four actual ones and almost everything after the merge is
scored against the wrong entry. One error, fifteen wrong fields.

Two things went right in the same sample and are worth keeping in view:

- the safety guardrail fired on the injury and on the photo of the strap, and
  raised both to urgent without being asked to in the prompt
- the model tried to put 2026-08-03 on three items that do not state it, and
  date grounding dropped all three, each with its own warning

So the guardrails did their job on a sample built to test them. What failed is
event segmentation, which is a different problem from any yet recorded here.

## Next

**1. Event segmentation.** New in Week 4 and now the biggest single source of
lost fields. One merge on 06 cost fifteen. Nothing in the pipeline currently
checks that the number of items bears any relation to the number of events in
the input, which is the same class of problem as the date inheritance that
Week 3 fixed in code rather than in the prompt. Same lesson probably applies.

**2. The scorer cannot tell a merge from fifteen mistakes.** Position matching
was the right call at five samples and is now hiding the shape of the errors.
A report that said "1 segmentation error, 3 field errors" would be worth more
than 13/28. This is a measurement problem, not a model problem, and it should
be fixed before anyone tunes a prompt against these numbers.

**3. Category**, five of the seven misses on the original five. Some are
arguable rather than wrong — calling "demo done, there is moisture behind it"
an issue instead of a contractor update is a defensible reading. Separate the
genuinely wrong from the arguable by hand; only the wrong ones are worth
chasing, and for the arguable ones the fix is to write the tie-break rule into
the prompt and into data/expected together.

**4. action_required**, missed twice on items that plainly ask for something.
Smaller and clearer than category.

## For the reviewer

Deliberately left open. These are judgement calls, and a second reader is
worth more on them than another pass from the person who wrote the answers.

- **Re-read the 06 answer key before anything is tuned against it.** One entry
  is genuinely arguable: the key says the photo of the strap is
  `action_required: false`, and the safety guardrail overrides it to true
  because the summary carries injury language. The guardrail may well be right.
  Whoever decides should change the key or the guardrail, and write down which
  and why — not quietly leave them disagreeing.
- **Sort the category misses into wrong and arguable.** The list is in
  `python -m src.score`. No code needed, just a second opinion recorded next to
  each one.
- **Samples 09 and 10**, to reach the 8-10 the plan asked for. Untested ground:
  a stream with no dates at all, and one where the same event is mentioned
  twice in different words. Write the answer key first, as always.
- **Run `python -m src.stability --runs 10`** on a machine that can spare the
  calls. Ten runs of 03 is thin evidence for how often segmentation moves.
