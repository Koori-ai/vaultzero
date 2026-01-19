"""
VaultZero Orchestrator V1 - 5-Agent Zero Trust Assessment System
Coordinates: Assessment → Benchmark → Recommendation → Roadmap → Report Generation
"""

import os
import json
from typing import Dict, TypedDict, Optional
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

# Import all 5 agents
from agents.assessment_agent import AssessmentAgent
from agents.benchmark_agent import BenchmarkAgent
from agents.recommendation_agent import RecommendationAgent
from agents.roadmap_agent import RoadmapAgent
from agents.report_generator_agent import ReportGeneratorAgent

load_dotenv()

# Define state that flows between agents
class VaultZeroState(TypedDict):
    """State object that gets passed between agents"""
    system_description: str
    user_answers: Dict[str, str]
    assessment_results: Dict
    benchmark_results: Dict
    recommendations: Dict
    roadmap: Dict
    report_filename: str
    final_report: Dict


class VaultZeroOrchestrator:
    """Orchestrates the complete VaultZero 5-agent assessment workflow"""
    
    def __init__(self, rag_system=None):
        """
        Initialize all 5 agents and build workflow
        
        Args:
            rag_system: Optional VaultZeroRAG instance for peer benchmarking
        """
        print("🔧 Initializing VaultZero 5-Agent System...")
        
        # Store RAG system
        self.rag_system = rag_system
        
        # Initialize all 5 agents
        self.assessment_agent = AssessmentAgent()
        self.benchmark_agent = BenchmarkAgent(rag_system=rag_system)
        self.recommendation_agent = RecommendationAgent()
        self.roadmap_agent = RoadmapAgent()
        self.report_generator_agent = ReportGeneratorAgent()
        
        # Build workflow
        self.workflow = self._build_workflow()
        
        if rag_system:
            print("✅ VaultZero 5-agent system ready with RAG-powered benchmarking!")
        else:
            print("⚠️  VaultZero 5-agent system ready (running without RAG benchmarking)")
    
    def _build_workflow(self):
        """Build LangGraph workflow connecting all 5 agents"""
        
        # Create state graph
        workflow = StateGraph(VaultZeroState)
        
        # Add all 5 agent nodes
        workflow.add_node("assess", self._run_assessment)
        workflow.add_node("benchmark", self._run_benchmark)
        workflow.add_node("recommend", self._run_recommendation)
        workflow.add_node("roadmap", self._run_roadmap)
        workflow.add_node("report", self._run_report_generation)
        workflow.add_node("finalize", self._create_final_report)
        
        # Define flow: assess → benchmark → recommend → roadmap → report → finalize
        workflow.set_entry_point("assess")
        workflow.add_edge("assess", "benchmark")
        workflow.add_edge("benchmark", "recommend")
        workflow.add_edge("recommend", "roadmap")
        workflow.add_edge("roadmap", "report")
        workflow.add_edge("report", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def _run_assessment(self, state: VaultZeroState) -> VaultZeroState:
        """Step 1/5: Run assessment agent"""
        print("\n" + "="*70)
        print("STEP 1/5: ASSESSMENT AGENT")
        print("="*70)
        
        results = self.assessment_agent.run_assessment(
            state["system_description"],
            state["user_answers"]
        )
        
        state["assessment_results"] = results
        return state
    
    def _run_benchmark(self, state: VaultZeroState) -> VaultZeroState:
        """Step 2/5: Run benchmark agent"""
        print("\n" + "="*70)
        print("STEP 2/5: BENCHMARK AGENT")
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
        """Step 3/5: Run recommendation agent"""
        print("\n" + "="*70)
        print("STEP 3/5: RECOMMENDATION AGENT")
        print("="*70)
        
        recommendations = self.recommendation_agent.run_recommendation(
            state["system_description"],
            state["assessment_results"],
            state["benchmark_results"]
        )
        
        state["recommendations"] = recommendations
        return state
    
    def _run_roadmap(self, state: VaultZeroState) -> VaultZeroState:
        """Step 4/5: Run roadmap agent"""
        print("\n" + "="*70)
        print("STEP 4/5: ROADMAP AGENT (2-YEAR PLAN)")
        print("="*70)
        
        roadmap = self.roadmap_agent.run_roadmap(
            state["system_description"],
            state["assessment_results"],
            state["benchmark_results"],
            state["recommendations"]
        )
        
        state["roadmap"] = roadmap
        return state
    
    def _run_report_generation(self, state: VaultZeroState) -> VaultZeroState:
        """Step 5/5: Run report generator agent"""
        print("\n" + "="*70)
        print("STEP 5/5: REPORT GENERATOR AGENT")
        print("="*70)
        
        report_filename = self.report_generator_agent.run_report_generation(
            state["system_description"],
            state["assessment_results"],
            state["benchmark_results"],
            state["recommendations"],
            state["roadmap"]
        )
        
        state["report_filename"] = report_filename
        return state
    
    def _create_final_report(self, state: VaultZeroState) -> VaultZeroState:
        """Step 6/5: Create comprehensive final report"""
        print("\n" + "="*70)
        print("FINALIZING COMPLETE ASSESSMENT")
        print("="*70)
        
        final_report = {
            "system_description": state["system_description"],
            "assessment": state["assessment_results"],
            "benchmark": state["benchmark_results"],
            "recommendations": state["recommendations"],
            "roadmap": state["roadmap"],
            "report_filename": state["report_filename"],
            "summary": {
                "current_maturity": state["assessment_results"]["overall_maturity_level"],
                "current_score": state["assessment_results"]["overall_score"],
                "peer_percentile": state["benchmark_results"]["overall_percentile"],
                "target_maturity_24_months": state["roadmap"]["expected_outcomes"]["24_month_maturity_target"],
                "target_maturity_6_months": state["roadmap"]["expected_outcomes"]["interim_6_month_target"],
                "target_maturity_12_months": state["roadmap"]["expected_outcomes"]["interim_12_month_target"],
                "investment_range": f"{state['roadmap']['total_investment']['two_year_total_min']} - {state['roadmap']['total_investment']['two_year_total_max']}",
                "top_recommendations": [rec['recommendation'] for rec in state["recommendations"]["prioritized_recommendations"][:5]]
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
        print(f"\n🎯 Maturity Targets:")
        print(f"   • 6 months: {final_report['summary']['target_maturity_6_months']}")
        print(f"   • 12 months: {final_report['summary']['target_maturity_12_months']}")
        print(f"   • 24 months: {final_report['summary']['target_maturity_24_months']}")
        print(f"\n💰 Total Investment (24 months): {final_report['summary']['investment_range']}")
        print(f"\n📄 Professional Report: {state['report_filename']}")
        print("\n" + "="*70)
        
        return state
    
    def run(self, system_description: str, user_answers: Dict[str, str]) -> Dict:
        """
        Run complete VaultZero 5-agent assessment workflow
        
        Args:
            system_description: Description of system to assess
            user_answers: Dictionary of pillar answers
            
        Returns:
            Complete final report with DOCX filename
        """
        print("\n" + "="*70)
        print("🚀 STARTING VAULTZERO 5-AGENT ASSESSMENT")
        print("="*70)
        print("Agents: Assessment → Benchmark → Recommendation → Roadmap → Report")
        print("="*70)
        
        # Initialize state
        initial_state = {
            "system_description": system_description,
            "user_answers": user_answers,
            "assessment_results": {},
            "benchmark_results": {},
            "recommendations": {},
            "roadmap": {},
            "report_filename": "",
            "final_report": {}
        }
        
        # Run workflow
        final_state = self.workflow.invoke(initial_state)
        
        print("\n" + "="*70)
        print("✅ VAULTZERO 5-AGENT ASSESSMENT COMPLETE")
        print("="*70)
        print(f"\n📄 Download your professional report: {final_state['report_filename']}")
        print("\n" + "="*70)
        
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
    print("🧪 TESTING VAULTZERO 5-AGENT ORCHESTRATOR")
    print("="*70)
    
    # Create orchestrator
    orchestrator = VaultZeroOrchestrator()
    
    # Run complete workflow
    final_report = orchestrator.run(test_system, test_answers)
    
    # Save complete report (JSON backup)
    output_file = "vaultzero_complete_report.json"
    with open(output_file, "w") as f:
        json.dump(final_report, f, indent=2)
    
    print(f"\n✅ JSON backup saved to {output_file}")
    print(f"✅ Professional DOCX report: {final_report['report_filename']}")
    print("\n🎉 VaultZero 5-Agent System is fully operational!")
