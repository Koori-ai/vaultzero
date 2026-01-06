"""
VaultZero Agent Orchestrator
LangGraph-based multi-agent workflow orchestration
Google Enterprise Agent Architecture pattern
"""

from typing import Dict, Any, TypedDict, Annotated
import operator
from datetime import datetime

from langgraph.graph import StateGraph, END
from agents import (
    DocumentAgent,
    ZeroTrustAnalyzerAgent,
    ComplianceAgent,
    ReportWriterAgent
)


class AgentState(TypedDict):
    """
    Shared state across all agents.
    
    LangGraph will manage this state and pass it between agents.
    """
    # Input
    uploaded_files: list
    assessment_mode: str  # 'ai', 'manual', 'hybrid'
    
    # Document Agent outputs
    documents_analyzed: int
    document_summaries: Dict[str, Any]
    extracted_technologies: list
    extracted_controls: list
    extracted_policies: list
    extraction_status: str
    
    # ZT Analyzer outputs
    zt_scores: Dict[str, float]
    zt_gaps: list
    zt_strengths: list
    zt_recommendations: list
    overall_maturity_score: float
    overall_maturity_level: str
    analysis_complete: bool
    
    # Compliance Agent outputs
    compliance_matrix: Dict[str, Any]
    compliance_gaps: list
    compliance_met: list
    compliance_percentage: float
    compliance_status: str
    compliance_mapping_complete: bool
    
    # Report Writer outputs
    report_path: str
    report_filename: str
    executive_summary: str
    report_generated: bool
    
    # Metadata
    workflow_started: str
    workflow_status: str
    current_step: str
    errors: Annotated[list, operator.add]
    last_updated: str
    last_agent: str


class VaultZeroOrchestrator:
    """
    Orchestrates multi-agent Zero Trust assessment workflow.
    
    Agent Flow:
    1. Document Agent: Parse and extract
    2. ZT Analyzer: Evaluate maturity
    3. Compliance Agent: Map to frameworks
    4. Report Writer: Generate DOCX
    """
    
    def __init__(self, api_key: str = None):
        """Initialize orchestrator and agents."""
        self.api_key = api_key
        
        # Initialize agents
        self.document_agent = DocumentAgent(api_key=api_key)
        self.zt_analyzer = ZeroTrustAnalyzerAgent(api_key=api_key)
        self.compliance_agent = ComplianceAgent(api_key=api_key)
        self.report_writer = ReportWriterAgent(api_key=api_key)
        
        # Build workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """
        Build LangGraph workflow.
        
        Graph structure:
        START -> Document Agent -> ZT Analyzer -> Compliance -> Report Writer -> END
        """
        
        # Create graph
        workflow = StateGraph(AgentState)
        
        # Add agent nodes
        workflow.add_node("document_analysis", self._document_node)
        workflow.add_node("zt_analysis", self._zt_node)
        workflow.add_node("compliance_mapping", self._compliance_node)
        workflow.add_node("report_generation", self._report_node)
        
        # Define edges (agent flow)
        workflow.set_entry_point("document_analysis")
        workflow.add_edge("document_analysis", "zt_analysis")
        workflow.add_edge("zt_analysis", "compliance_mapping")
        workflow.add_edge("compliance_mapping", "report_generation")
        workflow.add_edge("report_generation", END)
        
        return workflow.compile()
    
    async def _document_node(self, state: AgentState) -> AgentState:
        """Document Agent node."""
        try:
            state['current_step'] = 'Document Analysis'
            result = await self.document_agent.process(state)
            return result
        except Exception as e:
            state['errors'].append(f"Document Agent error: {str(e)}")
            raise
    
    async def _zt_node(self, state: AgentState) -> AgentState:
        """Zero Trust Analyzer node."""
        try:
            state['current_step'] = 'Zero Trust Analysis'
            result = await self.zt_analyzer.process(state)
            return result
        except Exception as e:
            state['errors'].append(f"ZT Analyzer error: {str(e)}")
            raise
    
    async def _compliance_node(self, state: AgentState) -> AgentState:
        """Compliance Mapping node."""
        try:
            state['current_step'] = 'Compliance Mapping'
            result = await self.compliance_agent.process(state)
            return result
        except Exception as e:
            state['errors'].append(f"Compliance Agent error: {str(e)}")
            raise
    
    async def _report_node(self, state: AgentState) -> AgentState:
        """Report Writer node."""
        try:
            state['current_step'] = 'Report Generation'
            result = await self.report_writer.process(state)
            result['workflow_status'] = 'complete'
            return result
        except Exception as e:
            state['errors'].append(f"Report Writer error: {str(e)}")
            raise
    
    async def run_assessment(
        self,
        uploaded_files: list,
        mode: str = 'ai'
    ) -> Dict[str, Any]:
        """
        Run complete assessment workflow.
        
        Args:
            uploaded_files: List of file paths to analyze
            mode: Assessment mode ('ai', 'manual', 'hybrid')
            
        Returns:
            Final state with all results
        """
        
        # Initialize state
        initial_state = {
            'uploaded_files': uploaded_files,
            'assessment_mode': mode,
            'workflow_started': datetime.now().isoformat(),
            'workflow_status': 'running',
            'current_step': 'Starting',
            'errors': [],
            'documents_analyzed': 0,
            'document_summaries': {},
            'extracted_technologies': [],
            'extracted_controls': [],
            'extracted_policies': [],
            'extraction_status': 'pending',
            'zt_scores': {},
            'zt_gaps': [],
            'zt_strengths': [],
            'zt_recommendations': [],
            'overall_maturity_score': 0.0,
            'overall_maturity_level': 'Unknown',
            'analysis_complete': False,
            'compliance_matrix': {},
            'compliance_gaps': [],
            'compliance_met': [],
            'compliance_percentage': 0.0,
            'compliance_status': 'Unknown',
            'compliance_mapping_complete': False,
            'report_path': '',
            'report_filename': '',
            'executive_summary': '',
            'report_generated': False,
            'last_updated': datetime.now().isoformat(),
            'last_agent': 'orchestrator'
        }
        
        print(f"🚀 Starting VaultZero Assessment")
        print(f"📁 Files to analyze: {len(uploaded_files)}")
        print(f"🤖 Mode: {mode}")
        print()
        
        # Run workflow
        try:
            final_state = await self.workflow.ainvoke(initial_state)
            
            print(f"✅ Assessment Complete!")
            print(f"📊 Maturity: {final_state['overall_maturity_level']} "
                  f"({final_state['overall_maturity_score']}/5.0)")
            print(f"📋 Compliance: {final_state['compliance_percentage']}%")
            print(f"📄 Report: {final_state['report_filename']}")
            
            return final_state
            
        except Exception as e:
            print(f"❌ Workflow failed: {str(e)}")
            raise
    
    def get_workflow_status(self, state: AgentState) -> Dict[str, Any]:
        """Get current workflow status."""
        return {
            'current_step': state.get('current_step', 'Unknown'),
            'status': state.get('workflow_status', 'Unknown'),
            'progress': self._calculate_progress(state),
            'errors': state.get('errors', [])
        }
    
    def _calculate_progress(self, state: AgentState) -> int:
        """Calculate workflow progress percentage."""
        steps_completed = 0
        
        if state.get('extraction_status') == 'complete':
            steps_completed += 1
        if state.get('analysis_complete'):
            steps_completed += 1
        if state.get('compliance_mapping_complete'):
            steps_completed += 1
        if state.get('report_generated'):
            steps_completed += 1
        
        return int((steps_completed / 4) * 100)


# Simple test function
async def test_orchestrator():
    """Test the orchestrator with sample files."""
    
    import os
    
    orchestrator = VaultZeroOrchestrator()
    
    # Sample files (you'll need to provide real paths)
    sample_files = [
        "/path/to/network_diagram.pdf",
        "/path/to/security_policy.docx"
    ]
    
    result = await orchestrator.run_assessment(sample_files)
    
    print("\n=== Assessment Results ===")
    print(f"Maturity: {result['overall_maturity_level']}")
    print(f"Score: {result['overall_maturity_score']}/5.0")
    print(f"Compliance: {result['compliance_percentage']}%")
    print(f"Report: {result['report_path']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_orchestrator())
