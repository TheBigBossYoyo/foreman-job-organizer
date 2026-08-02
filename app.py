import json
import os
from datetime import datetime
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
    "photo": "📷 Photo",
    "receipt": "🧾 Receipt",
    "client_update": "💬 Client",
    "contractor_update": "🏗️ Site work",
    "inspection": "✅ Inspection",
    "delivery": "🚚 Delivery",
    "schedule": "📅 Schedule",
    "issue": "⚠️ Issue",
    "payment": "💵 Payment",
    "other": "📦 Other",
}

SAMPLE_DIR = Path("data/samples")

st.set_page_config(page_title="Foreman AI Job Organizer", page_icon="🏗️", layout="wide")


def load_sample(name):
    return (SAMPLE_DIR / name).read_text(encoding="utf-8")

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

raw_text = st.text_area("Paste a messy job stream", height=300, key="raw_text")

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

        for item in ordered:
            marker = "⚠ " if item["item_id"] in needs_review else ""
            date_label = item["date"] or "no date"
            header = (
                f"{marker}{date_label} · "
                f"{CATEGORY_LABELS.get(item['category'], item['category'])} · "
                f"{item['title']}"
            )

            with st.expander(header, expanded=True):
                st.write(item["summary"])

                # One line of facts instead of three metric tiles. Fifteen large
                # numbers on screen at once buried the text they described.
                facts = [f"Confidence: {item['confidence']}"]
                if item["amount"] is not None:
                    facts.insert(0, f"**{item['amount']:,.2f} {item['currency'] or ''}**".strip())
                if item["priority"] in ("high", "urgent"):
                    facts.append(f"Priority: {item['priority']}")
                if item["people"]:
                    facts.append(", ".join(item["people"]))
                st.caption(" · ".join(facts))

                if item["action_required"] and item["action"]:
                    st.warning(f"**Action:** {item['action']}")
                if item["flags"]:
                    st.caption(
                        "⚠ Flagged: "
                        + ", ".join(flag.replace("_", " ") for flag in item["flags"])
                    )
                if item["compliance_notes"]:
                    st.caption(item["compliance_notes"])
                st.caption(f"Source: \"{item['source_excerpt']}\"")

    with right:
        st.subheader("Job overview")
        st.write(f"**Project:** {result['project_name'] or 'Not found'}")
        st.write(f"**Client:** {result['client_name'] or 'Not found'}")
        st.write(f"**Address:** {result['property_address'] or 'Not found'}")
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
