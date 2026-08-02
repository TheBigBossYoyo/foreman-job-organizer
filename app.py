import json
import os
from datetime import datetime
from html import escape
from pathlib import Path

import streamlit as st

from src.aggregate import summarize
from src.organizer import JobOrganizerError, organize_job_stream
from src.providers import resolve_chain
from src.schema import JobOrganizationResult

PROVIDER_LABELS = {
    "anthropic": "Anthropic Claude",
    "groq": "Groq",
    "local": "Local rule-based engine (no AI)",
}

# Short, readable names. "Contractor Update" title-cased from the enum reads as
# a database field; these read as something a foreman would say.
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

# One colour per category, carried by the card's left edge. Chosen to stay
# legible on both the light and dark Streamlit themes.
CATEGORY_COLORS = {
    "photo": "#9333EA",
    "receipt": "#EA580C",
    "client_update": "#2563EB",
    "contractor_update": "#F97316",
    "inspection": "#16A34A",
    "delivery": "#D97706",
    "schedule": "#0EA5E9",
    "issue": "#DC2626",
    "payment": "#059669",
    "other": "#64748B",
}

# Neutral greys at low alpha rather than fixed colours, so the cards sit
# correctly on a light or a dark background without a second stylesheet.
CARD_CSS = """
<style>
.jo-card {
  border: 1px solid rgba(128, 128, 128, 0.22);
  border-left: 4px solid var(--jo-accent, #64748B);
  border-radius: 8px;
  padding: 0.85rem 1rem;
  margin-bottom: 0.6rem;
  background: rgba(128, 128, 128, 0.06);
}
.jo-head {
  display: flex;
  align-items: baseline;
  gap: 0.6rem;
  flex-wrap: wrap;
  margin-bottom: 0.35rem;
}
.jo-date {
  font-variant-numeric: tabular-nums;
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  opacity: 0.75;
  min-width: 4.2rem;
}
.jo-cat {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.09em;
  text-transform: uppercase;
}
.jo-amount {
  margin-left: auto;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  font-size: 0.9rem;
}
.jo-badge {
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  background: rgba(220, 38, 38, 0.15);
  color: #DC2626;
}
.jo-title { font-weight: 600; line-height: 1.35; }
.jo-summary { opacity: 0.85; line-height: 1.5; margin-top: 0.15rem; }
.jo-action {
  margin-top: 0.5rem;
  padding: 0.4rem 0.6rem;
  border-radius: 6px;
  background: rgba(234, 88, 12, 0.12);
  font-size: 0.85rem;
}
.jo-source {
  margin-top: 0.5rem;
  padding-left: 0.6rem;
  border-left: 2px solid rgba(128, 128, 128, 0.3);
  font-size: 0.8rem;
  font-style: italic;
  opacity: 0.6;
  line-height: 1.4;
}
.jo-note { margin-top: 0.4rem; font-size: 0.78rem; opacity: 0.7; }
</style>
"""


def format_date(iso_date):
    """2026-07-21 becomes 21 Jul. Reads faster down a column than the ISO form."""
    if not iso_date:
        return "no date"
    try:
        return datetime.strptime(iso_date, "%Y-%m-%d").strftime("%d %b")
    except ValueError:
        return iso_date


def render_card(item):
    """One item as a self-contained card. Everything is escaped: the text here
    comes from a model reading arbitrary input, so it is never trusted as HTML.
    """
    colour = CATEGORY_COLORS.get(item["category"], CATEGORY_COLORS["other"])
    label = CATEGORY_LABELS.get(item["category"], item["category"])

    parts = [
        f'<div class="jo-card" style="--jo-accent: {colour}">',
        '<div class="jo-head">',
        f'<span class="jo-date">{escape(format_date(item["date"]))}</span>',
        f'<span class="jo-cat" style="color: {colour}">{escape(label)}</span>',
    ]

    if item["flags"]:
        flags = ", ".join(flag.replace("_", " ") for flag in item["flags"])
        parts.append(f'<span class="jo-badge">{escape(flags)}</span>')

    if item["amount"] is not None:
        amount = f'{item["amount"]:,.2f} {item["currency"] or ""}'.strip()
        parts.append(f'<span class="jo-amount">{escape(amount)}</span>')

    parts.append("</div>")
    parts.append(f'<div class="jo-title">{escape(item["title"])}</div>')
    parts.append(f'<div class="jo-summary">{escape(item["summary"])}</div>')

    if item["action_required"] and item["action"]:
        parts.append(f'<div class="jo-action"><b>Action</b> · {escape(item["action"])}</div>')

    if item["compliance_notes"]:
        parts.append(f'<div class="jo-note">{escape(item["compliance_notes"])}</div>')

    parts.append(f'<div class="jo-source">{escape(item["source_excerpt"])}</div>')
    parts.append("</div>")
    return "".join(parts)

SAMPLE_DIR = Path("data/samples")

st.set_page_config(page_title="Foreman AI Job Organizer", page_icon="🏗️", layout="wide")


def load_sample(name):
    return (SAMPLE_DIR / name).read_text(encoding="utf-8")

st.markdown(CARD_CSS, unsafe_allow_html=True)

st.title("🏗️ Foreman AI Job Organizer")
st.caption("Paste the running record of a job and get back a timeline you can read.")

with st.sidebar:
    st.header("Settings")
    # Show the whole chain, not just the winner. Knowing that Anthropic is
    # missing and Groq is carrying the run is the difference between a result
    # you trust and one you check.
    chain = resolve_chain()
    st.write("**Providers, in order:**")
    for position, provider in enumerate(chain, 1):
        label = PROVIDER_LABELS.get(provider, provider)
        if provider == "local":
            st.caption(f"{position}. {label} — always available")
        else:
            st.caption(f"{position}. {label}")
    if "anthropic" not in chain:
        st.info("No ANTHROPIC_API_KEY set, so Anthropic is skipped.")
    if chain == ["local"]:
        st.warning("No API keys at all. Output will be keyword-matched, not organized by a model.")

    st.markdown(
        """
**Privacy rule**

Made-up sample information only. Do not paste real Foreman customer or
company data.
"""
    )

    st.header("Samples")
    sample_names = sorted(path.name for path in SAMPLE_DIR.glob("*.txt"))
    if sample_names:
        chosen = st.selectbox("Test file", sample_names)
        if st.button("Load into the box"):
            st.session_state["raw_text"] = load_sample(chosen)
    else:
        st.caption(f"No .txt files found in {SAMPLE_DIR}.")

# Open on the first sample so the box is never empty, and so what you see is a
# real test file rather than a copy that drifts out of date.
if "raw_text" not in st.session_state:
    st.session_state["raw_text"] = load_sample(sample_names[0]) if sample_names else ""

# Once there is a result, the input is no longer the thing you came to look at.
# Collapse it so a 300px box does not push the timeline off the screen, but
# leave it one click away for the next run.
with st.expander("Job stream", expanded="result" not in st.session_state):
    raw_text = st.text_area(
        "Paste a messy job stream",
        height=300,
        key="raw_text",
        label_visibility="collapsed",
    )

if st.button("Organize job", type="primary", use_container_width=True):
    # Clear the last run before starting. Otherwise a failed call leaves the
    # previous timeline sitting under the error message, and ticked-off actions
    # carry over onto a completely different job.
    st.session_state.pop("result", None)
    for key in [key for key in st.session_state if key.startswith("action_")]:
        del st.session_state[key]

    try:
        with st.spinner("Organizing the job stream..."):
            result = organize_job_stream(raw_text)
        st.session_state["result"] = result.model_dump()
    except (ValueError, JobOrganizerError) as exc:
        st.error(str(exc))

if "result" in st.session_state:
    result = st.session_state["result"]

    # The guardrails already decided what needs a human. Reading their flags
    # rather than re-deriving the rule here means the app and the pipeline
    # cannot disagree about which items are questionable.
    needs_review = {item["item_id"] for item in result["items"] if item["flags"]}

    # A run on the no-model fallback changes how much everything below is worth,
    # so that one stays on top. Everything else goes under the timeline: the
    # point of the app is the timeline, and notices should not push it off the
    # screen before it has been read.
    if result.get("provider") == "local":
        st.error(
            "Organized without an AI model. Every field below was matched by "
            "keyword and needs checking."
        )

    left, right = st.columns([2, 1])

    with left:
        st.subheader("Organized timeline")

        # Chronological, with undated items last in the order they arrived. It
        # is a timeline, so it should read as one rather than follow whatever
        # order the model happened to emit.
        ordered = sorted(
            result["items"],
            key=lambda item: (item["date"] is None, item["date"] or ""),
        )

        # Rendered as one HTML block rather than per item. Streamlit wraps every
        # separate markdown call in its own padded container, which reintroduces
        # the gaps the cards exist to remove.
        st.markdown(
            "".join(render_card(item) for item in ordered),
            unsafe_allow_html=True,
        )

    with right:
        st.subheader("Job overview")
        # "Not stated" rather than "Not found". The field is blank because the
        # source never said, which is the missing-data rule working, not the
        # app failing to locate something that was there.
        for label, key in [
            ("Project", "project_name"),
            ("Client", "client_name"),
            ("Address", "property_address"),
        ]:
            value = result[key]
            if value:
                st.write(f"**{label}:** {value}")
            else:
                st.write(f"**{label}:** :grey[not stated in the source]")
        st.write(result["overall_summary"])

        summary = summarize(JobOrganizationResult.model_validate(result))

        st.subheader("Totals")
        c1, c2 = st.columns(2)
        c1.metric("Items", summary["item_count"])
        c2.metric("Need review", summary["needs_review"])
        if summary["spend"]:
            # One line per currency. A single combined total would be a number
            # that appears nowhere in the input.
            for currency, total in summary["spend"].items():
                st.write(f"**Spend ({currency}):** {total:,.2f}")
        if summary["date_range"]["start"]:
            st.caption(
                f"Dated {summary['date_range']['start']} to "
                f"{summary['date_range']['end']} · {summary['undated']} undated"
            )

        st.subheader("Open actions")
        if summary["open_actions"]:
            # Keyed by position, because two open actions can read the same and
            # Streamlit raises on duplicate widget ids built from the label.
            for index, action in enumerate(summary["open_actions"]):
                st.checkbox(action, key=f"action_{index}")
        else:
            st.success("No open actions detected.")

    # Notices live below the timeline, grouped rather than stacked. A column of
    # yellow banners above the result made a clean run look like a failure.
    warnings = result["warnings"]
    provider = result.get("provider")

    if needs_review or warnings:
        with st.expander(
            f"Review notes ({len(needs_review)} flagged, {len(warnings)} warnings)",
            expanded=False,
        ):
            if needs_review:
                st.write(
                    f"**{len(needs_review)} of {len(result['items'])} items flagged:** "
                    + ", ".join(sorted(needs_review))
                )
            else:
                st.write("**No items were flagged by the guardrails.**")

            for warning in warnings:
                st.caption(f"• {warning}")
    else:
        st.success("Nothing flagged and no warnings on this run.")

    if provider:
        st.caption(f"Organized by {PROVIDER_LABELS.get(provider, provider)}.")

    st.download_button(
        "Download JSON",
        data=json.dumps(result, indent=2, ensure_ascii=False),
        file_name="organized_job.json",
        mime="application/json",
        use_container_width=True,
    )

    if st.button("Save result locally"):
        # Save what is already on screen. Calling the organizer again here
        # would cost a second API call and could return something different.
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = Path("outputs") / f"streamlit_{timestamp}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        st.success(f"Saved to {path}")
