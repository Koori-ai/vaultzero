"""
VaultZero - AI-Powered Zero Trust Assessment Platform
Streamlit Web Interface
"""

import streamlit as st
import json
from datetime import datetime
from orchestrator import VaultZeroOrchestrator
import anthropic

# Page config
st.set_page_config(
    page_title="VaultZero - Zero Trust Assessment",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
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
    
    /* AI Assistant Button Styling */
    div[data-testid="stButton"] button[key="open_chat_fab"] {
        background: linear-gradient(135deg, #FF6B35 0%, #1f77b4 100%) !important;
        font-size: 1.5rem !important;
        padding: 1rem 2rem !important;
        border-radius: 50px !important;
        box-shadow: 0 8px 24px rgba(31, 119, 180, 0.4) !important;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% {
            box-shadow: 0 8px 24px rgba(31, 119, 180, 0.4);
        }
        50% {
            box-shadow: 0 8px 36px rgba(31, 119, 180, 0.7);
        }
    }
    </style>
""", unsafe_allow_html=True)


def get_chat_response(user_message: str) -> str:
    """Get response from Claude API with context awareness"""
    
    # Build context from session state
    context_parts = []
    
    # Add assessment results if available
    if st.session_state.get('assessment_complete') and st.session_state.get('results'):
        results = st.session_state.results
        
        if 'summary' in results:
            summary = results['summary']
            context_parts.append(
                f"User's Assessment Results:\n"
                f"- Overall Score: {summary.get('current_score', 'N/A')}/4.0\n"
                f"- Maturity Level: {summary.get('current_maturity', 'N/A')}\n"
                f"- Percentile: {summary.get('peer_percentile', 'N/A')}th\n"
                f"- Target: {summary.get('target_maturity', 'N/A')}"
            )
        
        if 'assessment' in results and 'pillars' in results['assessment']:
            pillar_scores = []
            for pillar_name, pillar_data in results['assessment']['pillars'].items():
                pillar_scores.append(
                    f"  - {pillar_name.title()}: {pillar_data['score']}/4.0 ({pillar_data['maturity_level']})"
                )
            if pillar_scores:
                context_parts.append("Pillar Scores:\n" + "\n".join(pillar_scores))
    
    # Build system prompt
    system_prompt = """You are a Zero Trust security expert assistant integrated into VaultZero, 
an AI-powered Zero Trust maturity assessment platform.

Your role is to:
- Answer questions about Zero Trust architecture and principles
- Help users understand their assessment results
- Provide guidance on improving Zero Trust maturity
- Explain scoring and recommendations
- Give examples of good security practices

The Zero Trust maturity scale is:
- 1.0 - Initial: Ad-hoc security processes
- 2.0 - Traditional: Basic perimeter security
- 3.0 - Advanced: Mature Zero Trust implementation
- 4.0 - Optimal: Industry-leading Zero Trust

The six pillars are: Identity, Devices, Networks, Applications, Data, Visibility & Analytics.

Be concise, helpful, and specific. Use the user's assessment context when available.
Keep responses under 250 words unless asked for more detail.
"""
    
    if context_parts:
        system_prompt += f"\n\nCurrent User Context:\n" + "\n\n".join(context_parts)
    
    # Build messages for API
    messages = []
    
    # Add recent chat history (last 6 messages for context)
    if 'chat_messages' in st.session_state:
        recent_messages = st.session_state.chat_messages[-6:] if len(st.session_state.chat_messages) > 6 else st.session_state.chat_messages
        for msg in recent_messages:
            if msg['role'] != 'system':
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
    
    # Add current message
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    try:
        # Call Claude API
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=messages
        )
        
        return response.content[0].text
        
    except Exception as e:
        return f"I apologize, but I encountered an error: {str(e)}\n\nPlease try again or rephrase your question."


# Initialize session state
if 'assessment_complete' not in st.session_state:
    st.session_state.assessment_complete = False
if 'results' not in st.session_state:
    st.session_state.results = None
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'chat_open' not in st.session_state:
    st.session_state.chat_open = False

# Header
st.markdown('<div class="main-header">🔒 VaultZero</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Zero Trust Maturity Assessment</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/300x100/1f77b4/ffffff?text=VaultZero", use_container_width=True)
    
    st.markdown("### 🎯 How It Works")
    st.markdown("""
    1. **Describe** your system
    2. **Answer** questions for each pillar
    3. **Get** instant AI assessment
    4. **Compare** against peers (RAG-powered)
    5. **Receive** 6-month roadmap
    """)
    
    st.markdown("---")
    st.markdown("### 📊 About")
    st.markdown("""
    VaultZero uses a **multi-agent AI system** to:
    - Assess Zero Trust maturity
    - Benchmark against similar systems
    - Generate actionable roadmaps
    
    **Powered by:**
    - Claude Sonnet 4
    - LangGraph
    - RAG (21 assessments)
    """)
    
    st.markdown("---")
    st.markdown("### 🌟 Features")
    st.markdown("""
    ✅ Real-time assessment  
    ✅ Peer benchmarking  
    ✅ Cost estimates  
    ✅ Downloadable reports  
    ✅ 100% secure & private  
    """)

# Chat Dialog
@st.dialog("💬 AI Assistant", width="large")
def show_chat_dialog():
    st.markdown("### Ask me about Zero Trust!")
    
    # Suggested questions based on context
    if st.session_state.assessment_complete and st.session_state.results:
        suggestions = [
            ("💡", "Why did I get this score?"),
            ("🎯", "What are my quick wins?"),
            ("📊", "How do I compare to others?"),
            ("🔍", "Explain my recommendations"),
        ]
    else:
        suggestions = [
            ("❓", "What is Zero Trust?"),
            ("📝", "How should I score identity?"),
            ("💡", "Give me examples for networks"),
            ("🎯", "What's a good maturity score?"),
        ]
    
    st.markdown("**Quick questions:**")
    cols = st.columns(2)
    for idx, (emoji, question) in enumerate(suggestions):
        with cols[idx % 2]:
            if st.button(f"{emoji} {question}", key=f"q_{idx}", use_container_width=True):
                st.session_state.chat_messages.append({"role": "user", "content": question})
                with st.spinner("🤔 Thinking..."):
                    response = get_chat_response(question)
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
                st.rerun()
    
    st.markdown("---")
    
    # Chat history
    if st.session_state.chat_messages:
        chat_container = st.container(height=400)
        with chat_container:
            for message in st.session_state.chat_messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
    else:
        st.info("👋 Hi! I'm your Zero Trust AI assistant. Ask me anything!")
    
    # Chat input
    if prompt := st.chat_input("Type your question here...", key="chat_input_dialog"):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.spinner("🤔 Thinking..."):
            response = get_chat_response(prompt)
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
        st.rerun()
    
    # Clear button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()

# Main content
if not st.session_state.assessment_complete:
    # Input form
    st.markdown("## 📝 System Information")
    
    with st.form("assessment_form"):
        # System description
        system_description = st.text_area(
            "**System Description**",
            placeholder="e.g., Cloud-based healthcare platform handling patient records, hosted on AWS with microservices architecture...",
            height=100,
            help="Provide a brief description of the system you want to assess"
        )
        
        st.markdown("---")
        st.markdown("## 🔐 Zero Trust Pillar Assessment")
        st.markdown("*Answer the questions below for each pillar:*")
        
        # Create two columns for better layout
        col1, col2 = st.columns(2)
        
        with col1:
            # Identity
            st.markdown("### 🔑 Identity")
            identity_answer = st.text_area(
                "Describe your identity and access management practices",
                placeholder="e.g., We use Okta SSO with MFA enforced. RBAC implemented with quarterly reviews...",
                height=120,
                key="identity"
            )
            
            # Devices
            st.markdown("### 💻 Devices")
            devices_answer = st.text_area(
                "Describe your device security and management",
                placeholder="e.g., Corporate laptops managed with Intune. EDR deployed on all endpoints...",
                height=120,
                key="devices"
            )
            
            # Networks
            st.markdown("### 🌐 Networks")
            networks_answer = st.text_area(
                "Describe your network security architecture",
                placeholder="e.g., Zero-trust network access via Zscaler. Micro-segmentation in cloud...",
                height=120,
                key="networks"
            )
        
        with col2:
            # Applications
            st.markdown("### 📱 Applications")
            applications_answer = st.text_area(
                "Describe your application security practices",
                placeholder="e.g., Security testing in CI/CD. Runtime protection with RASP...",
                height=120,
                key="applications"
            )
            
            # Data
            st.markdown("### 🗄️ Data")
            data_answer = st.text_area(
                "Describe your data protection and governance",
                placeholder="e.g., Data classification enforced. DLP policies active. Encryption at rest and in transit...",
                height=120,
                key="data"
            )
        
        st.markdown("---")
        
        # Submit button
        submitted = st.form_submit_button("🚀 Run VaultZero Assessment", use_container_width=True)
        
        if submitted:
            # Validation
            if not system_description or not all([identity_answer, devices_answer, networks_answer, applications_answer, data_answer]):
                st.error("⚠️ Please fill in all fields before submitting!")
            else:
                # Prepare answers
                user_answers = {
                    "identity": identity_answer,
                    "devices": devices_answer,
                    "networks": networks_answer,
                    "applications": applications_answer,
                    "data": data_answer
                }
                
                # Run assessment
                with st.spinner("🤖 Running multi-agent assessment... This may take 60-90 seconds..."):
                    try:
                        # Initialize orchestrator
                        orchestrator = VaultZeroOrchestrator()
                        
                        # Run complete workflow
                        results = orchestrator.run(system_description, user_answers)
                        
                        # Save to session state
                        st.session_state.results = results
                        st.session_state.assessment_complete = True
                        
                        # Rerun to show results
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error running assessment: {str(e)}")
                        st.exception(e)

else:
    # Display results
    results = st.session_state.results
    
    st.markdown('<div class="success-box">', unsafe_allow_html=True)
    st.markdown("### ✅ Assessment Complete!")
    st.markdown("Your comprehensive Zero Trust assessment is ready.")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Executive Summary
    st.markdown("## 📊 Executive Summary")
    
    summary = results['summary']
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="Current Maturity",
            value=summary['current_maturity'],
            delta=None
        )
    
    with col2:
        st.metric(
            label="Current Score",
            value=f"{summary['current_score']:.1f}/4.0",
            delta=None
        )
    
    with col3:
        st.metric(
            label="Peer Percentile",
            value=f"{summary['peer_percentile']}th",
            delta=None
        )
    
    with col4:
        st.metric(
            label="6-Month Target",
            value=summary['target_maturity'],
            delta=None
        )
    
    with col5:
        st.metric(
            label="Investment",
            value=summary['investment_range'].split(' - ')[0],
            delta=summary['investment_range'].split(' - ')[1]
        )
    
    # Tabs for detailed results
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Assessment", "📊 Benchmark", "🗺️ Roadmap", "📥 Download"])
    
    with tab1:
        st.markdown("### 🔐 Pillar Assessment Results")
        
        assessment = results['assessment']
        
        for pillar_name, pillar_data in assessment['pillars'].items():
            with st.expander(f"**{pillar_name.upper()}** - {pillar_data['maturity_level']} ({pillar_data['score']:.1f}/4.0)", expanded=False):
                st.markdown(f"**Findings:** {pillar_data['findings']}")
                
                if pillar_data.get('strengths'):
                    st.markdown("**✅ Strengths:**")
                    for strength in pillar_data['strengths']:
                        st.markdown(f"- {strength}")
                
                if pillar_data.get('gaps'):
                    st.markdown("**⚠️ Gaps:**")
                    for gap in pillar_data['gaps']:
                        st.markdown(f"- {gap}")
        
        st.markdown("### 🎯 Key Findings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**⚡ Quick Wins**")
            for win in assessment['quick_wins']:
                st.markdown(f"- {win}")
        
        with col2:
            st.markdown("**🚀 Strategic Recommendations**")
            for rec in assessment['strategic_recommendations']:
                st.markdown(f"- {rec}")
    
    with tab2:
        st.markdown("### 📊 Benchmark Analysis")
        
        benchmark = results['benchmark']
        
        st.markdown(f"**Competitive Position:** {benchmark['competitive_position']}")
        
        st.markdown("#### Pillar Rankings vs Peers")
        
        for pillar, data in benchmark['pillar_rankings'].items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{pillar.title()}**")
            with col2:
                st.markdown(f"{data['percentile']}th percentile ({data['vs_peers']})")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**💪 Strengths vs Peers**")
            for strength in benchmark['strengths_vs_peers']:
                st.markdown(f"- {strength}")
        
        with col2:
            st.markdown("**⚠️ Gaps vs Peers**")
            for gap in benchmark['gaps_vs_peers']:
                st.markdown(f"- {gap}")
        
        st.markdown("#### 🌟 Peer Best Practices")
        for practice in benchmark['peer_best_practices']:
            st.markdown(f"**{practice['practice']}**")
            st.markdown(f"- From: {practice['system']}")
            st.markdown(f"- How: {practice['implementation']}")
            st.markdown("")
    
    with tab3:
        st.markdown("### 🗺️ 6-Month Implementation Roadmap")
        
        roadmap = results['roadmap']
        
        st.markdown(f"**Executive Summary:** {roadmap['executive_summary']}")
        st.markdown(f"**Total Investment:** {roadmap['total_cost_estimate']['minimum']} - {roadmap['total_cost_estimate']['maximum']}")
        
        st.markdown("#### ⚡ Quick Wins (Months 1-2)")
        for qw in roadmap['quick_wins']:
            with st.expander(f"**{qw['initiative']}** - {qw['effort']} effort, {qw['impact']} impact"):
                st.markdown(f"**Timeline:** {qw['timeline']}")
                st.markdown(f"**Cost:** {qw['cost_estimate']}")
                st.markdown(f"**Why Now:** {qw['why_now']}")
                st.markdown("**Success Metrics:**")
                for metric in qw['success_metrics']:
                    st.markdown(f"- {metric}")
        
        st.markdown("#### 🎯 Medium-Term Initiatives (Months 3-4)")
        for mt in roadmap['medium_term']:
            with st.expander(f"**{mt['initiative']}** - {mt['effort']} effort, {mt['impact']} impact"):
                st.markdown(f"**Timeline:** {mt['timeline']}")
                st.markdown(f"**Cost:** {mt['cost_estimate']}")
                if 'dependencies' in mt:
                    st.markdown(f"**Dependencies:** {', '.join(mt['dependencies'])}")
                st.markdown("**Success Metrics:**")
                for metric in mt['success_metrics']:
                    st.markdown(f"- {metric}")
        
        st.markdown("#### 🚀 Transformational Initiatives (Months 5-6)")
        for lt in roadmap['long_term']:
            with st.expander(f"**{lt['initiative']}** - {lt['effort']} effort, {lt['impact']} impact"):
                st.markdown(f"**Timeline:** {lt['timeline']}")
                st.markdown(f"**Cost:** {lt['cost_estimate']}")
                if 'dependencies' in lt:
                    st.markdown(f"**Dependencies:** {', '.join(lt['dependencies'])}")
                st.markdown("**Success Metrics:**")
                for metric in lt['success_metrics']:
                    st.markdown(f"- {metric}")
        
        st.markdown("#### 📅 Month-by-Month Plan")
        for month_key, month_data in roadmap['month_by_month'].items():
            month_num = month_key.split('_')[1]
            with st.expander(f"**Month {month_num}:** {month_data['focus']}"):
                st.markdown("**Initiatives:**")
                for init in month_data['initiatives']:
                    st.markdown(f"- {init}")
                st.markdown("**Milestones:**")
                for milestone in month_data['milestones']:
                    st.markdown(f"- ✓ {milestone}")
    
    with tab4:
        st.markdown("### 📥 Download Report")
        
        st.markdown("Download your complete VaultZero assessment report in JSON format.")
        
        # Prepare download
        report_json = json.dumps(results, indent=2)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vaultzero_report_{timestamp}.json"
        
        st.download_button(
            label="📥 Download Complete Report (JSON)",
            data=report_json,
            file_name=filename,
            mime="application/json",
            use_container_width=True
        )
        
        st.markdown("---")
        st.markdown("**Report includes:**")
        st.markdown("- Complete assessment results")
        st.markdown("- Benchmark analysis")
        st.markdown("- 6-month implementation roadmap")
        st.markdown("- Cost estimates and timelines")
    
    # Reset button
    if st.button("🔄 Start New Assessment", use_container_width=True):
        st.session_state.assessment_complete = False
        st.session_state.results = None
        st.rerun()

# Footer with AI Assistant Button
st.markdown("---")

# AI Assistant button - centered at bottom
col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    if st.button("💬 Ask AI Assistant", key="open_chat_fab", use_container_width=True, type="primary"):
        show_chat_dialog()

st.markdown("""
<div style='text-align: center; color: #666; margin-top: 1rem;'>
    <p>🔒 <strong>VaultZero</strong> | AI-Powered Zero Trust Assessment Platform</p>
    <p>Built with Claude Sonnet 4, LangGraph, and RAG | <a href="https://huggingface.co/datasets/Reply2susi/zero-trust-maturity-assessments" target="_blank">Dataset on Hugging Face</a></p>
</div>
""", unsafe_allow_html=True)