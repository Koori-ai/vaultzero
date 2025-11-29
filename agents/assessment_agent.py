"""
VaultZero Assessment Agent
Conducts interactive Zero Trust maturity assessments
"""

from anthropic import Anthropic
import os
from typing import Dict
import json
from dotenv import load_dotenv

load_dotenv()

class AssessmentAgent:
    def __init__(self):
        """Initialize Assessment Agent with Claude"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
        
    def conduct_assessment(self, system_description: str, answers: Dict[str, str]) -> Dict:
        """
        Conduct Zero Trust assessment with user-provided answers
        
        Args:
            system_description: Description of system to assess
            answers: Dictionary of pillar -> answer
            
        Returns:
            Complete assessment results
        """
        
        prompt = f"""You are a Zero Trust security expert. Assess this system's ZT maturity.

SYSTEM TO ASSESS:
{system_description}

USER'S RESPONSES BY PILLAR:
{json.dumps(answers, indent=2)}

Based on these answers, provide a detailed assessment in JSON format:
{{
    "system_name": "Extract from description or create appropriate name",
    "pillars": {{
        "identity": {{
            "score": <0-4>,
            "maturity_level": "TRADITIONAL/INITIAL/ADVANCED/OPTIMAL",
            "findings": "2-3 sentence assessment",
            "gaps": ["Specific gap 1", "Specific gap 2"],
            "strengths": ["Specific strength 1"]
        }},
        "devices": {{
            "score": <0-4>,
            "maturity_level": "TRADITIONAL/INITIAL/ADVANCED/OPTIMAL",
            "findings": "2-3 sentence assessment",
            "gaps": ["Specific gap 1"],
            "strengths": ["Specific strength 1"]
        }},
        "networks": {{
            "score": <0-4>,
            "maturity_level": "TRADITIONAL/INITIAL/ADVANCED/OPTIMAL",
            "findings": "2-3 sentence assessment",
            "gaps": ["Specific gap 1"],
            "strengths": ["Specific strength 1"]
        }},
        "applications": {{
            "score": <0-4>,
            "maturity_level": "TRADITIONAL/INITIAL/ADVANCED/OPTIMAL",
            "findings": "2-3 sentence assessment",
            "gaps": ["Specific gap 1"],
            "strengths": ["Specific strength 1"]
        }},
        "data": {{
            "score": <0-4>,
            "maturity_level": "TRADITIONAL/INITIAL/ADVANCED/OPTIMAL",
            "findings": "2-3 sentence assessment",
            "gaps": ["Specific gap 1"],
            "strengths": ["Specific strength 1"]
        }}
    }},
    "overall_score": <average of all pillar scores>,
    "overall_maturity_level": "TRADITIONAL/INITIAL/ADVANCED/OPTIMAL",
    "key_gaps": ["Top 5 critical gaps across all pillars"],
    "quick_wins": ["3-5 low-effort, high-impact improvements"],
    "strategic_recommendations": ["3-5 long-term strategic initiatives"]
}}

MATURITY SCORING:
- 0-0.9: TRADITIONAL (Legacy security, perimeter-based)
- 1.0-1.9: INITIAL (Starting ZT journey, some modern controls)
- 2.0-2.9: ADVANCED (Strong ZT implementation, continuous improvement)
- 3.0-4.0: OPTIMAL (Industry-leading ZT maturity)

Be specific, actionable, and objective. Provide ONLY valid JSON."""

        print("\n🔍 Running Zero Trust assessment with Claude API...")
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result_text = response.content[0].text
        
        # Extract JSON from response
        try:
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            assessment = json.loads(result_text)
            return assessment
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON: {e}")
            print(f"Raw response: {result_text}")
            return {"error": "Failed to parse assessment", "raw": result_text}
    
    def display_assessment(self, assessment: Dict):
        """Display assessment results in readable format"""
        print("\n" + "="*70)
        print("📊 ZERO TRUST MATURITY ASSESSMENT RESULTS")
        print("="*70)
        
        print(f"\n🏢 System: {assessment.get('system_name', 'N/A')}")
        print(f"📈 Overall Score: {assessment['overall_score']:.1f}/4.0")
        print(f"🎯 Overall Maturity: {assessment['overall_maturity_level']}")
        
        print("\n" + "="*70)
        print("📋 PILLAR-BY-PILLAR ASSESSMENT")
        print("="*70)
        
        for pillar_name, pillar_data in assessment['pillars'].items():
            print(f"\n🔹 {pillar_name.upper()}")
            print(f"   Score: {pillar_data['score']:.1f}/4.0 | Maturity: {pillar_data['maturity_level']}")
            print(f"   {pillar_data['findings']}")
            
            if pillar_data.get('strengths'):
                print(f"   ✅ Strengths:")
                for strength in pillar_data['strengths']:
                    print(f"      • {strength}")
            
            if pillar_data.get('gaps'):
                print(f"   ⚠️  Gaps:")
                for gap in pillar_data['gaps']:
                    print(f"      • {gap}")
        
        print("\n" + "="*70)
        print("🎯 KEY FINDINGS")
        print("="*70)
        
        print("\n⚠️  Critical Gaps:")
        for gap in assessment['key_gaps']:
            print(f"   • {gap}")
        
        print("\n⚡ Quick Wins (Start Here):")
        for win in assessment['quick_wins']:
            print(f"   • {win}")
        
        print("\n🚀 Strategic Recommendations:")
        for rec in assessment['strategic_recommendations']:
            print(f"   • {rec}")
        
        print("\n" + "="*70)
    
    def run_assessment(self, system_description: str, answers: Dict[str, str]):
        """Complete assessment workflow"""
        print("\n" + "="*70)
        print("🎯 VAULTZERO ASSESSMENT AGENT")
        print("="*70)
        
        # Conduct assessment
        results = self.conduct_assessment(system_description, answers)
        
        # Display results
        if 'error' not in results:
            self.display_assessment(results)
        
        return results


# Test function
if __name__ == "__main__":
    # GENERIC TEST DATA - For testing only
    
    agent = AssessmentAgent()
    
    test_system = "Cloud-based enterprise SaaS application with customer data"
    
    test_answers = {
        "identity": "Single sign-on with MFA enforced for all users. Role-based access control implemented with regular reviews.",
        "devices": "Corporate devices managed with endpoint detection and response. BYOD allowed with mobile device management.",
        "networks": "Cloud-hosted infrastructure with security groups. Network segmentation partially implemented.",
        "applications": "Security testing integrated in CI/CD pipeline. Application-level monitoring and logging in place.",
        "data": "Data classification framework exists but not fully enforced. Encryption at rest implemented, in-transit encryption partial."
    }
    
    print("Testing VaultZero Assessment Agent...")
    print("="*70)
    
    results = agent.run_assessment(test_system, test_answers)
    
    # Save results
    with open("assessment_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n✅ Results saved to assessment_test_results.json")