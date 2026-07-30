import json
import os
from datetime import datetime
from pathlib import Path

import streamlit as st

from src.organizer import JobOrganizerError, organize_job_stream

st.set_page_config(page_title="Foreman AI Job Organizer", page_icon="🏗️", layout="wide")

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

default_text = """Project: Chen bathroom renovation
Client: Maya Chen
Address: 44 Pine Avenue

2026-07-27 - Crew note: Demolition is complete. Found moisture behind the shower wall.
Photo: dark staining around the lower-left corner of the shower framing.
Receipt: BuildMart, cement board and waterproofing membrane, $326.40.
Client text: "Please confirm whether the moisture issue changes the Friday tile start."
2026-07-28 - Inspector Lopez can visit at 2:30 PM on Thursday.
Delivery update: Vanity is delayed and now expected 2026-08-03.
"""

raw_text = st.text_area("Paste a messy job stream", value=default_text, height=300)

if st.button("Organize job", type="primary", use_container_width=True):
    try:
        with st.spinner("Organizing the job stream..."):
            result = organize_job_stream(raw_text)
        st.session_state["result"] = result.model_dump()
    except (ValueError, JobOrganizerError) as exc:
        st.error(str(exc))

if "result" in st.session_state:
    result = st.session_state["result"]

    left, right = st.columns([2, 1])

    with left:
        st.subheader("Organized timeline")
        for item in result["items"]:
            header = (
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
            for action in result["open_actions"]:
                st.checkbox(action, value=False)
        else:
            st.success("No open actions detected.")

        if result["warnings"]:
            st.subheader("Warnings")
            for warning in result["warnings"]:
                st.warning(warning)

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
