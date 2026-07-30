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
Interface: text box for the pasted stream, timeline and open actions on screen,
JSON download.

Test set: expand from 5 to 8-10 samples and hand-write the correct output for
each before measuring anything.

Scoring: compare field by field, report a percentage rather than an impression.

Weakest field to keep improving: [fill in after the first real scored run].
