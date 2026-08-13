"""Turn a phone chat export into a job stream the organizer can read.

Every sample in data/samples was typed by us. The fair objection to the whole
project is that we also invented the shape of the input, so this reads the
format a contractor's job record actually arrives in: a WhatsApp export, which
is one tap on a phone and the thing most small crews genuinely run on.

The interesting decision is what to do with the timestamps, and the answer is
nothing.

An export carries a send time on every line, and it is tempting to use it: it
would fill in the dates that two thirds of our items are missing. It would also
be wrong. A message saying "building control came round last tuesday and signed
off the footings, forgot to say" was sent on the 5th and describes something
that happened on the 28th. The timestamp says when it was typed, not when it
happened, and the gap between those two is precisely the mistake src/dates.py
exists to catch.

So send times are reported to the person importing and never written into the
stream. If a foreman typed a date, the organizer will find it. If nobody typed
one, the item stays undated, exactly as if the text had been pasted by hand.

What is safe to fix is formatting. A message that wrapped onto a second line in
the export is one message split by the file format, not two events, so those
are rejoined. Two consecutive messages from the same person are left alone,
even when they are obviously one thought: deciding that two lines are really
one event is the merge that broke 08_dense_stream, and it is not this module's
job.
"""

import re

# WhatsApp on iOS writes an invisible left-to-right mark before the opening
# bracket, and again before an attachment marker. Nothing shows it, and it
# pushes the line out of the ^\[ anchor below: on a real 15-month export, 343
# of 956 messages failed to parse and were glued onto the message above as if
# they had wrapped. That is the merge this module exists to avoid, done
# silently, so the marks come off before anything else looks at the line.
BIDI = dict.fromkeys(map(ord, "‎‏‪‫‬⁦⁧⁨⁩"))

# The media placeholder is localised: "<Media omitted>" on an English phone,
# "<pièce jointe : IMG-0001.jpg>" on a French one, and the NOISE list below
# only ever knew the English wording. A filename on its own is not a job
# event, but an attachment can be sent with a caption, so the marker is
# removed and the message survives only if something was said alongside it.
ATTACHMENT = re.compile(
    r"<\s*(?:pièce jointe|fichier joint|archivo adjunto|allegato"
    r"|anhang|bijlage|attached|attachment)\s*:[^>]*>",
    re.I,
)


def strip_bidi(text):
    """Drop the direction marks WhatsApp writes around timestamps and media."""
    return (text or "").translate(BIDI)


# WhatsApp exports come in two shapes depending on platform and locale:
#   [03/08/2026, 07:14:22] Dan Reyes: message
#   03/08/2026, 07:14 - Dan Reyes: message
# A sender name is bounded to keep "10:30 - we agreed: no" from parsing as one.
BRACKETED = re.compile(
    r"^\[(?P<date>\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}),?\s+(?P<time>[\d:]{4,8}\s*(?:[APap]\.?[Mm]\.?)?)\]\s*"
    r"(?:(?P<sender>[^:]{1,40}):\s*)?(?P<text>.*)$"
)
DASHED = re.compile(
    r"^(?P<date>\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}),?\s+(?P<time>[\d:]{4,8}\s*(?:[APap]\.?[Mm]\.?)?)\s+-\s+"
    r"(?:(?P<sender>[^:]{1,40}):\s*)?(?P<text>.*)$"
)

# Content the export writes on the crew's behalf. None of it is a job event, and
# "<Media omitted>" in particular would become a photo item about nothing.
NOISE = [
    "messages and calls are end-to-end encrypted",
    "media omitted",
    "image omitted",
    "video omitted",
    "audio omitted",
    "sticker omitted",
    "document omitted",
    "this message was deleted",
    "you deleted this message",
    "missed voice call",
    "missed video call",
    "created group",
    "added you",
    "joined using this group's invite link",
    "changed the subject",
    "changed this group's icon",
]


def is_noise(text):
    """True for the lines the app wrote rather than a person."""
    stripped = text.strip().strip("<>").lower()
    if not stripped:
        return True
    return any(phrase in stripped for phrase in NOISE)


def parse_line(line):
    """(date, sender, text) for a message line, or None if it is not one."""
    line = strip_bidi(line)
    for pattern in (BRACKETED, DASHED):
        match = pattern.match(line)
        if match:
            return match.group("date"), (match.group("sender") or "").strip(), match.group("text")
    return None


def parse_export(raw_text):
    """Return (job_stream, stats) for a pasted or uploaded chat export.

    `stats` is what the importer wants to tell a human before they trust it:
    how many messages came through, who from, the window they were sent in, and
    how many lines were dropped as noise.
    """
    messages = []
    dates = []
    dropped = 0

    for line in (raw_text or "").splitlines():
        parsed = parse_line(line)

        if parsed is None:
            # No timestamp: this is the tail of a message that wrapped in the
            # export. Formatting, not a second event, so it rejoins the one above.
            #
            # The marker has to come off here too. A wrapped tail carrying
            # "<pièce jointe : 0728-PHOTO-2025-12-05-13-55-42.jpg>" glues the
            # filename into the message body, and that filename is the send
            # timestamp written out in full. Date grounding then finds
            # 2025-12-05 genuinely present on the item's source line and keeps
            # it. That is the send time this module throws away, coming back in
            # through the one door it wasn't watching.
            tail = ATTACHMENT.sub("", strip_bidi(line)).strip()
            if tail and messages:
                messages[-1]["text"] = f"{messages[-1]['text']} {tail}".strip()
            continue

        date, sender, text = parsed
        text = ATTACHMENT.sub("", text).strip()
        if not sender or is_noise(text):
            dropped += 1
            continue

        dates.append(date)
        messages.append({"sender": sender, "text": text.strip()})

    # Drop any message that was nothing but a media placeholder once its
    # continuation lines were joined on.
    kept = [m for m in messages if not is_noise(m["text"])]
    dropped += len(messages) - len(kept)

    stream = "\n".join(f"{m['sender']}: {m['text']}" for m in kept)
    stats = {
        "messages": len(kept),
        "dropped": dropped,
        "senders": sorted({m["sender"] for m in kept}),
        "first_sent": dates[0] if dates else None,
        "last_sent": dates[-1] if dates else None,
    }
    return stream, stats


def describe(stats):
    """One sentence for the person importing, including what was not used."""
    if not stats["messages"]:
        return "No messages found. Is this a chat export?"

    who = len(stats["senders"])
    sentence = (
        f"{stats['messages']} message{'' if stats['messages'] == 1 else 's'} "
        f"from {who} {'person' if who == 1 else 'people'}"
    )
    if stats["first_sent"] and stats["last_sent"]:
        if stats["first_sent"] == stats["last_sent"]:
            sentence += f", sent {stats['first_sent']}"
        else:
            sentence += f", sent between {stats['first_sent']} and {stats['last_sent']}"
    if stats["dropped"]:
        sentence += f". {stats['dropped']} line{'' if stats['dropped'] == 1 else 's'} dropped as app noise"
    return (
        sentence + ". Send times were not used as event dates: they say when a "
        "message was typed, not when the work happened."
    )
