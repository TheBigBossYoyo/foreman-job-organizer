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

Test set: still 5 samples, expand to 8-10. The answers live in data/expected
now, so a new sample means writing its expected file at the same time.

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
samples scored 117, 118, 118. The number is 118 ± 1, which means a one-field
change is noise and should not be reported as an improvement. Worth re-checking
if the test set ever grows, since a bigger denominator should damp this.

## Next

Weakest field now: category, five of the seven remaining misses. Different in
kind from dates, because some of them are arguable rather than wrong — calling
"demo done, there is moisture behind it" an issue instead of a contractor
update is a defensible reading. Before tuning anything:

- Separate the genuinely wrong ones from the arguable ones by hand.
- Only the wrong ones are worth chasing. For the arguable ones the fix is to
  write the tie-break rule into the prompt and into data/expected together, so
  the answer key states which reading the project intends.

Also outstanding: action_required missed twice on items that plainly ask for
something. That is a smaller and clearer target than category.
