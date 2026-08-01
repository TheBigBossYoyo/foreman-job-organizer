import json
import os
from datetime import datetime
from pathlib import Path

import streamlit as st

from src.organizer import JobOrganizerError, organize_job_stream

SAMPLE_DIR = Path("data/samples")

st.set_page_config(page_title="Foreman AI Job Organizer", page_icon="🏗️", layout="wide")


def load_sample(name):
    return (SAMPLE_DIR / name).read_text(encoding="utf-8")

st.title("🏗️ Foreman AI Job Organizer")
st.caption("Paste the running record of a job and get back a timeline you can read.")

with st.sidebar:
    st.header("Settings")
    if os.getenv("GROQ_API_KEY"):
        st.success("Groq API connected")
    else:
        st.error("No GROQ_API_KEY found. Copy .env.example to .env and add your key.")

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

    # Dates were the weakest field in the Week 3 scoring, and a missing date or a
    # low confidence label is exactly where the model tends to have guessed. Put
    # those items in front of the reviewer instead of leaving them to be found.
    needs_review = {
        item["item_id"] for item in result["items"]
        if item["date"] is None or item["confidence"] == "low"
    }
    if needs_review:
        flagged_ids = ", ".join(sorted(needs_review))
        st.info(
            f"{len(needs_review)} of {len(result['items'])} items need a human "
            f"check ({flagged_ids}). They are missing a date or came back at low "
            f"confidence."
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
                st.caption(f"Source: \"{item['source_excerpt']}\"")

    with right:
        st.subheader("Job overview")
        st.write(f"**Project:** {result['project_name'] or 'Not found'}")
        st.write(f"**Client:** {result['client_name'] or 'Not found'}")
        st.write(f"**Address:** {result['property_address'] or 'Not found'}")
        st.write(result["overall_summary"])

        st.subheader("Open actions")
        if result["open_actions"]:
            # Keyed by position, because two open actions can read the same and
            # Streamlit raises on duplicate widget ids built from the label.
            for index, action in enumerate(result["open_actions"]):
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
