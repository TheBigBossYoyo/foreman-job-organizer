"""Turn an organized job into a calendar file, without inventing a single date.

The obvious version of this feature puts every item on a calendar. That cannot
be done honestly here: 33 of the 44 items across the sample set carry no date,
because their own line never gave one, and resolving "thursday pm" into a real
Thursday is exactly the invention src/dates.py exists to prevent.

iCalendar already has the right answer. A VEVENT happens on a day. A VTODO is
something to do, and its DUE property is optional. So:

    a grounded date        -> VEVENT on that day
    action, but no date    -> VTODO with no DUE
    neither                -> nothing, it is a record and not a task

On 03_tricky_bathroom that produces three to-dos and no events at all, which is
the correct answer and a more convincing demonstration of the date rule than
any number. On 08_dense_stream "electrician booked for 2026-08-06" produces a
real event.

Dates are written as VALUE=DATE, never as a datetime. We know the day the input
named. Nothing in any sample states a time, and writing 09:00 to make a calendar
look tidier would be the same mistake one field along.

No dependencies: iCalendar is text. RFC 5545, the parts that apply.
"""

from datetime import date as date_cls, datetime, timedelta, timezone

PRODID = "-//VTSP//Foreman Job Organizer//EN"

# RFC 5545 section 3.1: lines are folded at 75 octets, and a continuation line
# begins with one space, which counts towards the next 75.
LINE_LIMIT = 75


def escape_text(value):
    """Escape a TEXT value. Backslash first, or it re-escapes the others."""
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def fold(line):
    """Fold one content line to 75 octets, splitting on octets, not characters.

    Counting characters would overflow the limit on any accented name, and
    splitting mid-character would produce a file no parser can read.
    """
    raw = line.encode("utf-8")
    if len(raw) <= LINE_LIMIT:
        return line

    chunks = []
    start, limit = 0, LINE_LIMIT
    while start < len(raw):
        end = min(start + limit, len(raw))
        # Never cut inside a multi-byte character: continuation bytes are 10xxxxxx.
        while end < len(raw) and (raw[end] & 0xC0) == 0x80:
            end -= 1
        chunks.append(raw[start:end].decode("utf-8"))
        start = end
        # Continuation lines carry a leading space that counts towards the 75.
        limit = LINE_LIMIT - 1

    return "\r\n ".join(chunks)


def as_ics_date(value):
    """YYYY-MM-DD to YYYYMMDD, or None if it is not a date we can trust."""
    try:
        return date_cls.fromisoformat(value).strftime("%Y%m%d")
    except (TypeError, ValueError):
        return None


def uid_for(item, project):
    """Stable within a job and unique enough between them."""
    stem = f"{project or 'job'}-{item.item_id}".lower().replace(" ", "-")
    return f"{stem}@foreman-job-organizer.invalid"


def describe(item):
    """The body of an entry: what it is, then the line it came from."""
    parts = [item.summary]
    if item.action_required and item.action:
        parts.append(f"Action: {item.action}")
    if item.source_excerpt:
        parts.append(f'From the job stream: "{item.source_excerpt}"')
    if item.flags:
        parts.append("Flagged for review: " + ", ".join(item.flags))
    return "\n\n".join(part for part in parts if part)


def to_ics(result, now=None):
    """One iCalendar file for a whole job. Returns text with CRLF endings.

    `now` is injectable so a test can assert on the whole file rather than on
    everything except the timestamp.
    """
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    project = result.project_name or "Job"

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{escape_text(project)}",
    ]

    for item in result.items:
        day = as_ics_date(item.date)
        summary = escape_text(item.title)
        description = escape_text(describe(item))
        uid = uid_for(item, result.project_name)

        if day:
            # DTEND is exclusive for a whole-day event, so a one-day event ends
            # the following day. Without this some clients show nothing at all.
            end = (date_cls.fromisoformat(item.date) + timedelta(days=1)).strftime("%Y%m%d")
            lines += [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{stamp}",
                f"DTSTART;VALUE=DATE:{day}",
                f"DTEND;VALUE=DATE:{end}",
                f"SUMMARY:{summary}",
                f"DESCRIPTION:{description}",
                "END:VEVENT",
            ]
        elif item.action_required:
            # No DUE. The input never said when, and a to-do with an invented
            # deadline is worse than one without a deadline.
            lines += [
                "BEGIN:VTODO",
                f"UID:{uid}",
                f"DTSTAMP:{stamp}",
                f"SUMMARY:{summary}",
                f"DESCRIPTION:{description}",
                "END:VTODO",
            ]

    lines.append("END:VCALENDAR")
    return "\r\n".join(fold(line) for line in lines) + "\r\n"


def counts(result):
    """(events, todos, left out). What the download will and will not contain."""
    events = sum(1 for item in result.items if as_ics_date(item.date))
    todos = sum(
        1 for item in result.items
        if not as_ics_date(item.date) and item.action_required
    )
    return events, todos, len(result.items) - events - todos
