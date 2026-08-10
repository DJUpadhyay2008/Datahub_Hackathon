# ==============================================================================
# FILE: frontend/components/ai_assistant.py
# WHY THIS FILE EXISTS:
#   Implements the Step 6 Grounded AI Assistant UI page in Streamlit.
# WHAT IT DOES:
#   1. Renders interactive chatbot interface connected directly to your active local `llama-server` (Gemma 4 E2B model).
#   2. Allows switching between local llama.cpp / Gemma server or Google Gemini API.
#   3. Displays a "Grounding Inspector" expander showing the raw DataHub context retrieved BEFORE calling the LLM.
# HOW IT INTERACTS WITH DATAHUB:
#   Sends requests to FastAPI backend `/ask` endpoint, demonstrating zero-hallucination grounded AI execution.
# ==============================================================================

import streamlit as st
import requests
import json

BACKEND_URL = "http://localhost:8000"

def render_ai_assistant():
    st.markdown("## 🤖 Grounded AI Governance Assistant")
    st.caption("Step 6: AI Chatbot grounded strictly on DataHub metadata using your local Gemma 4 E2B model.")

    # --------------------------------------------------------------------------
    # SIDEBAR / SETTINGS PANEL FOR LLM CONFIGURATION
    # --------------------------------------------------------------------------
    with st.expander("⚙️ LLM Provider & Model Settings", expanded=True):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            provider = st.selectbox(
                "Select LLM Provider:",
                options=["gemini", "llama_cpp"],
                index=0,
                help="Choose between Google Gemini API or your active local llama-server Gemma model."
            )
        with col_p2:
            if provider == "gemini":
                api_key = st.text_input("Gemini API Key:", type="password", value="", help="Enter GEMINI_API_KEY")
                llama_url = ""
                llama_model = ""
            else:
                api_key = ""
                llama_url = st.text_input("Local Endpoint URL:", value="http://localhost:8080/v1", help="llama-server / Ollama endpoint")
                llama_model = st.text_input("Local Model Name:", value="gemma-4-E2B-it-UD-Q4_K_XL.gguf", help="Active model name")

    st.markdown("---")

    # --------------------------------------------------------------------------
    # PRESET SAMPLE QUESTIONS
    # --------------------------------------------------------------------------
    st.markdown("#### 💡 Quick Test Questions (Click to Ask):")
    cols_preset = st.columns(3)
    
    preset_question = None
    with cols_preset[0]:
        if st.button("❓ What datasets contain customer email?"):
            preset_question = "What datasets contain customer email?"
        if st.button("❓ Who owns Inventory?"):
            preset_question = "Who owns Inventory?"
    with cols_preset[1]:
        if st.button("❓ What dashboards depend on Orders?"):
            preset_question = "What dashboards depend on Orders?"
        if st.button("❓ What columns exist in Products?"):
            preset_question = "What columns exist in Products?"
    with cols_preset[2]:
        if st.button("❓ What breaks if I delete Orders?"):
            preset_question = "What breaks if I delete Orders?"

    st.markdown("---")

    # Chat History Session State Initialization
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Chat Input Box
    user_input = st.chat_input("Ask a question about datasets, owners, lineage, or columns...")
    
    if preset_question:
        user_input = preset_question

    if user_input:
        # Append user message
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Prepare payload for backend API
        payload = {
            "question": user_input,
            "provider": provider,
            "api_key": api_key,
            "llama_url": llama_url,
            "llama_model": llama_model
        }
        
        with st.spinner("🔍 Step 1: Querying DataHub GMS ➔ Step 2: Generating response with Gemma 4 E2B..."):
            try:
                resp = requests.post(f"{BACKEND_URL}/ask", json=payload, timeout=25)
                res_data = resp.json()
            except Exception as e:
                # Direct fallback invocation
                from ai_grounding import answer_grounded_question
                res_data = answer_grounded_question(
                    user_input,
                    provider=provider,
                    api_key=api_key,
                    llama_url=llama_url,
                    llama_model=llama_model
                )

        # Append AI response
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": res_data.get("answer", "No answer returned."),
            "grounding_context": res_data.get("grounding_context", "")
        })

    # Render Conversation Stream
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(msg["content"])
                
                # GROUNDING INSPECTOR VISUAL EVIDENCE
                if "grounding_context" in msg and msg["grounding_context"]:
                    with st.expander("🔍 GROUNDING INSPECTOR: View Raw DataHub Context Passed to LLM"):
                        st.caption("Proof of Grounding: DataHub was queried BEFORE sending prompt to LLM.")
                        st.code(msg["grounding_context"], language="text")
