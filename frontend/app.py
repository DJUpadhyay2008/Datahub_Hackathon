# ==============================================================================
# FILE: frontend/app.py
# WHY THIS FILE EXISTS:
#   Main entrypoint for the Streamlit Web Application for DataHub Learning Lab.
# WHAT IT DOES:
#   1. Sets up Streamlit page layout, modern dark theme styling, and sidebar navigation.
#   2. Routes between Dashboard, Metadata Explorer, Lineage Viewer, AI Grounded Chatbot, and Architecture Guides.
# HOW IT INTERACTS WITH DATAHUB:
#   Serves as the unified graphical interface consuming metadata APIs from FastAPI backend (`backend/main.py`).
# ==============================================================================

import streamlit as st
import requests

# Page Configuration
st.set_page_config(
    page_title="DataHub Learning Lab",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Modern Aesthetics
st.markdown("""
<style>
    .main {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .stCard {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    h1, h2, h3 {
        color: #38bdf8 !important;
    }
    .stButton>button {
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

# Imports for components
from components.metadata_explorer import render_metadata_explorer
from components.ai_assistant import render_ai_assistant
from components.lineage_viewer import render_lineage_dag
from components.autodoc_console import render_autodoc_console
from datahub_client import FALLBACK_METADATA

# Sidebar Navigation
st.sidebar.image("https://raw.githubusercontent.com/datahub-project/datahub/master/docs/img/datahub-logo-color-light.png", width=200)
st.sidebar.title("DataHub Learning Lab")
st.sidebar.caption("Interactive Educational Project for DataHub OSS, Lineage & Grounded AI")

page = st.sidebar.radio(
    "Navigation Menu",
    options=[
        "🏠 Home Dashboard",
        "🔍 Metadata Explorer (Steps 4 & 7)",
        "🔄 Lineage DAG Viewer (Step 3)",
        "🤖 AI Grounded Assistant (Step 6)",
        "🤖 AutoDoc Agent (Step 8)",
        "📖 DataHub Architecture Guide"
    ]
)

# Backend URL Check
BACKEND_URL = "http://localhost:8000"

def get_backend_status():
    try:
        r = requests.get(BACKEND_URL, timeout=1)
        return r.status_code == 200, r.json()
    except Exception:
        return False, None

backend_online, backend_info = get_backend_status()

# Sidebar Status Indicators
st.sidebar.markdown("---")
st.sidebar.markdown("### 🚦 Service Status")
if backend_online:
    st.sidebar.success("✅ FastAPI Backend: ONLINE")
    gms_connected = backend_info.get("datahub_gms_connected", False)
    if gms_connected:
        st.sidebar.success("✅ DataHub GMS: CONNECTED")
    else:
        st.sidebar.warning("⚡ DataHub GMS: Standalone Mode")
else:
    st.sidebar.error("❌ FastAPI Backend: Offline")
    st.sidebar.caption("Run `./venv/bin/python backend/main.py` to start API")

# ------------------------------------------------------------------------------
# PAGE ROUTING LOGIC
# ------------------------------------------------------------------------------

if page == "🏠 Home Dashboard":
    st.title("🛡️ Welcome to DataHub Learning Lab")
    st.subheader("Understand Metadata, Ingestion, Lineage, Ownership & Grounded AI through Code")

    st.markdown("""
    This project is designed to visually demonstrate **how DataHub works internally** using a realistic E-Commerce scenario.
    
    ### 🎯 E-Commerce Data Ecosystem
    The database contains tables representing transactional e-commerce workflows:
    - 👤 **`customers`**: Demographic PII contact data.
    - 🛒 **`orders`**: Transactional header orders.
    - 📦 **`products`**: Master product catalog.
    - 💳 **`payments`**: Financial transactions.
    - 🏬 **`inventory`**: Warehouse stock levels per product.
    - ⭐ **`reviews`**: Customer ratings and text feedback.
    - 📊 **`sales_report`**: Aggregated daily revenue statistics.
    - 📈 **`revenue_dashboard`**: Executive BI dashboard metrics.
    """)

    st.markdown("---")
    
    # Key Concepts Cards
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        #### 📦 Metadata vs Data
        * **Data**: Actual rows inside PostgreSQL (`Alice Smith`, `$249.99`).
        * **Metadata**: Data about data (Schema types, Owners, Lineage, PII tags, Column descriptions).
        """)
    with c2:
        st.markdown("""
        #### 🔄 Lineage & Ownership
        * **Lineage**: Graph of upstream source tables generating downstream reports.
        * **Ownership**: Technical & business point of contacts for each dataset aspect.
        """)
    with c3:
        st.markdown("""
        #### 🤖 Grounded AI
        * Prevents LLM hallucinations by querying DataHub BEFORE sending context to Gemini or local `llama.cpp` (`gemma4:e2b`).
        """)

elif page == "🔍 Metadata Explorer (Steps 4 & 7)":
    render_metadata_explorer()

elif page == "🔄 Lineage DAG Viewer (Step 3)":
    st.markdown("## 🔄 DataHub Lineage Graph Visualizer")
    st.caption("Step 3: Visualizing upstream inputs and downstream outputs (Customers ➔ Orders ➔ Sales Report ➔ Revenue Dashboard).")
    
    table_choice = st.selectbox("Select Target Dataset for Lineage Analysis:", list(FALLBACK_METADATA.keys()), format_func=lambda x: FALLBACK_METADATA[x]["name"])
    selected_name = FALLBACK_METADATA[table_choice]["name"]
    render_lineage_dag(selected_name, FALLBACK_METADATA)

elif page == "🤖 AI Grounded Assistant (Step 6)":
    render_ai_assistant()

elif page == "🤖 AutoDoc Agent (Step 8)":
    render_autodoc_console()

elif page == "📖 DataHub Architecture Guide":
    st.markdown("## 📖 DataHub Educational & Architecture Guide")
    
    st.markdown("""
    ### 1. DataHub OSS Docker Services Breakdown (Step 1)
    - **`datahub-gms` (Port 8080)**: Generalized Metadata Service backend. Serves GraphQL and REST APIs.
    - **`datahub-frontend` (Port 9002)**: Web dashboard UI for human users.
    - **`elasticsearch` (Port 9200)**: Full-text search engine powering dataset and entity searches.
    - **`kafka` & `zookeeper` (Port 9092)**: Async event stream publishing MetadataChangeEvents (MCE).
    - **`schema-registry` (Port 8081)**: Manages Avro schemas for Kafka payloads.
    
    ### 2. Ingestion & Lineage Mechanics (Steps 2 & 3)
    - **Ingestion**: DataHub connects via PostgreSQL connector (`docker/datahub-ingestion/postgres_ingestion.yml`), reads system catalog (`pg_catalog`), and posts metadata aspects to GMS.
    - **Lineage**: Programmatically emitted via Python REST Emitter (`docker/datahub-ingestion/lineage_emission.py`).
    
    ### 3. How AI Grounding Works (Step 6)
    1. User asks: *"What dashboards depend on Orders?"*
    2. Backend queries DataHub API to get lineage graph for `orders`.
    3. Grounded context is formatted and injected into System Prompt.
    4. Prompt dispatched to Gemini API or local `llama.cpp` (`gemma4:e2b`).
    5. Zero hallucination response delivered to user!
    """)
