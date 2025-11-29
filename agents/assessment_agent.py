"""
VaultZero Assessment Agent
Conducts interactive Zero Trust maturity assessments
"""

from anthropic import Anthropic
import os
from typing import Dict, List
import json

class AssessmentAgent:
    def __init__(self):
        """Initialize Assessment Agent with Claude"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
        
    def quick_assessment(self, system_description: str, answers: Dict[str, str]) -> Dict:
        """
        Quick assessment with pre-provided answers
        
        Args:
            system_description: System to assess
            answers: Dictionary of pillar -> answer
            
        Returns:
            Assessment results
        """
        
        prompt = f"""You are a Zero Trust security expert. Assess this system's ZT maturity.

System: {system_description}

User provided these answers:

{json.dumps(answers, indent=2)}

Based on these answers, provide a detailed assessment in JSON format:
{{
    "pillars": {{
        "Identity": {{"score": X.X, "maturity": "LEVEL", "findings": "details"}},
        "Devices": {{"score": X.X, "maturity": "LEVEL", "findings": "details"}},
        "Networks": {{"score": X.X, "maturity": "LEVEL", "findings": "details"}},
        "Applications": {{"score": X.X, "maturity": "LEVEL", "findings": "details"}},
        "Data": {{"score": X.X, "maturity": "LEVEL", "findings": "details"}}
    }},
    "overall_score": X.X,
    "overall_maturity": "LEVEL",
    "key_gaps": ["list of 3-5 main gaps"],
    "quick_wins": ["list of 3 quick improvements"],
    "recommendations": ["list of 3-5 strategic recommendations"]
}}

Maturity levels:
- 0-0.9: TRADITIONAL
- 1.0-1.9: INITIAL  
- 2.0-2.9: ADVANCED
- 3.0-4.0: OPTIMAL

Provide ONLY the JSON, no other text."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=3000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        result_text = response.content[0].text
        
        # Extract JSON from response
        try:
            # Remove markdown code blocks if present
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            assessment = json.loads(result_text)
            return assessment
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Raw response: {result_text}")
            return {"error": "Failed to parse assessment", "raw": result_text}


# Test function
def test_assessment_agent():
    """Test the assessment agent"""
    from dotenv import load_dotenv
    load_dotenv()
    
    agent = AssessmentAgent()
    
    # Test system
    system_desc = "Public-facing web application handling customer PII data, hosted on AWS"
    
    # Sample answers
    answers = {
        "Identity": "We use Okta SSO with MFA enforced for all users. Role-based access control is implemented.",
        "Devices": "Corporate laptops are managed via Intune. BYOD is allowed for contractors with basic MDM.",
        "Networks": "Applications are in AWS with security groups. No microsegmentation implemented yet.",
        "Applications": "Security testing in CI/CD. Runtime monitoring with basic logging.",
        "Data": "PII is identified but not classified systematically. Database encryption at rest only."
    }
    
    print("Testing VaultZero Assessment Agent...")
    print("="*60)
    
    result = agent.quick_assessment(system_desc, answers)
    
    print("\nAssessment Results:")
    print("="*60)
    print(json.dumps(result, indent=2))
    
    return result


if __name__ == "__main__":
    test_assessment_agent()