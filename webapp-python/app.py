"""Streamlit UI for the Job Organizer (Python port).

Paste a messy job stream, get a categorized timeline, a job summary, a
next-actions checklist, review flags, and a downloadable JSON — the same
structured contract as the PHP web app. Runs on Anthropic Claude when a key is
set, otherwise a rule-based local engine (demo mode).

    streamlit run app.py
"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src import aggregate, providers
from src.organizer import organize_stream
from src.schema import CATEGORY_LABELS

load_dotenv()

st.set_page_config(page_title="Job Organizer", page_icon="🗂️", layout="wide")

SAMPLES = Path(__file__).parent / "data" / "samples"


def flag_badge(flag: str) -> str:
    labels = {
        "safety_review": "🦺 Safety review",
        "missing_amount": "💲 Missing amount",
        "low_confidence": "❓ Low confidence",
        "possible_pii": "🔒 Possible PII",
        "needs_human": "👤 Needs human",
        "date_unverified": "📅 Date unverified",
    }
    return labels.get(flag, flag)


st.title("🗂️ Job Organizer")
st.caption("Turn a contractor's messy job stream into a clean, structured timeline.")

mode = "🟢 Live AI (Claude)" if providers.active_provider() == "claude" else "⚙️ Demo mode (rule-based — set ANTHROPIC_API_KEY for Claude)"
st.info(mode)

with st.sidebar:
    st.header("Samples")
    st.caption("Made-up data only — never real customer data.")
    picked = None
    for f in sorted(SAMPLES.glob("*.txt")):
        if st.button(f"📄 {f.stem}", use_container_width=True):
            picked = f.read_text(encoding="utf-8")

default = picked or st.session_state.get("stream", "")
stream = st.text_area("Paste the messy job stream", value=default, height=240, key="stream")

if st.button("✨ Organize", type="primary"):
    if not stream.strip():
        st.warning("Paste a job stream first.")
        st.stop()
    with st.spinner("Organizing…"):
        items = organize_stream(stream)
        summary = aggregate.summarize(items)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Items", summary["item_count"])
    c2.metric("Recorded spend", f"${summary['total_spend']:,.2f}")
    c3.metric("Labor hrs", summary["total_labor_hours"])
    c4.metric("Need review", summary["needs_review"])

    st.subheader("📋 Summary")
    st.write(summary["narrative"])
    if summary["safety_flags"]:
        st.error("🦺 Safety items need human review: " + "; ".join(summary["safety_flags"]))

    tab_items, tab_timeline, tab_actions, tab_json = st.tabs(
        ["Items", "Timeline", "Next actions", "Raw JSON"]
    )

    with tab_items:
        for it in items:
            with st.container(border=True):
                top = f"**{it.title or '(untitled)'}** — {CATEGORY_LABELS.get(it.category, it.category)}  ·  conf {int(it.category_confidence * 100)}%"
                st.markdown(top)
                st.write(it.summary)
                facts = []
                if it.occurred_at:
                    facts.append(f"📅 {it.occurred_at}")
                if it.vendor:
                    facts.append(f"🏬 {it.vendor}")
                if it.amount is not None:
                    facts.append(f"💲 ${it.amount:,.2f}")
                if it.phase:
                    facts.append(f"🔧 {it.phase}")
                if facts:
                    st.caption("  ·  ".join(facts))
                if it.flags:
                    st.write(" ".join(f"`{flag_badge(f)}`" for f in it.flags))
                if it.compliance_notes:
                    st.caption("⚠ " + it.compliance_notes)

    with tab_timeline:
        for row in summary["timeline"]:
            st.markdown(f"**{row['date'] or 'No date'}** — {CATEGORY_LABELS.get(row['category'], row['category'])}: {row['title']}")
            st.caption(row["summary"])

    with tab_actions:
        if not summary["next_actions"]:
            st.success("No open next actions.")
        for i, action in enumerate(summary["next_actions"]):
            st.checkbox(action, key=f"action_{i}")

    with tab_json:
        payload = {"items": [it.model_dump() for it in items], "summary": summary}
        st.code(json.dumps(payload, indent=2, ensure_ascii=False), language="json")
        st.download_button(
            "⬇ Download JSON",
            json.dumps(payload, indent=2, ensure_ascii=False),
            file_name="job_organized.json",
            mime="application/json",
        )

st.caption("Organizes information only — not legal, financial, or engineering advice. Sample data is fictional.")
