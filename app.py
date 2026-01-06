"""
VaultZero v2.0 - AI-Powered Zero Trust Assessment
"""
import streamlit as st
import asyncio
import os
from pathlib import Path
import json
from datetime import datetime
import traceback

# Try importing and capture any errors
AGENTS_AVAILABLE = False
IMPORT_ERROR = None

try:
    from orchestrator import VaultZeroOrchestrator
    AGENTS_AVAILABLE = True
except Exception as e:
    IMPORT_ERROR = str(e)
    IMPORT_ERROR_TRACEBACK = traceback.format_exc()

# Page config
st.set_page_config(
    page_title="VaultZero v2.0",
    page_icon="🔒",
    layout="wide"
)

st.title("🔒 VaultZero v2.0")
st.subheader("AI-Powered Zero Trust Assessment")

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Status")
    
    if AGENTS_AVAILABLE:
        st.success("✅ AI Agents Ready")
    else:
        st.error("⚠️ AI Agents Not Available")
        if IMPORT_ERROR:
            with st.expander("🔍 Error Details", expanded=True):
                st.code(IMPORT_ERROR)
                st.code(IMPORT_ERROR_TRACEBACK)

# Main content
if AGENTS_AVAILABLE:
    st.success("✅ System ready for AI-powered assessments!")
    
    # File upload
    uploaded_files = st.file_uploader(
        "Upload Documents",
        type=['pdf', 'docx', 'txt', 'pptx', 'xlsx'],
        accept_multiple_files=True,
        help="Upload Zero Trust architecture docs, policies, configs, etc."
    )
    
    if uploaded_files:
        st.info(f"📁 {len(uploaded_files)} files uploaded")
        
        # Show file details
        for file in uploaded_files:
            st.text(f"• {file.name} ({file.size / 1024:.1f} KB)")
        
       # Get API key from secrets (never from user input!)
        api_key = os.getenv('ANTHROPIC_API_KEY') or st.secrets.get("ANTHROPIC_API_KEY")
        
        if not api_key:
            st.warning("⚠️ API key not configured. Add ANTHROPIC_API_KEY to .env or Streamlit secrets.")
        
        if api_key and st.button("🚀 Run AI Assessment"):
            with st.spinner("Running AI-powered assessment..."):
                try:
                    # TODO: Implement actual workflow
                    st.info("🤖 Agent workflow will be implemented here!")
                    st.success("✅ Assessment complete! (Demo mode)")
                    
                    # Placeholder results
                    st.markdown("### 📊 Results Preview")
                    st.json({
                        "status": "demo",
                        "files_processed": len(uploaded_files),
                        "message": "Full agent workflow coming soon!"
                    })
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.code(traceback.format_exc())
        
else:
    st.error("⚠️ Cannot run assessments - AI agents not available")
    st.info("Check the error details in the sidebar")
    
    st.markdown("---")
    st.markdown("### 🔧 Troubleshooting")
    st.markdown("""
    **Common issues:**
    1. Missing dependencies: `pip install langgraph langchain langchain-anthropic`
    2. Agent import errors: Check `agents/` folder
    3. Orchestrator errors: Check `orchestrator.py`
    """)

# Footer
st.markdown("---")
st.caption("VaultZero v2.0 | AI-Powered Zero Trust Assessment | Powered by Claude & LangGraph")