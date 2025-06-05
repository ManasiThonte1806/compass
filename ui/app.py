# --- FILE: ui/app.py ---

import streamlit as st
import datetime
import logging
import sys
import os
from pathlib import Path
import json
from typing import List, Dict, Optional, Any
import glob
import re

# Get the project root directory
script_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)

from agents.multi_tool_agent import create_tools, create_agent, run_agent_with_logging
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from feedback.logger import log_feedback
from security.pii_filter import redact_pii
from security.compliance_tagger import flag_compliance_terms
from dashboards.metrics import load_logs, calculate_queries_per_day, calculate_tool_usage, calculate_avg_response_time

load_dotenv()

logging.basicConfig(filename='ui_calls.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
tools = create_tools(llm)
agent = create_agent(tools, llm)

def get_unstructured_data(source: str) -> List[Dict]:
    unstructured_data = []
    parsed_data_path = "data/unstructured/parsed.jsonl"
    try:
        with open(parsed_data_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                if data['filename'] == source:
                    unstructured_data.append(data)
                    break
    except Exception as e:
        st.error(f"Error reading parsed data: {e}")
    return unstructured_data

import difflib

def highlight_text(text: str, highlights: List[Dict[str, str]]) -> str:
    for h in highlights:
        highlight = h.get("text")
        if highlight:
            # Try fuzzy match and find the closest substring in `text`
            match = difflib.get_close_matches(highlight, [text], n=1, cutoff=0.4)
            if match:
                close_match = match[0]
                # Escape original string to safely replace
                text = text.replace(close_match, f"<mark>{close_match}</mark>")
                print(f"[HIGHLIGHT] Applied fuzzy match: {close_match}")
    return text


def main():
    st.title("AllyIn Compass")

    st.markdown("""
        <style>
            mark {
                background-color: #ffe066; 
                padding: 2px 4px;
                border-radius: 4px;
                font-weight: bold;
            }
        </style>
    """, unsafe_allow_html=True)

    

    # --- Main Input Section ---
    user_query = st.text_input("Ask a question:", placeholder="e.g., What is Alice Smith's role?")

    domain = st.selectbox("Select Domain:", ["General", "Finance", "Biotech", "Energy"])

    with st.sidebar:
       
        st.header("Filters")
        st.slider("Confidence Threshold", 0.0, 1.0, 0.5)
        st.date_input("Date Range", (datetime.date(2023, 1, 1), datetime.date.today()))

        source = st.selectbox("Select Source:", [
        "All", "Customers", "Orders", "Products",
        "email1.eml", "email2.eml", "email3.eml",
        "PDF1.pdf", "pdf2.pdf", "pdf3.pdf",
        "finance.pdf", "biotech.pdf", "energy.pdf"
    ])

        st.header("Dashboard")
        logs = load_logs()
        if not logs.empty:
            st.subheader("Queries Per Day")
            st.bar_chart(calculate_queries_per_day(logs))
            st.subheader("Tool Usage Frequency")
            st.bar_chart(calculate_tool_usage(logs))
            st.subheader("Average Response Time")
            st.metric("Avg. Response Time (s)", f"{calculate_avg_response_time(logs):.2f}")
        else:
            st.info("No logs yet.")


    if user_query:
        st.subheader("Answer:")
        try:
            unstructured_data = get_unstructured_data(source) if source.endswith(('.pdf', '.eml')) else []
            
            # --- MODIFICATION: SIMPLIFIED CALL TO run_agent_with_logging ---
            # The logic for determining 'agent_input' based on 'source'
            # (including the 'All' source with keyword checks)
            # now lives entirely within multi_tool_agent.py's run_agent_with_logging function.
            # Here, we just pass the selected 'source' directly.
            agent_response = run_agent_with_logging(agent, user_query, domain, source, unstructured_data)

            answer = agent_response.get("answer", "")
            highlights = agent_response.get("source_highlights", [])
            highlighted_answer = highlight_text(answer, highlights) if highlights else answer

            st.markdown(highlighted_answer, unsafe_allow_html=True)

            redacted = redact_pii(answer)
            with st.expander("Redacted Answer"):
                st.write(redacted)

            flagged = flag_compliance_terms(answer)
            if flagged:
                st.warning(f"Compliance warning: {flagged}")
            else:
                st.info("No compliance concerns.")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("👍"):
                    log_feedback(user_query, answer, 1)
                    st.success("Thanks for your feedback!")
            with col2:
                if st.button("👎"):
                    log_feedback(user_query, answer, -1)
                    st.warning("We'll use this to improve.")

        except Exception as e:
            st.error(f"An error occurred: {e}")

   
if __name__ == "__main__":
    main()