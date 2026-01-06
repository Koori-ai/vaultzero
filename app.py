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
import tempfile
import shutil

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
                if 'IMPORT_ERROR_TRACEBACK' in globals():
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
            # Create temp directory for uploaded files
            temp_dir = tempfile.mkdtemp()
            file_paths = []
            
            try:
                # Save uploaded files to temp directory
                with st.spinner("📤 Saving uploaded files..."):
                    for uploaded_file in uploaded_files:
                        file_path = os.path.join(temp_dir, uploaded_file.name)
                        with open(file_path, 'wb') as f:
                            f.write(uploaded_file.getbuffer())
                        file_paths.append(file_path)
                    st.success(f"✅ Saved {len(file_paths)} files")
                
                # Initialize orchestrator
                with st.spinner("🤖 Initializing AI agents..."):
                    orchestrator = VaultZeroOrchestrator(api_key=api_key)
                    st.success("✅ Agents initialized")
                
                # Run assessment
                st.markdown("### 🔄 Agent Workflow Progress")
                
                progress_placeholder = st.empty()
                
                with st.spinner("🔍 Running AI-powered assessment..."):
                    progress_placeholder.info("📄 Document Agent: Analyzing uploaded files...")
                    
                    # Run the orchestrator workflow
                    async def run_workflow():
                        try:
                            result = await orchestrator.run_assessment(
                            uploaded_files=file_paths,
                            mode='ai'
                            )
                            return result
                        except Exception as e:
                            st.error(f"❌ Workflow error: {str(e)}")
                            st.code(traceback.format_exc())
                            return None
                    
                    # Execute async workflow
                    result = asyncio.run(run_workflow())
                    
                    if result:
                        progress_placeholder.success("✅ Assessment complete!")
                        
                        # Display results
                        st.markdown("### 📊 Assessment Results")
                        
                        # Overall maturity score
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            overall_score = result.get('overall_maturity_score', 0)
                            st.metric("Overall Maturity Score", f"{overall_score:.1f}/5.0")
                        
                        with col2:
                            maturity_level = result.get('overall_maturity_level', 'Unknown')
                            st.metric("Maturity Level", maturity_level)
                        
                        with col3:
                            docs_analyzed = result.get('documents_analyzed', 0)
                            st.metric("Documents Analyzed", docs_analyzed)
                        
                        # Zero Trust Pillar Scores
                        if 'zt_scores' in result and result['zt_scores']:
                            st.markdown("#### 🎯 Zero Trust Pillar Scores")
                            zt_scores = result['zt_scores']
                            
                            cols = st.columns(4)
                            pillar_names = list(zt_scores.keys())
                            
                            for i, pillar in enumerate(pillar_names):
                                with cols[i % 4]:
                                    score = zt_scores[pillar]
                                    st.metric(pillar, f"{score:.1f}/5.0")
                        
                        # Strengths and Gaps
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if 'zt_strengths' in result and result['zt_strengths']:
                                st.markdown("#### ✅ Strengths")
                                for strength in result['zt_strengths'][:5]:
                                    st.success(f"• {strength}")
                        
                        with col2:
                            if 'zt_gaps' in result and result['zt_gaps']:
                                st.markdown("#### ⚠️ Gaps Identified")
                                for gap in result['zt_gaps'][:5]:
                                    st.warning(f"• {gap}")
                        
                        # Recommendations
                        if 'zt_recommendations' in result and result['zt_recommendations']:
                            st.markdown("#### 💡 Recommendations")
                            for i, rec in enumerate(result['zt_recommendations'][:5], 1):
                                st.info(f"{i}. {rec}")
                        
                        # Compliance Status
                        if 'compliance_percentage' in result:
                            st.markdown("#### 📋 Compliance Status")
                            compliance_pct = result['compliance_percentage']
                            st.progress(min(compliance_pct / 100, 1.0))
                            st.text(f"Compliance: {compliance_pct:.1f}%")
                        
                        # Download report
                        if 'report_path' in result and os.path.exists(result['report_path']):
                            st.markdown("### 📄 Download Report")
                            with open(result['report_path'], 'rb') as f:
                                st.download_button(
                                    label="📥 Download Assessment Report (DOCX)",
                                    data=f.read(),
                                    file_name=f"VaultZero_Assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                )
                        
                        # Raw results (expandable)
                        with st.expander("🔍 View Raw Results (JSON)"):
                            st.json(result)
                    else:
                        st.error("❌ Assessment failed - check error details above")
                
            except Exception as e:
                st.error(f"❌ Error during assessment: {str(e)}")
                st.code(traceback.format_exc())
            
            finally:
                # Cleanup temp directory
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
        
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