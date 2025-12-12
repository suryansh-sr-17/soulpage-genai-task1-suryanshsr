import streamlit as st
import sys
import os
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup
load_dotenv()
logging.basicConfig(level=logging.INFO)
st.set_page_config(page_title="Company Intelligence Agent", layout="wide")

import streamlit as st
import sys
import os
import json
import logging
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orchestrator import Orchestrator
st.markdown("Generate evidence-backed intelligence reports using AI agents.")

# Sidebar Inputs
with st.sidebar:
    st.header("Configuration")
    company_name = st.text_input("Company Name", value="Tesla")
    ticker = st.text_input("Ticker Symbol", value="TSLA")
    
    today = datetime.now().date()
    # User's system is in 2025, but data is needed for 2024
    # Defaulting to 1 year ago effectively
    real_time_approx = today - timedelta(days=365)
    
    default_start = real_time_approx - timedelta(days=7)
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From Date", value=default_start)
    with col2:
        end_date = st.date_input("To Date", value=real_time_approx)
        
    top_k = st.slider("Top-K Sources", min_value=3, max_value=20, value=5)
    
    generate_btn = st.button("Generate Report", type="primary")

# Main Content
if generate_btn:
    if not company_name or not ticker:
        st.error("Please provide both Company Name and Ticker.")
    else:
        try:
            status_container = st.container()
            with st.status("Running Agentic Pipeline...", expanded=True) as status:
                st.write("Initializing agents...")
                orchestrator = Orchestrator()
                
                st.write("🕵️‍♀️ Collecting data (News + Prices)...")
                
                # We simply call run directly. 
                # In a more complex app, we might hook into logs to update status in real-time.
                report = orchestrator.run(
                    company=company_name,
                    ticker=ticker,
                    from_date=str(start_date),
                    to_date_param=str(end_date),
                    top_k=top_k
                )
                
                status.update(label="Analysis Complete!", state="complete", expanded=False)
            
            # Display Report
            st.divider()
            st.header(f"Intelligence Report: {company_name} ({ticker})")
            
            # Summary & Sentiment
            col_summ, col_meta = st.columns([3, 1])
            with col_summ:
                st.subheader("Executive Summary")
                st.write(report.get("summary", "No summary available."))
            
            with col_meta:
                st.subheader("Sentiment")
                sentiment = report.get("sentiment", "neutral").lower()
                color = "gray"
                if sentiment == "positive": color = "green"
                elif sentiment == "negative": color = "red"
                st.markdown(f":{color}[{sentiment.upper()}]")
                
                st.subheader("Confidence")
                conf = report.get("confidence", 0.0)
                st.progress(conf)
                st.caption(f"{conf*100:.1f}%")

            # Drivers & Risks
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📈 Key Drivers")
                for item in report.get("key_drivers", []):
                    st.markdown(f"- {item}")
            
            with col2:
                st.subheader("⚠️ Major Risks")
                for item in report.get("risks", []):
                    st.markdown(f"- {item}")
            
            # Evidence
            st.subheader("🔍 Key Evidence")
            evidence = report.get("evidence", [])
            if evidence:
                # Format as table
                evidence_data = []
                for e in evidence:
                    evidence_data.append({
                        "Quote": e.get("quote"),
                        "Source Article": e.get("article_id"),
                        "Link": e.get("url")
                    })
                st.dataframe(evidence_data, use_container_width=True, column_config={
                     "Link": st.column_config.LinkColumn("Source URL")
                })
            else:
                st.info("No specific evidence cited.")
                
            # JSON Export
            st.divider()
            json_str = json.dumps(report, indent=2)
            st.download_button(
                label="Download JSON Report",
                data=json_str,
                file_name=f"report_{ticker}_{datetime.now().date()}.json",
                mime="application/json"
            )
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
            logging.error(f"UI Error: {e}")

else:
    st.info("Configure settings in the sidebar and click 'Generate Report' to start.")
