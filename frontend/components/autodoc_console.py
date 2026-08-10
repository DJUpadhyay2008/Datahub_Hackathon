# ==============================================================================
# FILE: frontend/components/autodoc_console.py
# WHY THIS FILE EXISTS:
#   Implements the Streamlit UI tab component for the AutoDoc Agent.
# WHAT IT DOES:
#   1. Renders a control console to scan for undocumented datasets.
#   2. Displays discoveries, AI recommendations, missing fields, and approval state.
#   3. Integrates the Grounding Inspector to show schemas/lineages queried for each table.
#   4. Emits write-back calls for approved datasets individually.
# ==============================================================================

import streamlit as st
import requests
import json
import os
import sys

# Ensure backend directory is accessible
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "backend"))
from autodoc_agent import APPROVED_URNS

BACKEND_URL = "http://localhost:8000"

def render_autodoc_console():
    st.markdown("## 🤖 AutoDoc Agent & Governance Console")
    st.caption("Step 8: Discover datasets missing descriptions, owners, or tags. Grounded recommendations are generated using local Gemma 4 E2B.")

    # Session State Initialization
    if "autodoc_results" not in st.session_state:
        st.session_state.autodoc_results = []
    if "scan_performed" not in st.session_state:
        st.session_state.scan_performed = False

    st.markdown("---")

    # Control Button
    if st.button("🔍 Scan for Undocumented Datasets"):
        with st.spinner("Scanning metadata catalog and invoking local Gemma model..."):
            try:
                resp = requests.get(f"{BACKEND_URL}/autodoc/scan", timeout=120)
                if resp.status_code == 200:
                    st.session_state.autodoc_results = resp.json().get("results", [])
                    st.session_state.scan_performed = True
                    st.success(f"Scan complete! Discovered {len(st.session_state.autodoc_results)} undocumented dataset(s).")
                else:
                    st.error(f"Error during dataset scan: {resp.text}")
            except Exception as e:
                st.error(f"Failed to connect to backend scan endpoint: {e}")

    # Display Scan Results
    if st.session_state.scan_performed:
        if not st.session_state.autodoc_results:
            st.info("🎉 All datasets in the catalog are fully documented! No missing metadata found.")
        else:
            st.markdown("### 📋 Discovered Datasets & Grounded Suggestions")
            st.caption("Note: Write-back is locked for datasets not present on the administrator-approved URN list.")

            # Table Header Row
            header_cols = st.columns([3, 4, 2, 2, 2])
            with header_cols[0]:
                st.markdown("**Dataset / URN**")
            with header_cols[1]:
                st.markdown("**AI Suggestion Summary**")
            with header_cols[2]:
                st.markdown("**Missing Aspects**")
            with header_cols[3]:
                st.markdown("**Write-Back Status**")
            with header_cols[4]:
                st.markdown("**Actions**")

            st.markdown("---")

            # Render Table Content Rows
            for idx, ds in enumerate(st.session_state.autodoc_results):
                urn = ds["urn"]
                name = ds["name"]
                platform = ds["platform"]
                missing = [k for k, v in ds["missing"].items() if v]
                
                suggested = ds["suggested"]
                desc = suggested.get("description", "")
                tags = suggested.get("tags", [])
                owner = suggested.get("suggested_owner", "")
                confidence = suggested.get("confidence_note", "")
                
                is_approved = urn in APPROVED_URNS

                row_cols = st.columns([3, 4, 2, 2, 2])

                # Column 1: URN Info
                with row_cols[0]:
                    st.markdown(f"📁 **`{name}`** (platform: `{platform}`)")
                    st.caption(f"`{urn}`")

                # Column 2: Suggestion Summary
                with row_cols[1]:
                    st.markdown(f"📝 **Description**: {desc}")
                    st.markdown(f"🏷️ **Tags**: {', '.join(tags) if tags else '*None*'}")
                    st.markdown(f"👤 **Owner**: `{owner}`")

                # Column 3: Missing Fields
                with row_cols[2]:
                    st.markdown(", ".join(missing))

                # Column 4: Approved status
                with row_cols[3]:
                    if is_approved:
                        st.markdown("🟢 **Approved**")
                    else:
                        st.markdown("🔒 **Restricted**")
                        st.caption("Not approved for write-back")

                # Column 5: Write-back trigger
                with row_cols[4]:
                    if is_approved:
                        if st.button("✍️ Write to DataHub", key=f"write_btn_{idx}"):
                            with st.spinner("Writing metadata to DataHub..."):
                                try:
                                    payload = {
                                        "urn": urn,
                                        "description": desc,
                                        "tags": tags,
                                        "owner": owner
                                    }
                                    write_resp = requests.post(f"{BACKEND_URL}/autodoc/write", json=payload)
                                    if write_resp.status_code == 200:
                                        st.success("✅ Success!")
                                    else:
                                        st.error(f"Failed: {write_resp.json().get('detail', write_resp.text)}")
                                except Exception as err:
                                    st.error(f"Error: {err}")
                    else:
                        st.button("✍️ Write to DataHub", key=f"write_btn_{idx}", disabled=True, help="URN is not in APPROVED_URNS list.")

                # Reusing Grounding Inspector visual pattern
                with st.expander("🔍 GROUNDING INSPECTOR: View Raw DataHub Context Passed to LLM"):
                    st.caption("Proof of Grounding: DataHub was queried BEFORE sending prompt to LLM.")
                    st.code(ds["raw_context"], language="text")
                    st.markdown(f"**Model Confidence Reasoning**: *{confidence}*")

                st.markdown("---")
