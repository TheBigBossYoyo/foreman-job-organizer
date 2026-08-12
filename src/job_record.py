"""One job, as a document a contractor could actually hand to somebody.

Slide two of the talk says the details that decide billing and disputes live in
someone's phone. Nothing else this tool produces solves that. JSON is for
another program and the screen is for the person who ran it; neither survives
being attached to an email six months later, when the argument is about who
said what and when.

So: one self-contained HTML page per job. Timeline, every source quote, the
open actions, and — the part that matters — the warnings, printed rather than
tucked behind an expander. A record that hides its own caveats is worth less
than no record, because it invites more trust than it has earned.

Three things travel with it that a screenshot would lose: the date it was
generated, which engine produced it, and the note that every entry quotes the
line it came from. A document that cannot be checked is just an assertion in a
nicer font.

Deliberately paper: white ground, dark ink, print rules, whatever the reader's
theme. This is meant to be printed or saved as a PDF, and a dark-mode invoice
is not a thing. Everything is inlined, so the file works with no network.
"""

from datetime import date as date_cls, datetime
from html import escape

CATEGORY_LABELS = {
    "photo": "Photo",
    "receipt": "Receipt",
    "client_update": "Client update",
    "contractor_update": "Site work",
    "inspection": "Inspection",
    "delivery": "Delivery",
    "schedule": "Schedule",
    "issue": "Issue",
    "payment": "Payment",
    "other": "Other",
}

PROVIDER_LABELS = {
    "anthropic": "Anthropic Claude",
    "groq": "Groq",
    "local": "the local rule-based engine",
}

STYLE = """
@page { margin: 18mm 16mm; }
* { box-sizing: border-box; }
body {
  margin: 0; padding: 2.5rem 1.5rem 4rem;
  background: #FFFFFF; color: #16202B;
  font: 15px/1.6 Georgia, "Iowan Old Style", "Times New Roman", serif;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.sheet { max-width: 46rem; margin: 0 auto; }
.mono {
  font-family: ui-monospace, "SF Mono", SFMono-Regular, Menlo, Consolas, monospace;
}

header { border-bottom: 2px solid #16202B; padding-bottom: 1rem; margin-bottom: .5rem; }
.kicker {
  font-family: ui-monospace, Menlo, Consolas, monospace;
  font-size: .66rem; letter-spacing: .16em; text-transform: uppercase;
  color: #7C8894; margin: 0 0 .5rem;
}
h1 { font-size: 1.9rem; line-height: 1.15; margin: 0 0 .35rem; letter-spacing: -.01em; }
.sub { color: #4A5765; margin: 0; }
.meta {
  display: flex; flex-wrap: wrap; gap: .3rem 1.4rem;
  font-family: ui-monospace, Menlo, Consolas, monospace;
  font-size: .68rem; letter-spacing: .06em; text-transform: uppercase;
  color: #7C8894; margin: 1rem 0 2.2rem;
}

h2 {
  font-family: ui-monospace, Menlo, Consolas, monospace;
  font-size: .68rem; font-weight: 700; letter-spacing: .16em; text-transform: uppercase;
  color: #7C8894; margin: 2.4rem 0 .9rem;
  border-bottom: 1px solid #DDE2E6; padding-bottom: .4rem;
}

.entry { padding: .85rem 0; border-bottom: 1px solid #EDEFF1; page-break-inside: avoid; }
.entry:last-child { border-bottom: none; }
.entry-top {
  display: flex; flex-wrap: wrap; align-items: baseline; gap: .6rem; margin-bottom: .25rem;
}
.when {
  font-family: ui-monospace, Menlo, Consolas, monospace;
  font-size: .72rem; font-weight: 700; color: #16202B;
  min-width: 6.5rem;
}
.when.none { color: #9AA5B1; font-weight: 400; }
.cat {
  font-family: ui-monospace, Menlo, Consolas, monospace;
  font-size: .62rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase;
  color: #4A5765;
}
.amt { margin-left: auto; font-weight: 700; }
.flag {
  font-family: ui-monospace, Menlo, Consolas, monospace;
  font-size: .58rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase;
  color: #92400E; border: 1px solid #E7D3AE; background: #FCF6E9; padding: .05rem .35rem;
}
.title { font-weight: 700; }
.summary { color: #34414F; margin: .15rem 0 0; }
.action { color: #8A3A12; margin: .4rem 0 0; }
.quote {
  margin: .5rem 0 0; padding-left: .8rem; border-left: 2px solid #DDE2E6;
  font-family: ui-monospace, Menlo, Consolas, monospace;
  font-size: .74rem; color: #6B7885; line-height: 1.5;
  overflow-wrap: anywhere;
}

ul { margin: 0; padding: 0; list-style: none; }
li { padding: .35rem 0 .35rem 1.4rem; position: relative; color: #34414F; }
li::before {
  content: ""; position: absolute; left: .15rem; top: .95rem;
  width: .35rem; height: .35rem; background: #9AA5B1;
}
li.box::before {
  content: ""; top: .78rem; left: 0;
  width: .72rem; height: .72rem; background: #FFF; border: 1.5px solid #7C8894;
}

.note {
  margin-top: 2.6rem; padding-top: 1rem; border-top: 1px solid #DDE2E6;
  font-size: .8rem; color: #6B7885; line-height: 1.6;
}
.note strong { color: #34414F; }

@media print {
  body { padding: 0; }
  .entry { border-bottom: 1px solid #E6E9EB; }
}
"""


def format_date(value):
    """2026-08-05 to '5 Aug 2026'. Anything unparseable comes back as it is.

    Built without %-d, which is a glibc extension and raises on Windows.
    """
    if not value:
        return ""
    try:
        parsed = date_cls.fromisoformat(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{parsed.day} {parsed.strftime('%b %Y')}"


def money(item):
    if item.amount is None:
        return ""
    return f"{item.amount:,.2f} {item.currency or ''}".strip()


def render_entry(item):
    when = format_date(item.date)
    parts = [
        '<div class="entry">',
        '<div class="entry-top">',
        f'<span class="when{"" if when else " none"}">{escape(when) if when else "no date given"}</span>',
        f'<span class="cat">{escape(CATEGORY_LABELS.get(item.category, item.category))}</span>',
    ]

    for flag in item.flags:
        parts.append(f'<span class="flag">{escape(flag.replace("_", " "))}</span>')

    amount = money(item)
    if amount:
        parts.append(f'<span class="amt">{escape(amount)}</span>')

    parts.append("</div>")
    parts.append(f'<div class="title">{escape(item.title)}</div>')
    if item.summary:
        parts.append(f'<p class="summary">{escape(item.summary)}</p>')
    if item.action_required and item.action:
        parts.append(f'<p class="action">Outstanding: {escape(item.action)}</p>')
    if item.compliance_notes:
        parts.append(f'<p class="action">{escape(item.compliance_notes)}</p>')
    if item.source_excerpt:
        parts.append(f'<p class="quote">{escape(item.source_excerpt)}</p>')

    parts.append("</div>")
    return "".join(parts)


def to_html(result, summary=None, generated=None):
    """A whole job as one printable page.

    `summary` is the dict from aggregate.summarize when the caller has one; the
    open actions are taken from it because it has already collapsed duplicates
    and added the ones derived from the guardrails. Without it the model's own
    list is used.

    `generated` is injectable so a test can assert on the whole document.
    """
    stamp = (generated or datetime.now()).strftime("%d %B %Y")
    provider = PROVIDER_LABELS.get(result.provider, result.provider or "an unknown engine")
    actions = (summary or {}).get("open_actions") or result.open_actions

    identity = " · ".join(
        escape(value) for value in (result.client_name, result.property_address) if value
    )

    body = [
        '<div class="sheet">',
        "<header>",
        '<p class="kicker">Job record</p>',
        f"<h1>{escape(result.project_name or 'Untitled job')}</h1>",
        f'<p class="sub">{identity}</p>' if identity else '<p class="sub">No client or address was given in the source.</p>',
        "</header>",
        '<div class="meta">',
        f"<span>Generated {escape(stamp)}</span>",
        f"<span>Organized by {escape(provider)}</span>",
        f"<span>{len(result.items)} entries</span>",
        "</div>",
    ]

    if result.overall_summary:
        body.append(f'<p class="summary">{escape(result.overall_summary)}</p>')

    body.append("<h2>Timeline</h2>")
    body.extend(render_entry(item) for item in result.items)

    if actions:
        body.append("<h2>Outstanding</h2><ul>")
        body.extend(f'<li class="box">{escape(action)}</li>' for action in actions)
        body.append("</ul>")

    # Printed, not hidden. A record that buries what the tool was unsure about
    # invites more trust than it has earned.
    if result.warnings:
        body.append("<h2>What the organizer flagged</h2><ul>")
        body.extend(f"<li>{escape(warning)}</li>" for warning in result.warnings)
        body.append("</ul>")

    body.append(
        '<p class="note"><strong>How to read this.</strong> This record was '
        "assembled automatically from a text job stream. Every entry quotes the "
        "line it came from, so any of it can be checked against the original. "
        "An entry marked <em>no date given</em> is not undated by accident: no "
        "date was written on that line, and one was not inferred from the lines "
        "around it. Amounts and dates are copied, never calculated or guessed. "
        "This is a prototype and the entries above have not been reviewed by a "
        "person.</p>"
    )
    body.append("</div>")

    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f"<title>Job record — {escape(result.project_name or 'Untitled job')}</title>\n"
        f"<style>{STYLE}</style>\n</head>\n<body>\n"
        + "".join(body)
        + "\n</body>\n</html>\n"
    )
