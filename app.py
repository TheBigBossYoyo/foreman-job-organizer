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

    provider = result.get("provider")
    if provider == "local":
        st.error(
            "Organized without an AI model. Every field below was matched by "
            "keyword and needs checking."
        )
    elif provider:
        st.caption(f"Organized by {PROVIDER_LABELS.get(provider, provider)}.")

    if needs_review:
        flagged_ids = ", ".join(sorted(needs_review))
        st.info(
            f"{len(needs_review)} of {len(result['items'])} items need a human "
            f"check ({flagged_ids})."
        )

    for warning in result["warnings"]:
        st.warning(warning)

    left, right = st.columns([2, 1])

    with left:
        st.subheader("Organized timeline")
        for item in result["items"]:
            header = (
                f"{'⚠ ' if item['item_id'] in needs_review else ''}"
                f"{item['item_id']} · {item['category'].replace('_', ' ').title()} · "
                f"{item['title']}"
            )
            with st.expander(header, expanded=True):
                st.write(item["summary"])
                c1, c2, c3 = st.columns(3)
                c1.metric("Date", item["date"] or "Not found")
                c2.metric("Priority", item["priority"].title())
                c3.metric("Confidence", item["confidence"].title())
                if item["amount"] is not None:
                    st.write(f"**Amount:** {item['amount']:.2f} {item['currency'] or ''}".strip())
                if item["action_required"]:
                    st.warning(f"Action: {item['action']}")
                if item["flags"]:
                    st.caption("Flagged: " + ", ".join(f.replace("_", " ") for f in item["flags"]))
                if item["compliance_notes"]:
                    st.caption(f"⚠ {item['compliance_notes']}")
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
