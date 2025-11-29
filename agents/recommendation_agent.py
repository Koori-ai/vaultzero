"""
Recommendation Agent - Generates prioritized 6-month Zero Trust implementation roadmap
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
    
    def generate_roadmap(self, 
                        system_description: str,
                        assessment_results: dict,
                        benchmark_results: dict):
        """Generate 6-month implementation roadmap with priorities and costs"""
        
        prompt = f"""You are a Zero Trust implementation strategist. Create a detailed 6-month roadmap.

SYSTEM CONTEXT:
{system_description}

CURRENT STATE (Assessment):
{json.dumps(assessment_results, indent=2)}

BENCHMARK POSITION:
{json.dumps(benchmark_results, indent=2)}

Generate a comprehensive 6-month implementation roadmap in JSON format:

{{
    "executive_summary": "2-3 sentence overview of strategy",
    "quick_wins": [
        {{
            "initiative": "Specific quick win",
            "timeline": "Weeks 1-4",
            "effort": "Low/Medium/High",
            "impact": "Low/Medium/High",
            "cost_estimate": "$X - $Y",
            "why_now": "Why this is urgent",
            "success_metrics": ["Measurable outcome 1", "Measurable outcome 2"]
        }}
    ],
    "medium_term": [
        {{
            "initiative": "Medium-term improvement",
            "timeline": "Months 3-4",
            "effort": "Low/Medium/High",
            "impact": "Low/Medium/High",
            "cost_estimate": "$X - $Y",
            "dependencies": ["What must be done first"],
            "success_metrics": ["Measurable outcome 1"]
        }}
    ],
    "long_term": [
        {{
            "initiative": "Transformational change",
            "timeline": "Months 5-6",
            "effort": "Low/Medium/High",
            "impact": "Low/Medium/High",
            "cost_estimate": "$X - $Y",
            "dependencies": ["What must be done first"],
            "success_metrics": ["Measurable outcome 1"]
        }}
    ],
    "month_by_month": {{
        "month_1": {{
            "focus": "Primary focus area",
            "initiatives": ["Initiative 1", "Initiative 2"],
            "milestones": ["Milestone 1", "Milestone 2"]
        }},
        "month_2": {{"focus": "...", "initiatives": [], "milestones": []}},
        "month_3": {{"focus": "...", "initiatives": [], "milestones": []}},
        "month_4": {{"focus": "...", "initiatives": [], "milestones": []}},
        "month_5": {{"focus": "...", "initiatives": [], "milestones": []}},
        "month_6": {{"focus": "...", "initiatives": [], "milestones": []}}
    }},
    "total_cost_estimate": {{
        "minimum": "$X",
        "maximum": "$Y",
        "breakdown": {{
            "identity": "$X",
            "devices": "$X",
            "networks": "$X",
            "applications": "$X",
            "data": "$X"
        }}
    }},
    "risk_mitigation": [
        {{
            "risk": "Potential risk",
            "mitigation": "How to address it",
            "owner": "Who should own this"
        }}
    ],
    "expected_outcomes": {{
        "6_month_maturity_target": "Target overall maturity level",
        "pillar_improvements": {{
            "identity": "Current -> Target",
            "devices": "Current -> Target",
            "networks": "Current -> Target",
            "applications": "Current -> Target",
            "data": "Current -> Target"
        }},
        "percentile_improvement": "Expected percentile change vs peers"
    }}
}}

CRITICAL: Prioritize based on GAPS identified. Focus on areas below peer average. Be specific and actionable."""

        print("\n🗺️  Generating implementation roadmap with Claude API...")
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=6000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text
        
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        roadmap = json.loads(response_text)
        return roadmap
    
    def display_roadmap(self, roadmap: dict):
        """Display roadmap in readable format"""
        print("\n" + "="*70)
        print("🗺️  6-MONTH ZERO TRUST IMPLEMENTATION ROADMAP")
        print("="*70)
        
        print(f"\n📋 EXECUTIVE SUMMARY:")
        print(f"   {roadmap['executive_summary']}")
        
        print(f"\n💰 TOTAL INVESTMENT: {roadmap['total_cost_estimate']['minimum']} - {roadmap['total_cost_estimate']['maximum']}")
        
        print("\n" + "="*70)
        print("⚡ QUICK WINS (Months 1-2)")
        print("="*70)
        for qw in roadmap['quick_wins']:
            print(f"\n✅ {qw['initiative']}")
            print(f"   Timeline: {qw['timeline']}")
            print(f"   Effort: {qw['effort']} | Impact: {qw['impact']}")
            print(f"   Cost: {qw['cost_estimate']}")
            print(f"   Why Now: {qw['why_now']}")
            print(f"   Success Metrics:")
            for metric in qw['success_metrics']:
                print(f"      • {metric}")
        
        print("\n" + "="*70)
        print("🎯 MEDIUM-TERM INITIATIVES (Months 3-4)")
        print("="*70)
        for mt in roadmap['medium_term']:
            print(f"\n📊 {mt['initiative']}")
            print(f"   Timeline: {mt['timeline']}")
            print(f"   Effort: {mt['effort']} | Impact: {mt['impact']}")
            print(f"   Cost: {mt['cost_estimate']}")
            if 'dependencies' in mt:
                print(f"   Dependencies: {', '.join(mt['dependencies'])}")
            print(f"   Success Metrics:")
            for metric in mt['success_metrics']:
                print(f"      • {metric}")
        
        print("\n" + "="*70)
        print("🚀 TRANSFORMATIONAL INITIATIVES (Months 5-6)")
        print("="*70)
        for lt in roadmap['long_term']:
            print(f"\n🌟 {lt['initiative']}")
            print(f"   Timeline: {lt['timeline']}")
            print(f"   Effort: {lt['effort']} | Impact: {lt['impact']}")
            print(f"   Cost: {lt['cost_estimate']}")
            if 'dependencies' in lt:
                print(f"   Dependencies: {', '.join(lt['dependencies'])}")
            print(f"   Success Metrics:")
            for metric in lt['success_metrics']:
                print(f"      • {metric}")
        
        print("\n" + "="*70)
        print("📅 MONTH-BY-MONTH TIMELINE")
        print("="*70)
        for month_key, month_data in roadmap['month_by_month'].items():
            month_num = month_key.split('_')[1]
            print(f"\n📆 MONTH {month_num}: {month_data['focus']}")
            print("   Initiatives:")
            for init in month_data['initiatives']:
                print(f"      • {init}")
            print("   Milestones:")
            for milestone in month_data['milestones']:
                print(f"      ✓ {milestone}")
        
        print("\n" + "="*70)
        print("🎯 EXPECTED OUTCOMES (End of Month 6)")
        print("="*70)
        print(f"\n   Target Maturity: {roadmap['expected_outcomes']['6_month_maturity_target']}")
        print(f"   Percentile Improvement: {roadmap['expected_outcomes']['percentile_improvement']}")
        print("\n   Pillar Improvements:")
        for pillar, improvement in roadmap['expected_outcomes']['pillar_improvements'].items():
            print(f"      • {pillar.title()}: {improvement}")
        
        print("\n" + "="*70)
        print("⚠️  RISK MITIGATION STRATEGIES")
        print("="*70)
        for risk in roadmap['risk_mitigation']:
            print(f"\n   Risk: {risk['risk']}")
            print(f"   Mitigation: {risk['mitigation']}")
            print(f"   Owner: {risk['owner']}")
        
        print("\n" + "="*70)
        
    def run_recommendation(self, system_description: str, assessment_results: dict, benchmark_results: dict):
        """Complete recommendation workflow"""
        print("\n" + "="*70)
        print("🎯 VAULTZERO RECOMMENDATION AGENT")
        print("="*70)
        
        roadmap = self.generate_roadmap(system_description, assessment_results, benchmark_results)
        self.display_roadmap(roadmap)
        return roadmap


if __name__ == "__main__":
    # GENERIC TEST DATA - For testing only
    test_system = "Cloud-based enterprise SaaS application"
    
    test_assessment = {
        "system_name": "Enterprise Cloud Application",
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
    roadmap = agent.run_recommendation(test_system, test_assessment, test_benchmark)
    
    with open("roadmap_test_results.json", "w") as f:
        json.dump(roadmap, f, indent=2)
    
    print("\n✅ Roadmap saved to roadmap_test_results.json")