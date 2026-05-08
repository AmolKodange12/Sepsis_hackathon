import streamlit as st
import pandas as pd
import json
import os
import glob

st.set_page_config(page_title="Sepsis Counterfactual Explorer", layout="wide")

# --- PATH CONFIG ---
# Points to where your AI-extracted JSONs live
DATA_DIR = "data/mortality_counterfactuals"

@st.cache_data
def load_all_extractions():
    """Loads PaperExtractions format JSONs into a flat list for dataframes."""
    all_data = []
    if not os.path.exists(DATA_DIR):
        return []
    
    # Grab all results.json files
    json_files = glob.glob(os.path.join(DATA_DIR, "*_results.json"))
    
    for file_path in json_files:
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                # Ensure we are looking at the 'extractions' key from your new schema
                if "extractions" in data:
                    paper_id = data.get("paper_id", "Unknown")
                    year = data.get("year", "N/A")
                    
                    for ext in data["extractions"]:
                        # Flatten the structure for the table
                        ext['source_paper'] = paper_id
                        ext['year'] = year
                        all_data.append(ext)
            except Exception as e:
                continue
    return all_data

# --- DATA LOADING ---
all_evidence = load_all_extractions()

# --- UI HEADER ---
st.title("🟢 Use Case 1: Mortality Benchmarking")
st.markdown("""
This view aggregates **Hazard Ratios (HR)** and **Odds Ratios (OR)** extracted from clinical literature 
to help estimate the expected mortality (Counterfactual) for your patient registry.
""")

if not all_evidence:
    st.warning(f"No extraction files found in `{DATA_DIR}`. Run your extraction script first!")
else:
    # Create Dataframe
    df = pd.DataFrame(all_evidence)

    # --- SIDEBAR FILTERS ---
    with st.sidebar:
        st.header("Filter Evidence")
        all_papers = sorted(list(df['source_paper'].unique()))
        selected_paper = st.multiselect("Filter by Paper", all_papers, default=all_papers)
        
        st.divider()
        st.write("**Quick Metrics**")
        st.metric("Total Associations", len(df))
        # Count mentions of HR/OR in variables
        prognostic_count = df['variable'].str.contains('HR|OR|P-value', case=False).sum()
        st.metric("Statistical Predictors", prognostic_count)

    # Filter Data
    filtered_df = df[df['source_paper'].isin(selected_paper)]

    # --- MAIN CONTENT ---
    tab1, tab2 = st.tabs(["📊 Evidence Table", "🔍 Deep Traceability"])

    with tab1:
        st.subheader("Extracted Clinical Variables & Effects")
        
        # Search bar for specific variables (e.g., Lactate)
        search = st.text_input("🔍 Search Predictors", placeholder="e.g., Lactate, SOFA, APACHE")
        if search:
            filtered_df = filtered_df[
                filtered_df['variable'].str.contains(search, case=False) | 
                filtered_df['evidence_text'].str.contains(search, case=False)
            ]

        # Clean up columns for display
        display_cols = ['variable', 'value', 'source_paper', 'year', 'evidence_text']
        # Filter to only existing columns to prevent errors
        actual_cols = [c for c in display_cols if c in filtered_df.columns]
        
        st.dataframe(
            filtered_df[actual_cols], 
            width='stretch', 
            hide_index=True
        )

    with tab2:
        st.subheader("Evidence Grounding")
        st.info("Review the raw text sentences where the AI found the prognostic values.")
        
        for _, row in filtered_df.iterrows():
            with st.expander(f"📄 {row['source_paper']} | {row['variable']}"):
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.metric("Extracted Value", row['value'])
                with col2:
                    st.markdown(f"**Evidence Text:**\n> {row['evidence_text']}")
                    st.caption(f"Source Type: {row.get('source_type', 'N/A')}")

# --- DOWNLOAD FOR ANALYSIS ---
if all_evidence:
    csv = df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        "Download Evidence CSV",
        csv,
        "sepsis_mortality_evidence.csv",
        "text/csv",
        key='download-csv'
    )