from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import streamlit as st

from src.organizer import JobOrganizerError, organize_job_stream, save_result

st.set_page_config(
    page_title="Foreman AI Job Organizer",
    page_icon="🏗️",
    layout="wide",
)

st.title("🏗️ Foreman AI Job Organizer")
st.caption(
    "Turn messy construction-job notes, receipts, photo captions, and updates "
    "into a clean timeline with open actions."
)

with st.sidebar:
    st.header("Settings")
    has_key = bool(os.getenv("GROQ_API_KEY"))
    use_demo = st.toggle("Demo mode (no API key)", value=not has_key)
    if has_key and not use_demo:
        st.success("Groq API connected")
    elif use_demo:
        st.info("Rule-based demo mode is active.")
    else:
        st.warning("Add GROQ_API_KEY to .env or Streamlit secrets.")

    st.markdown(
        """
**Privacy rule**

Use made-up sample information only. Do not paste real Foreman customer or
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

raw_text = st.text_area(
    "Paste a messy job stream",
    value=default_text,
    height=300,
)

if st.button("Organize job", type="primary", use_container_width=True):
    try:
        with st.spinner("Organizing the job stream..."):
            result = organize_job_stream(raw_text, demo_mode=use_demo)

        st.session_state["result"] = result.model_dump()
    except (ValueError, JobOrganizerError) as exc:
        st.error(str(exc))

if "result" in st.session_state:
    result = st.session_state["result"]

    left, right = st.columns([2, 1])

    with left:
        st.subheader("Organized timeline")
        for item in result["items"]:
            with st.expander(
                f"{item['item_id']} · {item['category'].replace('_', ' ').title()} · "
                f"{item['title']}",
                expanded=True,
            ):
                st.write(item["summary"])
                c1, c2, c3 = st.columns(3)
                c1.metric("Date", item["date"] or "Not found")
                c2.metric("Priority", item["priority"].title())
                c3.metric("Confidence", item["confidence"].title())
                if item["amount"] is not None:
                    st.write(
                        f"**Amount:** {item['amount']:.2f} "
                        f"{item['currency'] or ''}".strip()
                    )
                if item["action_required"]:
                    st.warning(f"Action: {item['action']}")
                st.caption(f"Source: “{item['source_excerpt']}”")

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

    json_text = json.dumps(result, indent=2, ensure_ascii=False)
    st.download_button(
        "Download JSON",
        data=json_text,
        file_name="organized_job.json",
        mime="application/json",
        use_container_width=True,
    )

    if st.button("Save result locally"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = save_result(
            organize_job_stream(raw_text, demo_mode=use_demo),
            Path("outputs") / f"streamlit_{timestamp}.json",
        )
        st.success(f"Saved to {path}")
