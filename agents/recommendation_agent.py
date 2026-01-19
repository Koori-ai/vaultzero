"""
Recommendation Agent - Identifies gaps and prioritizes improvements
Now focused ONLY on recommendations - roadmap is separate agent
UPDATED: Added risk_level and impact_if_not_fixed for report compatibility
"""

import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RecommendationAgent:
    def __init__(self):
        """Initialize the Recommendation Agent with Claude API"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
    
    def generate_recommendations(self, 
                                system_description: str,
                                assessment_results: dict,
                                benchmark_results: dict):
        """Generate prioritized recommendations based on gaps and benchmark position"""
        
        prompt = f"""You are a Zero Trust security expert. Analyze the assessment and benchmark results to identify gaps and prioritize improvements.

SYSTEM CONTEXT:
{system_description}

CURRENT STATE (Assessment):
{json.dumps(assessment_results, indent=2)}

BENCHMARK POSITION:
{json.dumps(benchmark_results, indent=2)}

Generate comprehensive recommendations in JSON format:

{{
    "critical_gaps": [
        {{
            "pillar": "Which pillar",
            "gap": "Specific gap identified",
            "current_state": "What exists now",
            "desired_state": "What should exist",
            "business_impact": "Why this matters",
            "impact_if_not_fixed": "Concrete consequences if left unaddressed",
            "priority": "Critical/High/Medium/Low",
            "risk_level": "Critical/High/Medium/Low",
            "effort_estimate": "Low/Medium/High"
        }}
    ],
    "strengths_to_maintain": [
        {{
            "pillar": "Which pillar",
            "strength": "What's working well",
            "why_important": "Why to keep this"
        }}
    ],
    "prioritized_recommendations": [
        {{
            "rank": 1,
            "priority": "Critical/High/Medium/Low",
            "recommendation": "Specific actionable recommendation",
            "title": "Short title for the recommendation",
            "pillar": "Which pillar",
            "rationale": "Why this is priority",
            "expected_impact": "What will improve",
            "quick_win": true/false,
            "effort_estimate": "Low/Medium/High",
            "impact_score": 1-10,
            "cost_estimate": "$XX,000 - $XX,000 or Low/Medium/High",
            "success_criteria": ["Measurable outcome 1", "Measurable outcome 2"]
        }}
    ],
    "pillar_priorities": {{
        "identity": {{
            "priority_level": "Critical/High/Medium/Low",
            "key_improvements": ["Improvement 1", "Improvement 2"],
            "rationale": "Why this pillar needs focus"
        }},
        "devices": {{"priority_level": "...", "key_improvements": [], "rationale": "..."}},
        "networks": {{"priority_level": "...", "key_improvements": [], "rationale": "..."}},
        "applications": {{"priority_level": "...", "key_improvements": [], "rationale": "..."}},
        "data": {{"priority_level": "...", "key_improvements": [], "rationale": "..."}}
    }},
    "investment_priorities": {{
        "high_roi_quick_wins": ["Initiative 1", "Initiative 2"],
        "strategic_investments": ["Major investment 1", "Major investment 2"],
        "cost_optimization_opportunities": ["Cost saving 1", "Cost saving 2"]
    }},
    "summary": {{
        "total_gaps_identified": 0,
        "critical_gaps": 0,
        "high_priority_gaps": 0,
        "areas_above_peer_average": ["Pillar 1"],
        "areas_below_peer_average": ["Pillar 2"],
        "overall_priority_focus": "Primary area needing immediate attention"
    }}
}}

CRITICAL: 
- Prioritize based on GAPS identified in benchmark
- Focus on areas below peer average
- Be specific and actionable
- Identify quick wins vs strategic investments
- Consider business impact and implementation effort
- Include both risk_level AND impact_if_not_fixed for each critical gap
- Include title, impact_score, and cost_estimate for each recommendation"""

        print("\n💡 Generating prioritized recommendations with Claude API...")
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text
        
        # Extract JSON from response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        recommendations = json.loads(response_text)
        return recommendations
    
    def display_recommendations(self, recommendations: dict):
        """Display recommendations in readable format"""
        print("\n" + "="*70)
        print("💡 PRIORITIZED RECOMMENDATIONS")
        print("="*70)
        
        summary = recommendations['summary']
        print(f"\n📊 SUMMARY:")
        print(f"   Total Gaps Identified: {summary['total_gaps_identified']}")
        print(f"   Critical Gaps: {summary['critical_gaps']}")
        print(f"   High Priority Gaps: {summary['high_priority_gaps']}")
        print(f"   Overall Focus: {summary['overall_priority_focus']}")
        
        print("\n" + "="*70)
        print("🔴 CRITICAL GAPS (Immediate Attention Required)")
        print("="*70)
        for gap in recommendations['critical_gaps']:
            print(f"\n❗ [{gap['pillar'].upper()}] {gap['gap']}")
            print(f"   Current: {gap['current_state']}")
            print(f"   Desired: {gap['desired_state']}")
            print(f"   Impact: {gap['business_impact']}")
            print(f"   Risk: {gap.get('risk_level', gap.get('priority', 'N/A'))}")
            print(f"   Priority: {gap['priority']} | Effort: {gap['effort_estimate']}")
        
        print("\n" + "="*70)
        print("✅ STRENGTHS TO MAINTAIN")
        print("="*70)
        for strength in recommendations['strengths_to_maintain']:
            print(f"\n💪 [{strength['pillar'].upper()}] {strength['strength']}")
            print(f"   Why: {strength['why_important']}")
        
        print("\n" + "="*70)
        print("🎯 TOP 10 PRIORITIZED RECOMMENDATIONS")
        print("="*70)
        for rec in recommendations['prioritized_recommendations'][:10]:
            quick_win = "⚡ QUICK WIN" if rec.get('quick_win') else ""
            rank = rec.get('rank', 0)
            print(f"\n#{rank} {quick_win}")
            print(f"   {rec['recommendation']}")
            print(f"   Pillar: {rec['pillar']} | Effort: {rec['effort_estimate']} | Impact: {rec.get('impact_score', 'N/A')}/10")
            print(f"   Rationale: {rec['rationale']}")
            if rec.get('success_criteria'):
                print(f"   Success Criteria:")
                for criterion in rec['success_criteria']:
                    print(f"      ✓ {criterion}")
        
        print("\n" + "="*70)
        print("📊 PILLAR PRIORITIES")
        print("="*70)
        for pillar, details in recommendations['pillar_priorities'].items():
            print(f"\n🔹 {pillar.upper()}: {details['priority_level']}")
            print(f"   Rationale: {details['rationale']}")
            print("   Key Improvements:")
            for improvement in details['key_improvements']:
                print(f"      • {improvement}")
        
        print("\n" + "="*70)
        print("💰 INVESTMENT GUIDANCE")
        print("="*70)
        print("\n⚡ High ROI Quick Wins:")
        for qw in recommendations['investment_priorities']['high_roi_quick_wins']:
            print(f"   • {qw}")
        
        print("\n🎯 Strategic Investments:")
        for si in recommendations['investment_priorities']['strategic_investments']:
            print(f"   • {si}")
        
        print("\n💵 Cost Optimization:")
        for co in recommendations['investment_priorities']['cost_optimization_opportunities']:
            print(f"   • {co}")
        
        print("\n" + "="*70)
    
    def run_recommendation(self, system_description: str, assessment_results: dict, benchmark_results: dict):
        """Complete recommendation workflow"""
        print("\n" + "="*70)
        print("💡 VAULTZERO RECOMMENDATION AGENT")
        print("="*70)
        
        recommendations = self.generate_recommendations(system_description, assessment_results, benchmark_results)
        self.display_recommendations(recommendations)
        return recommendations


if __name__ == "__main__":
    # GENERIC TEST DATA - For testing only
    test_system = "Cloud-based enterprise SaaS application"
    
    test_assessment = {
        "system_name": "Enterprise Cloud Application",
        "overall_score": 2.0,
        "overall_maturity_level": "INITIAL",
        "pillars": {
            "identity": {"maturity_level": "INITIAL", "score": 2},
            "devices": {"maturity_level": "ADVANCED", "score": 3},
            "networks": {"maturity_level": "INITIAL", "score": 2},
            "applications": {"maturity_level": "TRADITIONAL", "score": 1},
            "data": {"maturity_level": "INITIAL", "score": 2}
        }
    }
    
    test_benchmark = {
        "overall_percentile": 45,
        "pillar_rankings": {
            "identity": {"percentile": 35, "vs_peers": "below average"},
            "devices": {"percentile": 75, "vs_peers": "above average"},
            "networks": {"percentile": 40, "vs_peers": "below average"},
            "applications": {"percentile": 25, "vs_peers": "below average"},
            "data": {"percentile": 30, "vs_peers": "below average"}
        },
        "strengths_vs_peers": ["Device security and endpoint management"],
        "gaps_vs_peers": ["Application security", "Data protection", "Identity governance"]
    }
    
    agent = RecommendationAgent()
    recommendations = agent.run_recommendation(test_system, test_assessment, test_benchmark)
    
    with open("recommendation_test_results.json", "w") as f:
        json.dump(recommendations, f, indent=2)
    
    print("\n✅ Recommendations saved to recommendation_test_results.json")
