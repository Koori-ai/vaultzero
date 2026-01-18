"""
VaultZero Unified Platform
Combines VaultZero 1.0 (RAG), VaultZero 2.0 (AI Docs), and KEVS Dashboard
"""

import streamlit as st
import json
import os
import tempfile
import asyncio
from datetime import datetime
from pathlib import Path

# VaultZero 1.0 imports
from orchestrator_v1 import VaultZeroOrchestrator as VaultZeroOrchestratorV1
from rag.vectorstore import VaultZeroRAG
from huggingface_hub import hf_hub_download

# VaultZero 2.0 imports
from orchestrator import VaultZeroOrchestrator as VaultZeroOrchestratorV2

# KEVS Dashboard imports
from tools.kevs_tool import KEVSTool

import anthropic
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="VaultZero Platform",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-size: 1.1rem;
        padding: 0.75rem;
        border-radius: 0.5rem;
        border: none;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #1557a0;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        background-color: #d1ecf1;
        border-left: 5px solid #17a2b8;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize RAG system for V1.0
@st.cache_resource
def initialize_rag():
    """Initialize RAG system for VaultZero 1.0"""
    data_path = "./data/zt_synthetic_dataset_complete.json"
    persist_directory = "./data/chroma_db"
    
    os.makedirs("./data", exist_ok=True)
    
    if not os.path.exists(data_path):
        print("📥 Downloading dataset...")
        try:
            hf_hub_download(
                repo_id="Reply2susi/zero-trust-maturity-assessments",
                filename="zt_synthetic_dataset_complete.json",
                repo_type="dataset",
                local_dir="./data",
                token=os.getenv('HUGGINGFACE_TOKEN')
            )
        except:
            hf_hub_download(
                repo_id="Reply2susi/zero-trust-maturity-assessments",
                filename="zt_synthetic_dataset_complete.json",
                repo_type="dataset",
                local_dir="./data"
            )
    
    rag = VaultZeroRAG(data_path=data_path, persist_directory=persist_directory)
    rag.initialize()
    return rag

# AI Assistant function
def get_chat_response(user_message: str):
    """Get response from Claude API"""
    context_parts = []
    
    if st.session_state.get('v1_assessment_complete') and st.session_state.get('v1_results'):
        results = st.session_state.v1_results
        if 'summary' in results:
            summary = results['summary']
            context_parts.append(
                f"User's Assessment Results:\n"
                f"- Overall Score: {summary.get('current_score', 'N/A')}/4.0\n"
                f"- Maturity Level: {summary.get('current_maturity', 'N/A')}\n"
                f"- Percentile: {summary.get('peer_percentile', 'N/A')}th"
            )
    
    system_prompt = """You are a Zero Trust security expert assistant.

Your role is to:
- Answer questions about Zero Trust architecture
- Help users understand assessment results
- Provide guidance on improving Zero Trust maturity

The Zero Trust maturity scale is:
- 1.0 - Initial: Ad-hoc security
- 2.0 - Traditional: Basic perimeter security
- 3.0 - Advanced: Mature Zero Trust
- 4.0 - Optimal: Industry-leading

Be concise, helpful, and specific. Keep responses under 200 words.
"""
    
    if context_parts:
        system_prompt += f"\n\nCurrent User Context:\n" + "\n\n".join(context_parts)
    
    messages = [{"role": "user", "content": user_message}]
    
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=system_prompt,
            messages=messages
        )
        return response.content[0].text
    except Exception as e:
        return f"Error: {str(e)}"

# Initialize session state
if 'v1_assessment_complete' not in st.session_state:
    st.session_state.v1_assessment_complete = False
if 'v1_results' not in st.session_state:
    st.session_state.v1_results = None
if 'v2_assessment_complete' not in st.session_state:
    st.session_state.v2_assessment_complete = False
if 'v2_results' not in st.session_state:
    st.session_state.v2_results = None
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'show_chat' not in st.session_state:
    st.session_state.show_chat = False

# Header
st.markdown('<div class="main-header">🔒 VaultZero Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Unified Zero Trust Assessment & Threat Intelligence</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/300x100/1f77b4/ffffff?text=VaultZero", use_container_width=True)
    
    st.markdown("---")
    if st.button("💬 AI Assistant", key="sidebar_chat", use_container_width=True, type="primary"):
        st.session_state.show_chat = True
        st.rerun()
    st.markdown("---")
    
    st.markdown("### 📊 Platform Features")
    st.markdown("""
    **VaultZero 1.0**
    - Manual questionnaire
    - RAG-powered benchmarking
    - 6-month roadmap
    
    **VaultZero 2.0**
    - AI document analysis
    - Multi-agent workflow
    - Professional reports
    
    **KEVS Dashboard**
    - CISA vulnerabilities
    - Real-time threat intel
    - CVE enrichment
    """)
    
    st.markdown("---")
    st.markdown("### 🌟 Platform Capabilities")
    st.markdown("""
    - AI-Powered Zero Trust Assessment
    - Peer Benchmarking (21+ Organizations)
    - Real-time CISA Threat Intelligence
    - Automated Professional Reports
    
    **💪 Key Features:**
    - Advanced Multi-Agent Analysis
    - RAG-Based Comparisons
    - Live Vulnerability Tracking
    - Comprehensive Roadmaps
    """)

# AI Assistant Dialog
if st.session_state.show_chat:
    @st.dialog("💬 AI Assistant", width="large")
    def show_chat_dialog():
        st.markdown("### Ask me about Zero Trust!")
        
        suggestions = [
            ("❓", "What is Zero Trust?"),
            ("📝", "How should I score identity?"),
            ("💡", "Give me examples for networks"),
            ("🎯", "What's a good maturity score?"),
        ]
        
        st.markdown("**Quick questions:**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(suggestions[0][0] + " " + suggestions[0][1], key="q_0", use_container_width=True):
                st.session_state.chat_messages = []
                st.session_state.chat_messages.append({"role": "user", "content": suggestions[0][1]})
                with st.spinner("💨 Quick answer..."):
                    response = get_chat_response(suggestions[0][1])
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
                st.rerun()
        with col2:
            if st.button(suggestions[1][0] + " " + suggestions[1][1], key="q_1", use_container_width=True):
                st.session_state.chat_messages = []
                st.session_state.chat_messages.append({"role": "user", "content": suggestions[1][1]})
                with st.spinner("💨 Quick answer..."):
                    response = get_chat_response(suggestions[1][1])
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
                st.rerun()
        
        col3, col4 = st.columns(2)
        with col3:
            if st.button(suggestions[2][0] + " " + suggestions[2][1], key="q_2", use_container_width=True):
                st.session_state.chat_messages = []
                st.session_state.chat_messages.append({"role": "user", "content": suggestions[2][1]})
                with st.spinner("💨 Quick answer..."):
                    response = get_chat_response(suggestions[2][1])
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
                st.rerun()
        with col4:
            if st.button(suggestions[3][0] + " " + suggestions[3][1], key="q_3", use_container_width=True):
                st.session_state.chat_messages = []
                st.session_state.chat_messages.append({"role": "user", "content": suggestions[3][1]})
                with st.spinner("💨 Quick answer..."):
                    response = get_chat_response(suggestions[3][1])
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
                st.rerun()
        
        st.markdown("---")
        
        if st.session_state.chat_messages:
            chat_container = st.container(height=350)
            with chat_container:
                for message in st.session_state.chat_messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
        else:
            st.info("👋 Hi! I'm your Zero Trust AI assistant. Ask me anything!")
        
        user_input = st.chat_input("Type your question here...", key="chat_input_dialog")
        if user_input:
            st.session_state.chat_messages.append({"role": "user", "content": user_input})
            with st.spinner("Thinking..."):
                response = get_chat_response(user_input)
                st.session_state.chat_messages.append({"role": "assistant", "content": response})
            st.rerun()
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🗑️ Clear Chat", key="clear_btn", use_container_width=True):
                st.session_state.chat_messages = []
                st.rerun()
        with col2:
            if st.button("✖️ Close", key="close_btn", use_container_width=True):
                st.session_state.show_chat = False
                st.rerun()
    
    show_chat_dialog()

# Main Tabs
tab1, tab2, tab3 = st.tabs(["🔒 VaultZero 1.0 (RAG)", "🤖 VaultZero 2.0 (AI Docs)", "🛡️ KEVS Dashboard"])

# ============================================================================
# TAB 1: VAULTZERO 1.0 - MANUAL ASSESSMENT WITH RAG
# ============================================================================
with tab1:
    st.markdown("## 🔒 VaultZero 1.0 - Manual Assessment with RAG Benchmarking")
    st.markdown("*Answer questions about your system to get peer-benchmarked assessment*")
    
    if not st.session_state.v1_assessment_complete:
        with st.form("v1_assessment_form"):
            system_description = st.text_area(
                "**System Description**",
                placeholder="e.g., Cloud-based healthcare platform handling patient records...",
                height=100
            )
            
            st.markdown("### 🔐 Zero Trust Pillar Assessment")
            
            col1, col2 = st.columns(2)
            
            with col1:
                identity_answer = st.text_area(
                    "🔑 **Identity**",
                    placeholder="Describe your identity and access management...",
                    height=120,
                    key="v1_identity"
                )
                
                devices_answer = st.text_area(
                    "💻 **Devices**",
                    placeholder="Describe your device security...",
                    height=120,
                    key="v1_devices"
                )
                
                networks_answer = st.text_area(
                    "🌐 **Networks**",
                    placeholder="Describe your network security...",
                    height=120,
                    key="v1_networks"
                )
            
            with col2:
                applications_answer = st.text_area(
                    "📱 **Applications**",
                    placeholder="Describe your application security...",
                    height=120,
                    key="v1_applications"
                )
                
                data_answer = st.text_area(
                    "🗄️ **Data**",
                    placeholder="Describe your data protection...",
                    height=120,
                    key="v1_data"
                )
            
            submitted = st.form_submit_button("🚀 Run VaultZero 1.0 Assessment", use_container_width=True)
            
            if submitted:
                if not system_description or not all([identity_answer, devices_answer, networks_answer, applications_answer, data_answer]):
                    st.error("⚠️ Please fill in all fields!")
                else:
                    st.session_state.show_chat = False
                    
                    user_answers = {
                        "identity": identity_answer,
                        "devices": devices_answer,
                        "networks": networks_answer,
                        "applications": applications_answer,
                        "data": data_answer
                    }
                    
                    with st.spinner("🤖 Running RAG-powered assessment... 60-90 seconds..."):
                        try:
                            rag = initialize_rag()
                            orchestrator = VaultZeroOrchestratorV1(rag_system=rag)
                            results = orchestrator.run(system_description, user_answers)
                            
                            st.session_state.v1_results = results
                            st.session_state.v1_assessment_complete = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
    
    else:
        results = st.session_state.v1_results
        
        st.markdown('<div class="success-box">✅ Assessment Complete!</div>', unsafe_allow_html=True)
        
        st.markdown("## 📊 Executive Summary")
        summary = results['summary']
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Current Maturity", summary['current_maturity'])
        with col2:
            st.metric("Current Score", f"{summary['current_score']:.1f}/4.0")
        with col3:
            st.metric("Peer Percentile", f"{summary['peer_percentile']}th")
        with col4:
            st.metric("6-Month Target", summary['target_maturity'])
        with col5:
            st.metric("Investment", summary['investment_range'].split(' - ')[0], summary['investment_range'].split(' - ')[1])
        
        subtab1, subtab2, subtab3, subtab4 = st.tabs(["📋 Assessment", "📊 Benchmark", "🗺️ Roadmap", "📥 Download"])
        
        with subtab1:
            st.markdown("### 🔐 Pillar Results")
            assessment = results['assessment']
            for pillar_name, pillar_data in assessment['pillars'].items():
                with st.expander(f"**{pillar_name.upper()}** - {pillar_data['maturity_level']} ({pillar_data['score']:.1f}/4.0)"):
                    st.markdown(f"**Findings:** {pillar_data['findings']}")
                    if pillar_data.get('strengths'):
                        st.markdown("**✅ Strengths:**")
                        for s in pillar_data['strengths']:
                            st.markdown(f"- {s}")
                    if pillar_data.get('gaps'):
                        st.markdown("**⚠️ Gaps:**")
                        for g in pillar_data['gaps']:
                            st.markdown(f"- {g}")
        
        with subtab2:
            st.markdown("### 📊 Benchmark Analysis")
            benchmark = results['benchmark']
            st.markdown(f"**Competitive Position:** {benchmark['competitive_position']}")
        
        with subtab3:
            st.markdown("### 🗺️ 6-Month Roadmap")
            roadmap = results['roadmap']
            st.markdown(f"**Summary:** {roadmap['executive_summary']}")
        
        with subtab4:
            report_json = json.dumps(results, indent=2)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                "📥 Download Report (JSON)",
                data=report_json,
                file_name=f"vaultzero_v1_report_{timestamp}.json",
                mime="application/json",
                use_container_width=True
            )
        
        if st.button("🔄 New Assessment", use_container_width=True):
            st.session_state.v1_assessment_complete = False
            st.session_state.v1_results = None
            st.rerun()

# ============================================================================
# TAB 2: VAULTZERO 2.0 - AI DOCUMENT ANALYSIS (ENHANCED UI)
# ============================================================================
with tab2:
    st.markdown("## 🤖 VaultZero 2.0 - AI-Powered Document Analysis")
    st.markdown("*Upload documents for automated Zero Trust assessment*")
    
    if not st.session_state.v2_assessment_complete:
        # Enhanced file upload section
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("**📁 Supported Document Types:**")
        st.markdown("PDF • Word (DOCX) • Excel (XLSX) • PowerPoint (PPTX) • Text (TXT)")
        st.markdown('</div>', unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader(
            "📤 Upload your security documentation",
            type=['pdf', 'txt', 'docx', 'xlsx', 'pptx'],
            accept_multiple_files=True,
            help="Upload network diagrams, policies, configurations, or any security-related documents"
        )
        
        if uploaded_files:
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            st.markdown(f"**✅ {len(uploaded_files)} file(s) uploaded successfully**")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Show uploaded files in a nice table
            for idx, file in enumerate(uploaded_files, 1):
                col1, col2, col3 = st.columns([1, 3, 2])
                with col1:
                    st.markdown(f"**{idx}.**")
                with col2:
                    st.markdown(f"📄 {file.name}")
                with col3:
                    st.markdown(f"*{file.size:,} bytes*")
        
        if st.button("🚀 Run VaultZero 2.0 AI Assessment", disabled=not uploaded_files, use_container_width=True, type="primary"):
            st.session_state.show_chat = False
            
            # Progress indicator
            progress_container = st.container()
            
            with st.spinner("🤖 Running multi-agent AI analysis..."):
                try:
                    # Save files
                    temp_dir = tempfile.mkdtemp()
                    file_paths = []
                    for uploaded_file in uploaded_files:
                        file_path = os.path.join(temp_dir, uploaded_file.name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        file_paths.append(file_path)
                    
                    # Run assessment
                    orchestrator = VaultZeroOrchestratorV2(api_key=os.getenv("ANTHROPIC_API_KEY"))
                    result = asyncio.run(orchestrator.run_assessment(uploaded_files=file_paths, mode='ai'))
                    
                    st.session_state.v2_results = result
                    st.session_state.v2_assessment_complete = True
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error during assessment: {str(e)}")
                    st.exception(e)
    
    else:
        result = st.session_state.v2_results
        
        # Success banner
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.markdown("### ✅ Assessment Complete!")
        st.markdown("Your AI-powered Zero Trust assessment is ready for review.")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Main results section
        st.markdown("## 📊 Assessment Results")
        
        # Top-level metrics in colored boxes
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div class="info-box" style="text-align: center;">', unsafe_allow_html=True)
            st.markdown("**Overall Maturity Score**")
            st.markdown(f"# {result.get('overall_maturity_score', 0):.1f}/5.0")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="info-box" style="text-align: center;">', unsafe_allow_html=True)
            st.markdown("**Maturity Level**")
            st.markdown(f"# {result.get('overall_maturity_level', 'N/A')}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="info-box" style="text-align: center;">', unsafe_allow_html=True)
            st.markdown("**Documents Analyzed**")
            st.markdown(f"# {result.get('documents_analyzed', 0)}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Pillar Scores Section with better formatting
        st.markdown("### 🎯 Zero Trust Pillar Scores")
        
        scores = result.get('zt_scores', {})
        if scores:
            # Display in 2 columns with progress bars
            col1, col2 = st.columns(2)
            pillar_list = list(scores.items())
            mid = len(pillar_list) // 2 + len(pillar_list) % 2
            
            with col1:
                for pillar, score in pillar_list[:mid]:
                    st.markdown(f"**{pillar}**")
                    st.progress(min(score / 5.0, 1.0))
                    st.markdown(f"Score: {score}/5.0")
                    st.markdown("")
            
            with col2:
                for pillar, score in pillar_list[mid:]:
                    st.markdown(f"**{pillar}**")
                    st.progress(min(score / 5.0, 1.0))
                    st.markdown(f"Score: {score}/5.0")
                    st.markdown("")
        
        st.markdown("---")
        
        # Detailed findings in expandable sections
        strengths = result.get('zt_strengths') or result.get('strengths') or []
        gaps = result.get('zt_gaps') or result.get('gaps') or []
        recommendations = result.get('zt_recommendations') or result.get('recommendations') or []
        
        if strengths or gaps or recommendations:
            st.markdown("### 📋 Detailed Findings")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if strengths:
                    with st.expander("💪 **Key Strengths**", expanded=True):
                        for strength in strengths:
                            st.markdown(f"✅ {strength}")
                            st.markdown("")
                
                if gaps:
                    with st.expander("⚠️ **Areas for Improvement**", expanded=True):
                        for gap in gaps:
                            st.markdown(f"🔸 {gap}")
                            st.markdown("")
            
            with col2:
                if recommendations:
                    with st.expander("🎯 **Priority Recommendations**", expanded=True):
                        for rec in recommendations:
                            st.markdown(f"📌 {rec}")
                            st.markdown("")
        else:
            st.markdown('<div class="warning-box">', unsafe_allow_html=True)
            st.markdown("💡 **Detailed findings are available in the downloadable report below**")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Download section with enhanced styling
        if 'report_path' in result and os.path.exists(result['report_path']):
            st.markdown("### 📥 Download Professional Report")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                with open(result['report_path'], 'rb') as f:
                    st.download_button(
                        "📄 Download Complete Assessment Report (DOCX)",
                        data=f.read(),
                        file_name=os.path.basename(result['report_path']),
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                        type="primary"
                    )
            
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown("**📋 Report Contents:**")
            st.markdown("• Executive Summary • Pillar-by-Pillar Analysis • Security Strengths & Gaps • Compliance Mapping • Actionable Recommendations")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # New Assessment Button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Start New Assessment", use_container_width=True, key="v2_new"):
                st.session_state.v2_assessment_complete = False
                st.session_state.v2_results = None
                st.rerun()

# ============================================================================
# TAB 3: KEVS DASHBOARD
# ============================================================================
with tab3:
    st.markdown("## 🛡️ KEVS Threat Intelligence Dashboard")
    st.markdown("*CISA Known Exploited Vulnerabilities (Real-time)*")
    
    @st.cache_data(ttl=3600)
    def load_kevs_data():
        tool = KEVSTool()
        vulnerabilities = asyncio.run(tool.get_vulnerabilities())
        return vulnerabilities
    
    with st.spinner("🔄 Loading CISA KEVS data..."):
        kevs_data = load_kevs_data()
    
    if kevs_data:
        st.success(f"✅ Loaded {len(kevs_data)} vulnerabilities from CISA KEVS")
        
        df = pd.DataFrame(kevs_data)
        
        # Filters
        st.markdown("### 🔍 Filter Vulnerabilities")
        col1, col2 = st.columns(2)
        with col1:
            vendor_filter = st.multiselect("🏢 Filter by Vendor", options=sorted(df['vendorProject'].unique()))
        with col2:
            product_filter = st.multiselect("📦 Filter by Product", options=sorted(df['product'].unique()))
        
        filtered_df = df.copy()
        if vendor_filter:
            filtered_df = filtered_df[filtered_df['vendorProject'].isin(vendor_filter)]
        if product_filter:
            filtered_df = filtered_df[filtered_df['product'].isin(product_filter)]
        
        st.markdown(f"### 📊 Showing {len(filtered_df)} vulnerabilities")
        
        # Data table
        st.dataframe(
            filtered_df[['cveID', 'vendorProject', 'product', 'vulnerabilityName', 'dateAdded']],
            use_container_width=True,
            hide_index=True
        )
        
        # Export button
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            "📥 Export to CSV",
            data=csv,
            file_name=f"kevs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.error("❌ Failed to load KEVS data")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>🔒 <strong>VaultZero Platform</strong> | Unified Zero Trust Assessment & Threat Intelligence</p>
    <p>VaultZero 1.0 (RAG) | VaultZero 2.0 (AI Docs) | KEVS Dashboard</p>
</div>
""", unsafe_allow_html=True)