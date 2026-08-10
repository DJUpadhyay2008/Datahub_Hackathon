# ==============================================================================
# FILE: frontend/components/metadata_explorer.py
# WHY THIS FILE EXISTS:
#   Implements the interactive Metadata Explorer page (Steps 4 & 7).
# WHAT IT DOES:
#   1. Renders dataset search bar and entity selector.
#   2. Displays Dataset Overview (Description, Platform, Owners, Tags).
#   3. Displays Column Schema table (Column Name, Data Type, Primary Key, Description).
#   4. Renders interactive Upstream and Downstream lineage buttons allowing full drilldown navigation.
# HOW IT INTERACTS WITH DATAHUB:
#   Calls backend API endpoints (`/search`, `/dataset`, `/schema`, `/lineage`) which fetch aspects from DataHub GMS.
# ==============================================================================

import streamlit as st
import pandas as pd
import requests
from components.lineage_viewer import render_lineage_dag

BACKEND_URL = "http://localhost:8000"

def render_metadata_explorer():
    st.markdown("## 🔍 DataHub Metadata Explorer")
    st.caption("Step 7: Click Dataset ➔ Schema ➔ Columns ➔ Lineage ➔ Downstream Assets to navigate metadata graphs.")

    # Search Bar
    search_query = st.text_input("🔎 Search DataHub Catalog (e.g., 'orders', 'email', 'customer', '*')", value="*")

    # Fetch datasets from backend API
    try:
        resp = requests.get(f"{BACKEND_URL}/search", params={"query": search_query}, timeout=3)
        search_data = resp.json()
        results = search_data.get("results", [])
    except Exception:
        st.warning("⚠️ FastAPI Backend offline. Loading cached client data.")
        from datahub_client import datahub_client
        results = datahub_client.search_datasets(search_query)

    if not results:
        st.info("No matching datasets found.")
        return

    # Dataset Selection Dropdown / Selector
    dataset_options = {item["name"]: item["urn"] for item in results}
    
    # Store selected table in session state for clickable navigation
    if "selected_dataset" not in st.session_state or st.session_state.selected_dataset not in dataset_options:
        st.session_state.selected_dataset = list(dataset_options.keys())[0]

    selected_name = st.selectbox(
        "Select Dataset to Explore:",
        options=list(dataset_options.keys()),
        index=list(dataset_options.keys()).index(st.session_state.selected_dataset)
    )
    st.session_state.selected_dataset = selected_name
    selected_urn = dataset_options[selected_name]

    # Fetch full dataset details
    try:
        ds_detail = requests.get(f"{BACKEND_URL}/dataset", params={"urn_or_name": selected_urn}).json()
    except Exception:
        from datahub_client import datahub_client
        ds_detail = datahub_client.get_dataset(selected_urn)

    if not ds_detail:
        st.error("Could not fetch dataset details.")
        return

    st.markdown("---")

    # --------------------------------------------------------------------------
    # 1. DATASET HEADER CARD & METADATA TOKENS
    # --------------------------------------------------------------------------
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown(f"### 📊 Table: `{ds_detail['name']}`")
        st.write(f"**Description:** {ds_detail.get('description', 'N/A')}")
        st.write(f"**Platform:** `{ds_detail.get('platform', 'postgres')}` | **Schema:** `{ds_detail.get('schema_name', 'ecommerce')}`")

    with col2:
        st.markdown("**👥 Technical & Business Owners:**")
        for owner in ds_detail.get("owners", []):
            st.info(f"👤 {owner}")
        
        st.markdown("**🏷️ Governance Tags:**")
        tags_html = " ".join([f"<span style='background-color:#3b82f6; color:white; padding:4px 8px; border-radius:12px; font-size:12px; margin-right:4px;'>{tag}</span>" for tag in ds_detail.get("tags", [])])
        st.markdown(tags_html, unsafe_allow_html=True)

    st.markdown("---")

    # --------------------------------------------------------------------------
    # 2. COLUMN SCHEMA LIST
    # --------------------------------------------------------------------------
    st.markdown("### 📋 Column Schema Metadata")
    cols = ds_detail.get("columns", [])
    if cols:
        df_cols = pd.DataFrame(cols)
        df_cols["is_pk"] = df_cols["is_pk"].apply(lambda x: "🔑 YES" if x else "NO")
        df_cols.rename(columns={
            "name": "Column Name",
            "type": "Data Type",
            "is_pk": "Primary Key",
            "description": "Column Description / PII Annotation"
        }, inplace=True)
        st.dataframe(df_cols, use_container_width=True)
    else:
        st.write("No column schema available.")

    st.markdown("---")

    # --------------------------------------------------------------------------
    # 3. LINEAGE & DOWNSTREAM ASSET EXPLORER
    # --------------------------------------------------------------------------
    st.markdown("### 🔄 Lineage & Downstream Impact Explorer")
    
    col_up, col_down = st.columns(2)

    with col_up:
        st.markdown("#### ⬅️ Upstream Source Inputs")
        upstreams = ds_detail.get("upstreams", [])
        if upstreams:
            for up in upstreams:
                up_table = up.split(".")[-1].replace(",PROD)", "")
                if st.button(f"➔ Jump to Upstream: {up_table}", key=f"up_{up_table}"):
                    st.session_state.selected_dataset = up_table
                    st.rerun()
        else:
            st.caption("No upstream sources (Root transactional table).")

    with col_down:
        st.markdown("#### ➡️ Downstream Dependent Assets")
        downstreams = ds_detail.get("downstreams", [])
        if downstreams:
            for down in downstreams:
                down_table = down.split(".")[-1].replace(",PROD)", "")
                if st.button(f"➔ Jump to Downstream: {down_table}", key=f"down_{down_table}"):
                    st.session_state.selected_dataset = down_table
                    st.rerun()
        else:
            st.caption("No downstream dependencies (Leaf dashboard/report asset).")

    st.markdown("---")
    
    # Render interactive graph
    from datahub_client import FALLBACK_METADATA
    render_lineage_dag(selected_name, FALLBACK_METADATA)
