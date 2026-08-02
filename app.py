import json
from datetime import datetime
from html import escape
from pathlib import Path

import streamlit as st

from src.aggregate import summarize
from src.organizer import JobOrganizerError, organize_job_stream
from src.providers import provider_status, resolve_chain
from src.schema import JobOrganizationResult
from src.text import normalize

SAMPLE_DIR = Path("data/samples")

st.set_page_config(page_title="Job Organizer", page_icon="🏗️", layout="centered")

PROVIDER_LABELS = {
    "anthropic": "Anthropic Claude",
    "groq": "Groq",
    "local": "Local engine",
}

# Green only for the one actually answering. A configured-but-idle backup and an
# unconfigured provider are different facts and should not share a colour.
STATE_COLORS = {
    "active": "#16A34A",
    "standby": "#CBD5E1",
    "no key": "#FCA5A5",
    "off": "#E2E8F0",
}

CATEGORY_LABELS = {
    "photo": "Photo",
    "receipt": "Receipt",
    "client_update": "Client",
    "contractor_update": "Site work",
    "inspection": "Inspection",
    "delivery": "Delivery",
    "schedule": "Schedule",
    "issue": "Issue",
    "payment": "Payment",
    "other": "Other",
}

# One colour per category, carried only by the timeline dot. Colour is the
# cheapest way to let someone find the receipts in a long list, and the dot is
# enough of it — tinting whole rows turns a record into a highlighter drawing.
CATEGORY_COLORS = {
    "photo": "#8B5CF6",
    "receipt": "#EA580C",
    "client_update": "#2563EB",
    "contractor_update": "#0F766E",
    "inspection": "#16A34A",
    "delivery": "#D97706",
    "schedule": "#0EA5E9",
    "issue": "#DC2626",
    "payment": "#059669",
    "other": "#94A3B8",
}

CSS = """
<style>
.block-container { padding-top: 3rem; padding-bottom: 4rem; max-width: 820px; }
#MainMenu, footer, header { visibility: hidden; }

/* ---- top line ---- */
.jo-top {
  display: flex; align-items: baseline; gap: .55rem;
  padding-bottom: .9rem; margin-bottom: 1.6rem;
  border-bottom: 1px solid #ECEEF1;
}
.jo-name { font-size: 1.08rem; font-weight: 700; color: #0F172A; letter-spacing: -.015em; }
.jo-engine { margin-left: auto; font-size: .74rem; color: #94A3B8; font-weight: 500; }

/* ---- job identity ---- */
.jo-job { margin-bottom: 1.4rem; }
.jo-job-name {
  font-size: 1.55rem; font-weight: 700; color: #0F172A;
  letter-spacing: -.02em; line-height: 1.2;
}
.jo-job-meta { font-size: .87rem; color: #64748B; margin-top: .3rem; }
.jo-muted { color: #CBD5E1; }

/* ---- numbers ---- */
.jo-nums {
  display: flex; gap: 2.6rem; flex-wrap: wrap;
  padding: 1rem 0 1.15rem; margin-bottom: 1.9rem;
  border-top: 1px solid #ECEEF1; border-bottom: 1px solid #ECEEF1;
}
.jo-num-v {
  font-size: 1.4rem; font-weight: 700; color: #0F172A;
  font-variant-numeric: tabular-nums; line-height: 1.1;
}
.jo-num-v.warn { color: #DC2626; }
.jo-num-l {
  font-size: .68rem; font-weight: 600; letter-spacing: .07em;
  text-transform: uppercase; color: #94A3B8; margin-top: .28rem;
}

/* ---- timeline ---- */
.jo-row {
  display: grid; grid-template-columns: 4.3rem .9rem 1fr;
  column-gap: .85rem; padding: .35rem .5rem 1.15rem .5rem;
  margin-left: -.5rem; border-radius: 8px;
  transition: background .12s ease;
}
.jo-row:hover { background: #FAFBFC; }
.jo-when {
  text-align: right; font-size: .78rem; font-weight: 700; color: #334155;
  font-variant-numeric: tabular-nums; white-space: nowrap; padding-top: .1rem;
}
/* Undated is a real state, not a rendering gap, so it says so in words. */
.jo-when.none {
  color: #CBD5E1; font-weight: 600; font-size: .66rem;
  letter-spacing: .04em; text-transform: uppercase;
}
.jo-rail { position: relative; }
.jo-dot {
  position: absolute; top: .35rem; left: .12rem;
  width: .58rem; height: .58rem; border-radius: 50%;
  box-shadow: 0 0 0 3px #fff; z-index: 1;
}
.jo-rail::after {
  content: ""; position: absolute; left: .385rem; top: .6rem; bottom: -1.5rem;
  width: 1.5px; background: #E2E8F0;
}
.jo-row:last-child .jo-rail::after { display: none; }

.jo-head { display: flex; align-items: baseline; gap: .5rem; margin-bottom: .2rem; }
.jo-cat {
  font-size: .66rem; font-weight: 700; letter-spacing: .09em; text-transform: uppercase;
}
/* Sits next to the category, not pushed to the far edge. Right-aligning it
   across a 700px column left it stranded a long way from the item it belongs
   to, reading as a stray number rather than that item's cost. */
.jo-amt {
  font-size: .87rem; font-weight: 700; color: #0F172A;
  font-variant-numeric: tabular-nums; white-space: nowrap;
}
.jo-flag {
  font-size: .62rem; font-weight: 700; letter-spacing: .05em; text-transform: uppercase;
  color: #B91C1C; background: #FEF2F2; border: 1px solid #FECACA;
  padding: .05rem .38rem; border-radius: 4px;
}
.jo-title { font-weight: 600; color: #0F172A; line-height: 1.4; font-size: .97rem; }
.jo-sum { color: #475569; font-size: .9rem; line-height: 1.55; margin-top: .15rem; }
.jo-act {
  margin-top: .5rem; font-size: .85rem; color: #9A3412;
  background: #FFFBF5; border: 1px solid #FDE7CE; border-radius: 6px;
  padding: .4rem .6rem; line-height: 1.45;
}
.jo-note { margin-top: .4rem; font-size: .8rem; color: #B45309; line-height: 1.45; }
.jo-src {
  margin-top: .45rem; padding-left: .65rem; border-left: 2px solid #ECEEF1;
  font-size: .79rem; color: #94A3B8; line-height: 1.45;
}
.jo-h {
  font-size: .7rem; font-weight: 700; letter-spacing: .09em; text-transform: uppercase;
  color: #94A3B8; margin: 2.2rem 0 .9rem;
}

/* ---- sidebar ---- */
[data-testid="stSidebar"] { background: #FAFBFC; border-right: 1px solid #ECEEF1; }
[data-testid="stSidebar"] .block-container { padding-top: 2.4rem; }
.jo-side-mark { font-size: 1.05rem; font-weight: 700; color: #0F172A; letter-spacing: -.01em; }
.jo-side-sub { font-size: .74rem; color: #94A3B8; margin-top: .1rem; margin-bottom: 1.4rem; }
.jo-side-h {
  font-size: .64rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase;
  color: #94A3B8; margin: 1.5rem 0 .5rem;
}
.jo-prov { display: flex; align-items: center; gap: .5rem; padding: .28rem 0; }
.jo-prov-dot { width: .5rem; height: .5rem; border-radius: 50%; flex: 0 0 auto; }
.jo-prov-name { font-size: .84rem; color: #334155; }
.jo-prov-name.dim { color: #94A3B8; }
.jo-prov-state {
  margin-left: auto; font-size: .66rem; font-weight: 600; letter-spacing: .04em;
  text-transform: uppercase; color: #94A3B8;
}
.jo-privacy {
  font-size: .72rem; color: #94A3B8; line-height: 1.5;
  border-top: 1px solid #ECEEF1; padding-top: .9rem; margin-top: 1.6rem;
}
</style>
"""


def load_sample(name):
    return (SAMPLE_DIR / name).read_text(encoding="utf-8")


def format_date(iso_date):
    """2026-07-21 becomes 21 Jul, which scans far better down a narrow column."""
    if not iso_date:
        return None
    try:
        return datetime.strptime(iso_date, "%Y-%m-%d").strftime("%d %b")
    except ValueError:
        return iso_date


def is_restatement(summary, excerpt):
    """True when the summary just says the source line again.

    On a plainly written line the model's summary is the line with a word
    changed, so showing both prints the same sentence twice under a title that
    is a third version of it. When that happens only the quote is kept: it is
    the evidence, and it is what the input actually said.
    """
    left, right = normalize(summary), normalize(excerpt)
    if not left or not right:
        return False
    if left in right or right in left:
        return True

    left_words, right_words = set(left.split()), set(right.split())
    shared = len(left_words & right_words)
    return shared / max(len(left_words), len(right_words)) >= 0.7


def render_numbers(summary):
    """Only figures taken from the run on screen.

    No job count and no running totals: the app organizes one stream and stores
    nothing, so any such number would have to be invented.
    """
    cells = [(str(summary["item_count"]), "items", False)]

    for currency, total in list(summary["spend"].items())[:2]:
        cells.append((f"{total:,.2f}", currency.lower(), False))

    if summary["undated"]:
        # Reads as a count of items, not as a statement about the job. "No date
        # given" was ambiguous enough that the first person to see it asked what
        # it meant.
        cells.append((
            f"{summary['undated']} of {summary['item_count']}",
            "items undated in the source",
            False,
        ))
    if summary["needs_review"]:
        cells.append((str(summary["needs_review"]), "need review", True))

    blocks = "".join(
        f'<div><div class="jo-num-v{" warn" if warn else ""}">{escape(value)}</div>'
        f'<div class="jo-num-l">{escape(label)}</div></div>'
        for value, label, warn in cells
    )
    st.markdown(f'<div class="jo-nums">{blocks}</div>', unsafe_allow_html=True)


def render_job_head(result):
    """Project, client and address. Absent fields are shown as absent, not hidden.

    A blank here is the missing-data rule working, and hiding it would look
    identical to the app never having tried.
    """
    name = result["project_name"] or "Untitled job"
    meta = [result["client_name"], result["property_address"]]
    shown = " · ".join(escape(part) for part in meta if part)
    if not shown:
        shown = '<span class="jo-muted">no client or address stated in the source</span>'

    st.markdown(
        f'<div class="jo-job"><div class="jo-job-name">{escape(name)}</div>'
        f'<div class="jo-job-meta">{shown}</div></div>',
        unsafe_allow_html=True,
    )


def render_row(item):
    """One timeline entry. Every value is escaped — this text came from a model
    reading arbitrary input, so it is never treated as markup.
    """
    colour = CATEGORY_COLORS.get(item["category"], CATEGORY_COLORS["other"])
    when = format_date(item["date"])

    parts = [
        '<div class="jo-row">',
        f'<div class="jo-when{"" if when else " none"}">'
        f'{escape(when) if when else "no date"}</div>',
        f'<div class="jo-rail"><span class="jo-dot" style="background:{colour}"></span></div>',
        '<div>',
        '<div class="jo-head">',
        f'<span class="jo-cat" style="color:{colour}">'
        f'{escape(CATEGORY_LABELS.get(item["category"], item["category"]))}</span>',
    ]

    if item["flags"]:
        flags = ", ".join(flag.replace("_", " ") for flag in item["flags"])
        parts.append(f'<span class="jo-flag">{escape(flags)}</span>')
    if item["amount"] is not None:
        amount = f'{item["amount"]:,.2f} {item["currency"] or ""}'.strip()
        parts.append(f'<span class="jo-amt">{escape(amount)}</span>')

    parts.append("</div>")
    parts.append(f'<div class="jo-title">{escape(item["title"])}</div>')

    if not is_restatement(item["summary"], item["source_excerpt"]):
        parts.append(f'<div class="jo-sum">{escape(item["summary"])}</div>')

    if item["action_required"] and item["action"]:
        parts.append(f'<div class="jo-act">{escape(item["action"])}</div>')
    if item["compliance_notes"]:
        parts.append(f'<div class="jo-note">{escape(item["compliance_notes"])}</div>')

    parts.append(f'<div class="jo-src">{escape(item["source_excerpt"])}</div>')
    parts.append("</div></div>")
    return "".join(parts)


st.markdown(CSS, unsafe_allow_html=True)

chain = resolve_chain()
st.markdown(
    f'<div class="jo-top"><span class="jo-name">Organize a job stream</span>'
    f'<span class="jo-engine">via {escape(PROVIDER_LABELS.get(chain[0], chain[0]))}</span></div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        '<div class="jo-side-mark">🏗️ Job Organizer</div>'
        '<div class="jo-side-sub">Foreman · VTSP technical track</div>',
        unsafe_allow_html=True,
    )

    sample_names = sorted(path.name for path in SAMPLE_DIR.glob("*.txt"))
    if sample_names:
        st.markdown('<div class="jo-side-h">Sample</div>', unsafe_allow_html=True)
        chosen = st.selectbox("Sample", sample_names, label_visibility="collapsed")
        if st.button("Load", use_container_width=True):
            st.session_state["raw_text"] = load_sample(chosen)

    # All three, always, with the reason each is or is not answering. A provider
    # that is simply missing from the list cannot be told apart from one this
    # app never supported.
    st.markdown('<div class="jo-side-h">Providers</div>', unsafe_allow_html=True)
    rows = "".join(
        f'<div class="jo-prov">'
        f'<span class="jo-prov-dot" style="background:{STATE_COLORS[state]}"></span>'
        f'<span class="jo-prov-name{"" if state == "active" else " dim"}">'
        f'{escape(PROVIDER_LABELS[name])}</span>'
        f'<span class="jo-prov-state">{escape(state)}</span></div>'
        for name, state in provider_status()
    )
    st.markdown(rows, unsafe_allow_html=True)

    if chain == ["local"]:
        st.warning("No API key. Output is keyword-matched, not organized by a model.")

    st.markdown(
        '<div class="jo-privacy">Made-up sample data only. Never paste real '
        'customer or company data.</div>',
        unsafe_allow_html=True,
    )

if "raw_text" not in st.session_state:
    st.session_state["raw_text"] = load_sample(sample_names[0]) if sample_names else ""

# Once there is a result the input is not what you came to look at, so it
# collapses. It stays one click away for the next run.
with st.expander("Job stream", expanded="result" not in st.session_state):
    raw_text = st.text_area(
        "stream", height=260, key="raw_text", label_visibility="collapsed"
    )

if st.button("Organize", type="primary"):
    # Clear the last run first. Otherwise a failure leaves the previous timeline
    # under the error, and ticked actions carry onto a different job.
    st.session_state.pop("result", None)
    for key in [key for key in st.session_state if key.startswith("action_")]:
        del st.session_state[key]

    try:
        with st.spinner("Organizing..."):
            st.session_state["result"] = organize_job_stream(raw_text).model_dump()
        # The input expander was already drawn open earlier in this same run, so
        # without a rerun it stays open and pushes the result down the page.
        st.rerun()
    except (ValueError, JobOrganizerError) as exc:
        st.error(str(exc))

if "result" in st.session_state:
    result = st.session_state["result"]
    summary = summarize(JobOrganizationResult.model_validate(result))

    if result.get("provider") == "local":
        st.error("No model was reached. Every field below was matched by keyword.")

    render_job_head(result)
    render_numbers(summary)

    # Chronological, undated last in arrival order. It is a timeline, so it
    # should read as one rather than follow the order the model emitted.
    ordered = sorted(
        result["items"], key=lambda item: (item["date"] is None, item["date"] or "")
    )
    # One markdown call for the whole list: Streamlit pads every separate call
    # with its own container, which breaks the rail into disconnected pieces.
    st.markdown("".join(render_row(item) for item in ordered), unsafe_allow_html=True)

    if summary["open_actions"]:
        st.markdown('<div class="jo-h">Open actions</div>', unsafe_allow_html=True)
        # Keyed by position: two actions can read the same, and Streamlit raises
        # on duplicate widget ids built from the label.
        for index, action in enumerate(summary["open_actions"]):
            st.checkbox(action, key=f"action_{index}")

    if result["warnings"]:
        with st.expander(f"Warnings ({len(result['warnings'])})"):
            for warning in result["warnings"]:
                st.caption(warning)

    left, right = st.columns(2)
    left.download_button(
        "Download JSON",
        data=json.dumps(result, indent=2, ensure_ascii=False),
        file_name="organized_job.json",
        mime="application/json",
        use_container_width=True,
    )
    if right.button("Save to outputs", use_container_width=True):
        # Saves what is on screen. Re-running the organizer here would cost
        # another call and could return something different.
        path = Path("outputs") / f"streamlit_{datetime.now():%Y%m%d_%H%M%S}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        st.success(f"Saved to {path}")
