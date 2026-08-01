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

Weakest field: dates, and now specifically inheritance. Inventing a year is
fixed. Copying the date off the line above is not, and adding another sentence
to the prompt did not move it at all, so the next attempt should not be another
sentence. Two options worth trying:

- Feed the model one line at a time so there is no line above to copy from.
- Check it in code after the fact: if the date does not appear inside that
  item's own source_excerpt, clear it and add a warning.

The second is cheaper and testable without an API call, so try it first.
