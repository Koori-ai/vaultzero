"""
VaultZero Orchestrator - Multi-Agent Zero Trust Assessment System
Coordinates Assessment → Benchmark → Recommendation workflow
"""

import os
import json
from typing import Dict, TypedDict, Optional
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

# Import our agents
from agents.assessment_agent import AssessmentAgent
from agents.benchmark_agent import BenchmarkAgent
from agents.recommendation_agent import RecommendationAgent

load_dotenv()

# Define state that flows between agents
class VaultZeroState(TypedDict):
    """State object that gets passed between agents"""
    system_description: str
    user_answers: Dict[str, str]
    assessment_results: Dict
    benchmark_results: Dict
    roadmap: Dict
    final_report: Dict


class VaultZeroOrchestrator:
    """Orchestrates the complete VaultZero assessment workflow"""
    
    def __init__(self, rag_system=None):
        """
        Initialize all agents and build workflow
        
        Args:
            rag_system: Optional VaultZeroRAG instance for peer benchmarking
        """
        print("🔧 Initializing VaultZero Multi-Agent System...")
        
        # Store RAG system
        self.rag_system = rag_system
        
        # Initialize agents
        self.assessment_agent = AssessmentAgent()
        self.benchmark_agent = BenchmarkAgent(rag_system=rag_system)
        self.recommendation_agent = RecommendationAgent()
        
        # Build workflow
        self.workflow = self._build_workflow()
        
        if rag_system:
            print("✅ VaultZero system ready with RAG-powered benchmarking!")
        else:
            print("⚠️  VaultZero system ready (running without RAG benchmarking)")
    
    def _build_workflow(self):
        """Build LangGraph workflow connecting all agents"""
        
        # Create state graph
        workflow = StateGraph(VaultZeroState)
        
        # Add agent nodes
        workflow.add_node("assess", self._run_assessment)
        workflow.add_node("benchmark", self._run_benchmark)
        workflow.add_node("recommend", self._run_recommendation)
        workflow.add_node("finalize", self._create_final_report)
        
        # Define flow: assess → benchmark → recommend → finalize
        workflow.set_entry_point("assess")
        workflow.add_edge("assess", "benchmark")
        workflow.add_edge("benchmark", "recommend")
        workflow.add_edge("recommend", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def _run_assessment(self, state: VaultZeroState) -> VaultZeroState:
        """Step 1: Run assessment agent"""
        print("\n" + "="*70)
        print("STEP 1/4: RUNNING ASSESSMENT AGENT")
        print("="*70)
        
        results = self.assessment_agent.run_assessment(
            state["system_description"],
            state["user_answers"]
        )
        
        state["assessment_results"] = results
        return state
    
    def _run_benchmark(self, state: VaultZeroState) -> VaultZeroState:
        """Step 2: Run benchmark agent"""
        print("\n" + "="*70)
        print("STEP 2/4: RUNNING BENCHMARK AGENT")
        if self.rag_system:
            print("📊 Using RAG-powered peer benchmarking...")
        print("="*70)
        
        results = self.benchmark_agent.run_benchmark(
            state["system_description"],
            state["assessment_results"]
        )
        
        state["benchmark_results"] = results
        return state
    
    def _run_recommendation(self, state: VaultZeroState) -> VaultZeroState:
        """Step 3: Run recommendation agent"""
        print("\n" + "="*70)
        print("STEP 3/4: RUNNING RECOMMENDATION AGENT")
        print("="*70)
        
        roadmap = self.recommendation_agent.run_recommendation(
            state["system_description"],
            state["assessment_results"],
            state["benchmark_results"]
        )
        
        state["roadmap"] = roadmap
        return state
    
    def _create_final_report(self, state: VaultZeroState) -> VaultZeroState:
        """Step 4: Create comprehensive final report"""
        print("\n" + "="*70)
        print("STEP 4/4: GENERATING FINAL REPORT")
        print("="*70)
        
        final_report = {
            "system_description": state["system_description"],
            "assessment": state["assessment_results"],
            "benchmark": state["benchmark_results"],
            "roadmap": state["roadmap"],
            "summary": {
                "current_maturity": state["assessment_results"]["overall_maturity_level"],
                "current_score": state["assessment_results"]["overall_score"],
                "peer_percentile": state["benchmark_results"]["overall_percentile"],
                "target_maturity": state["roadmap"]["expected_outcomes"]["6_month_maturity_target"],
                "investment_range": f"{state['roadmap']['total_cost_estimate']['minimum']} - {state['roadmap']['total_cost_estimate']['maximum']}"
            }
        }
        
        state["final_report"] = final_report
        
        # Display executive summary
        print("\n" + "="*70)
        print("📊 EXECUTIVE SUMMARY")
        print("="*70)
        print(f"\n🏢 System: {state['assessment_results'].get('system_name', 'N/A')}")
        print(f"📈 Current Maturity: {final_report['summary']['current_maturity']} ({final_report['summary']['current_score']:.1f}/4.0)")
        print(f"📊 Peer Ranking: {final_report['summary']['peer_percentile']}th percentile")
        print(f"🎯 6-Month Target: {final_report['summary']['target_maturity']}")
        print(f"💰 Investment: {final_report['summary']['investment_range']}")
        print("\n" + "="*70)
        
        return state
    
    def run(self, system_description: str, user_answers: Dict[str, str]) -> Dict:
        """
        Run complete VaultZero assessment workflow
        
        Args:
            system_description: Description of system to assess
            user_answers: Dictionary of pillar answers
            
        Returns:
            Complete final report
        """
        print("\n" + "="*70)
        print("🚀 STARTING VAULTZERO MULTI-AGENT ASSESSMENT")
        print("="*70)
        
        # Initialize state
        initial_state = {
            "system_description": system_description,
            "user_answers": user_answers,
            "assessment_results": {},
            "benchmark_results": {},
            "roadmap": {},
            "final_report": {}
        }
        
        # Run workflow
        final_state = self.workflow.invoke(initial_state)
        
        print("\n" + "="*70)
        print("✅ VAULTZERO ASSESSMENT COMPLETE")
        print("="*70)
        
        return final_state["final_report"]


# Test the orchestrator
if __name__ == "__main__":
    # GENERIC TEST DATA
    test_system = "Cloud-based enterprise SaaS application with customer data"
    
    test_answers = {
        "identity": "Single sign-on with MFA enforced. RBAC implemented with quarterly reviews.",
        "devices": "Corporate devices with EDR. BYOD with MDM for contractors.",
        "networks": "Cloud infrastructure with security groups. Partial network segmentation.",
        "applications": "Security testing in CI/CD. Application monitoring and logging.",
        "data": "Data classification framework exists. Encryption at rest, partial in-transit."
    }
    
    print("="*70)
    print("🧪 TESTING VAULTZERO ORCHESTRATOR")
    print("="*70)
    
    # Create orchestrator
    orchestrator = VaultZeroOrchestrator()
    
    # Run complete workflow
    final_report = orchestrator.run(test_system, test_answers)
    
    # Save complete report
    output_file = "vaultzero_complete_report.json"
    with open(output_file, "w") as f:
        json.dump(final_report, f, indent=2)
    
    print(f"\n✅ Complete report saved to {output_file}")
    print("\n🎉 VaultZero Multi-Agent System is fully operational!")