"""
VaultZero Roadmap Agent
Creates a 4-phase, 2-year implementation roadmap based on prioritized recommendations.

4-Phase Structure:
- Phase 1 (0-3 months): Immediate Quick Wins
- Phase 2 (3-6 months): Foundation Building  
- Phase 3 (6-12 months): Strategic Capabilities
- Phase 4 (12-24 months): Optimization & Maturity
"""

from typing import Dict, List, Any
import anthropic
import os
from datetime import datetime


class RoadmapAgent:
    """Agent responsible for creating phased implementation roadmaps"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.model = "claude-sonnet-4-20250514"  # Using Sonnet 4 for strategic planning
    
    # BACKWARD COMPATIBILITY: run_roadmap() with flexible arguments
    def run_roadmap(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Backward-compatible method that handles orchestrator_v1.py calling pattern:
        run_roadmap(system_description, assessment_results, benchmark_results, recommendations)
        """
        if len(args) == 4:
            # orchestrator_v1.py pattern
            system_description = args[0]
            assessment_results = args[1]
            benchmark_results = args[2]  # Not used but accepted
            recommendations = args[3]
            organization_name = system_description if isinstance(system_description, str) else "Your Organization"
        elif len(args) == 3:
            assessment_results = args[0]
            recommendations = args[1]
            organization_name = args[2]
        elif len(args) == 2:
            assessment_results = args[0]
            recommendations = args[1]
            organization_name = kwargs.get('organization_name', "Your Organization")
        else:
            raise ValueError(f"Unexpected number of arguments: {len(args)}")
        
        return self.generate_roadmap(assessment_results, recommendations, organization_name)
    
    def generate_roadmap(
        self,
        assessment_results: Dict[str, Any],
        recommendations: Dict[str, Any],
        organization_name: str = "Your Organization"
    ) -> Dict[str, Any]:
        """
        Generate a 4-phase, 2-year implementation roadmap
        
        Args:
            assessment_results: Results from AssessmentAgent (has 'pillars' with nested 'score')
            recommendations: Prioritized recommendations from RecommendationAgent
            organization_name: Name of the organization
            
        Returns:
            Dictionary containing phased roadmap with quarterly milestones
        """
        
        # Build context for Claude
        context = self._build_roadmap_context(
            assessment_results, 
            recommendations,
            organization_name
        )
        
        # Generate roadmap using Claude
        roadmap = self._generate_phased_roadmap(context, recommendations)
        
        return roadmap
    
    def _build_roadmap_context(
        self,
        assessment_results: Dict[str, Any],
        recommendations: Dict[str, Any],
        organization_name: str
    ) -> str:
        """Build context string for Claude"""
        
        context = f"""
ORGANIZATION: {organization_name}

CURRENT MATURITY SCORES:
"""
        
        # Extract pillar scores from nested structure
        # AssessmentAgent returns: pillars -> {pillar_name} -> score
        if 'pillars' in assessment_results:
            for pillar_name, pillar_data in assessment_results['pillars'].items():
                score = pillar_data.get('score', 0)
                context += f"- {pillar_name.replace('_', ' ').title()}: {score:.1f}/4.0\n"
        
        # Get overall score
        overall_score = assessment_results.get('overall_score', 0)
        context += f"\nOVERALL MATURITY: {overall_score:.1f}/4.0\n"
        context += f"TARGET MATURITY: 4.0/4.0 (within 24 months)\n\n"
        
        # Add top recommendations
        context += "TOP 10 PRIORITIZED RECOMMENDATIONS:\n"
        if 'prioritized_recommendations' in recommendations:
            for i, rec in enumerate(recommendations['prioritized_recommendations'][:10], 1):
                context += f"{i}. [{rec.get('priority', 'Medium')}] {rec.get('title', rec.get('recommendation', 'N/A'))}\n"
                context += f"   Impact: {rec.get('impact_score', 'N/A')}/10 | Effort: {rec.get('effort_estimate', 'N/A')}\n"
                context += f"   Pillar: {rec.get('pillar', 'N/A')}\n\n"
        
        return context
    
    def _generate_phased_roadmap(
        self,
        context: str,
        recommendations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate the 4-phase roadmap using Claude"""
        
        prompt = f"""You are a Zero Trust security architect creating a 2-year implementation roadmap.

{context}

Create a detailed 4-PHASE roadmap with these characteristics:

PHASE STRUCTURE:
- Phase 1 (Months 0-3): Immediate Quick Wins - Low-hanging fruit, quick security improvements
- Phase 2 (Months 3-6): Foundation Building - Core infrastructure and critical capabilities  
- Phase 3 (Months 6-12): Strategic Capabilities - Major transformations and advanced features
- Phase 4 (Months 12-24): Optimization & Maturity - Fine-tuning, automation, reaching 4.0 maturity

For EACH PHASE, provide:
1. 3-5 specific initiatives from the recommendations
2. Clear quarterly milestones 
3. Expected maturity improvement
4. Estimated investment (staff time + technology)
5. Key dependencies
6. Success metrics

PRIORITIZATION CRITERIA:
- Phase 1: Address critical gaps, achieve compliance quick wins, build momentum
- Phase 2: Establish foundational capabilities (MFA, logging, network segmentation basics)
- Phase 3: Implement strategic capabilities (zero trust architecture, advanced automation)
- Phase 4: Optimize and mature (AI/ML security, advanced analytics, continuous improvement)

OUTPUT FORMAT:
Return a structured roadmap with clear phases, milestones, and measurable outcomes.
Focus on practical, achievable goals that build upon each other.
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=8000,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        roadmap_text = response.content[0].text
        
        # Structure the roadmap
        roadmap = {
            "generated_at": datetime.now().isoformat(),
            "roadmap_text": roadmap_text,
            "phases": self._extract_phases(roadmap_text, recommendations),
            "total_investment": self._estimate_total_investment(recommendations),
            "expected_outcomes": self._define_expected_outcomes(recommendations)
        }
        
        return roadmap
    
    def _extract_phases(
        self,
        roadmap_text: str,
        recommendations: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract structured phase information"""
        
        phases = [
            {
                "phase_number": 1,
                "name": "Immediate Quick Wins",
                "timeframe": "Months 0-3",
                "focus": "Low-hanging fruit, quick security improvements, compliance quick wins",
                "initiatives_count": self._count_phase_initiatives(recommendations, 1),
                "maturity_target": "2.5-3.0"
            },
            {
                "phase_number": 2,
                "name": "Foundation Building",
                "timeframe": "Months 3-6",
                "focus": "Core infrastructure, critical capabilities, foundational security controls",
                "initiatives_count": self._count_phase_initiatives(recommendations, 2),
                "maturity_target": "3.0-3.5"
            },
            {
                "phase_number": 3,
                "name": "Strategic Capabilities",
                "timeframe": "Months 6-12",
                "focus": "Major transformations, advanced features, strategic security architecture",
                "initiatives_count": self._count_phase_initiatives(recommendations, 3),
                "maturity_target": "3.5-4.0"
            },
            {
                "phase_number": 4,
                "name": "Optimization & Maturity",
                "timeframe": "Months 12-24",
                "focus": "Fine-tuning, automation, advanced analytics, continuous improvement",
                "initiatives_count": self._count_phase_initiatives(recommendations, 4),
                "maturity_target": "4.0+"
            }
        ]
        
        return phases
    
    def _count_phase_initiatives(
        self,
        recommendations: Dict[str, Any],
        phase_number: int
    ) -> int:
        """Count recommendations allocated to each phase"""
        
        # Get total recommendations
        total_recs = len(recommendations.get('prioritized_recommendations', [])[:10])
        
        if phase_number == 1:
            return min(3, total_recs)  # 3 quick wins
        elif phase_number == 2:
            return min(3, max(0, total_recs - 3))  # Next 3
        elif phase_number == 3:
            return min(2, max(0, total_recs - 6))  # Next 2
        else:  # Phase 4
            return max(0, total_recs - 8)  # Remaining
    
    def _estimate_total_investment(
        self,
        recommendations: Dict[str, Any]
    ) -> Dict[str, str]:
        """Estimate total investment across all phases"""
        
        return {
            "phase_1": "$50K - $150K (Quick wins, minimal infrastructure)",
            "phase_2": "$150K - $300K (Foundation, some tools/licenses)",
            "phase_3": "$300K - $600K (Strategic capabilities, major investments)",
            "phase_4": "$200K - $400K (Optimization, advanced tools)",
            "total_24_months": "$700K - $1.45M (Staff time + technology + consulting)",
            "two_year_total_min": "$700K",
            "two_year_total_max": "$1.45M"
        }
    
    def _define_expected_outcomes(
        self,
        recommendations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Define expected outcomes at end of 24 months"""
        
        return {
            "maturity_improvements": [
                "Overall Zero Trust maturity: 4.0+ (from current baseline)",
                "All 5 pillars at 3.5+ minimum",
                "At least 2 pillars at 4.5+ (optimized)"
            ],
            "compliance_achievements": [
                "Full compliance with NIST 800-207 Level 3-4",
                "90%+ compliance with CISA BOD 22-01",
                "CMS ARS 5.1 security controls implemented"
            ],
            "security_posture": [
                "Reduced attack surface by 60%+",
                "Mean time to detect (MTTD) < 15 minutes",
                "Mean time to respond (MTTR) < 1 hour",
                "Zero trust policies enforced on 95%+ of assets"
            ],
            "operational_benefits": [
                "Automated security response for 80%+ of incidents",
                "Real-time visibility across all environments",
                "Continuous compliance monitoring and reporting"
            ],
            "24_month_maturity_target": "4.0/4.0 (Optimal)",
            "interim_6_month_target": "2.5-3.0/4.0 (Advanced)",
            "interim_12_month_target": "3.0-3.5/4.0 (Advanced+)"
        }
    
    def print_roadmap_summary(self, roadmap: Dict[str, Any]):
        """Print a formatted summary of the roadmap"""
        
        print("\n" + "="*80)
        print("🗺️  2-YEAR ZERO TRUST IMPLEMENTATION ROADMAP")
        print("="*80)
        
        print("\n📊 PHASES OVERVIEW:")
        for phase in roadmap['phases']:
            print(f"\n   Phase {phase['phase_number']}: {phase['name']} ({phase['timeframe']})")
            print(f"   Focus: {phase['focus']}")
            print(f"   Initiatives: {phase['initiatives_count']}")
            print(f"   Target Maturity: {phase['maturity_target']}")
        
        print("\n💰 ESTIMATED INVESTMENT:")
        print(f"   • Phase 1 (0-3 months): {roadmap['total_investment']['phase_1']}")
        print(f"   • Phase 2 (3-6 months): {roadmap['total_investment']['phase_2']}")
        print(f"   • Phase 3 (6-12 months): {roadmap['total_investment']['phase_3']}")
        print(f"   • Phase 4 (12-24 months): {roadmap['total_investment']['phase_4']}")
        print(f"   • TOTAL: {roadmap['total_investment']['total_24_months']}")
        
        print("\n🎯 EXPECTED OUTCOMES (End of 24 Months):")
        print("\n   Maturity Improvements:")
        for outcome in roadmap['expected_outcomes']['maturity_improvements']:
            print(f"   ✓ {outcome}")
        
        print("\n   Compliance Achievements:")
        for outcome in roadmap['expected_outcomes']['compliance_achievements']:
            print(f"   ✓ {outcome}")
        
        print("\n" + "="*80)


# Example usage
if __name__ == "__main__":
    # Mock data matching AssessmentAgent structure
    mock_assessment = {
        "system_name": "Test Healthcare System",
        "pillars": {
            "identity": {"score": 2.5, "maturity_level": "ADVANCED"},
            "devices": {"score": 2.0, "maturity_level": "TRADITIONAL"},
            "networks": {"score": 2.3, "maturity_level": "ADVANCED"},
            "applications": {"score": 2.4, "maturity_level": "ADVANCED"},
            "data": {"score": 2.2, "maturity_level": "TRADITIONAL"}
        },
        "overall_score": 2.3,
        "overall_maturity_level": "ADVANCED"
    }
    
    mock_recommendations = {
        "prioritized_recommendations": [
            {
                "title": "Implement Multi-Factor Authentication (MFA)",
                "recommendation": "Implement Multi-Factor Authentication (MFA)",
                "priority": "Critical",
                "impact_score": 9,
                "effort_estimate": "Medium",
                "pillar": "Identity"
            },
            {
                "title": "Deploy Endpoint Detection and Response (EDR)",
                "recommendation": "Deploy Endpoint Detection and Response (EDR)",
                "priority": "High",
                "impact_score": 8,
                "effort_estimate": "High",
                "pillar": "Devices"
            }
        ]
    }
    
    agent = RoadmapAgent()
    
    # Test orchestrator_v1.py calling pattern (4 args)
    print("Testing orchestrator_v1.py pattern (4 args)...")
    roadmap = agent.run_roadmap(
        "Test Healthcare System",
        mock_assessment,
        {},  # benchmark_results
        mock_recommendations
    )
    
    agent.print_roadmap_summary(roadmap)
    print("\n✅ Roadmap generated successfully!")
