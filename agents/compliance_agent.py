"""
Compliance Mapping Agent
Maps Zero Trust findings to security frameworks
"""

from typing import Dict, Any, List, Tuple
from .base_agent import BaseAgent


class ComplianceAgent(BaseAgent):
    """
    Maps Zero Trust assessment findings to compliance frameworks:
    - NIST 800-207 (Zero Trust Architecture)
    - CMS ARS 5.1 (CMS Acceptable Risk Safeguards)
    - CISA BOD 22-01 (Binding Operational Directive)
    """
    
    FRAMEWORKS = {
        'NIST 800-207': {
            'name': 'Zero Trust Architecture',
            'sections': [
                'ZT Core Principles',
                'ZT Deployment Models',
                'Trust Algorithm',
                'ZT Components'
            ]
        },
        'CMS ARS 5.1': {
            'name': 'CMS Acceptable Risk Safeguards',
            'sections': [
                'Access Control',
                'Identity Management',
                'Continuous Monitoring',
                'Incident Response'
            ]
        },
        'CISA BOD 22-01': {
            'name': 'Reducing the Significant Risk of Known Exploited Vulnerabilities',
            'sections': [
                'Vulnerability Remediation',
                'Asset Management',
                'Patch Management'
            ]
        }
    }
    
    def __init__(self, **kwargs):
        super().__init__(
            name="ComplianceAgent",
            model="claude-sonnet-4-20250514",
            **kwargs
        )
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map findings to compliance frameworks.
        
        Expected state keys:
            - zt_scores: Dict of pillar scores
            - zt_gaps: List of gaps
            - zt_strengths: List of strengths
            - zt_recommendations: List of recommendations
            
        Returns updated state with:
            - compliance_matrix: Dict of framework -> status
            - compliance_gaps: List of compliance gaps
            - compliance_met: List of controls met
            - compliance_percentage: Overall compliance %
        """
        self.logger.info("Starting compliance mapping")
        
        # Validate input
        self.validate_state(state, ['zt_scores', 'zt_gaps', 'zt_strengths'])
        
        zt_scores = state['zt_scores']
        zt_gaps = state.get('zt_gaps', [])
        zt_strengths = state.get('zt_strengths', [])
        
        # Map to each framework
        framework_results = {}
        all_compliance_gaps = []
        all_compliance_met = []
        
        for framework_id, framework_info in self.FRAMEWORKS.items():
            self.logger.info(f"Mapping to {framework_id}")
            
            result = await self._map_to_framework(
                framework_id=framework_id,
                framework_info=framework_info,
                zt_scores=zt_scores,
                zt_gaps=zt_gaps,
                zt_strengths=zt_strengths
            )
            
            framework_results[framework_id] = result
            all_compliance_gaps.extend(result['gaps'])
            all_compliance_met.extend(result['controls_met'])
        
        # Calculate overall compliance
        total_controls = sum(r['total_controls'] for r in framework_results.values())
        met_controls = sum(r['controls_met_count'] for r in framework_results.values())
        
        compliance_percentage = (met_controls / total_controls * 100) if total_controls > 0 else 0
        
        self.logger.info(f"Overall compliance: {compliance_percentage:.1f}% "
                        f"({met_controls}/{total_controls} controls)")
        
        # Update state
        updates = {
            'compliance_matrix': framework_results,
            'compliance_gaps': all_compliance_gaps,
            'compliance_met': all_compliance_met,
            'compliance_percentage': round(compliance_percentage, 1),
            'compliance_status': self._get_compliance_status(compliance_percentage),
            'compliance_mapping_complete': True
        }
        
        return self.update_state(state, updates)
    
    async def _map_to_framework(
        self,
        framework_id: str,
        framework_info: Dict[str, Any],
        zt_scores: Dict[str, float],
        zt_gaps: List[str],
        zt_strengths: List[str]
    ) -> Dict[str, Any]:
        """
        Map ZT findings to a specific framework.
        
        Returns:
            - total_controls: Number of framework controls
            - controls_met_count: Number of controls satisfied
            - controls_met: List of satisfied controls
            - gaps: List of compliance gaps
            - compliance_score: 0-100 percentage
        """
        
        system_prompt = f"""You are a compliance expert mapping Zero Trust findings to {framework_id}.

Framework: {framework_info['name']}
Key Areas: {', '.join(framework_info['sections'])}

Based on the organization's Zero Trust maturity scores and findings, identify:
1. CONTROLS MET: Which framework controls are satisfied
2. GAPS: Which framework controls have gaps
3. RECOMMENDATIONS: How to improve compliance

Be specific and cite actual framework requirements where possible."""
        
        # Build context
        zt_summary = "\n".join([
            f"{pillar}: {score}/5" for pillar, score in zt_scores.items()
        ])
        
        gaps_summary = "\n".join([f"- {gap}" for gap in zt_gaps[:10]])  # First 10 gaps
        strengths_summary = "\n".join([f"- {s}" for s in zt_strengths[:10]])
        
        context = f"""
ZERO TRUST MATURITY SCORES:
{zt_summary}

IDENTIFIED GAPS:
{gaps_summary}

IDENTIFIED STRENGTHS:
{strengths_summary}

Map these findings to {framework_id} compliance.

Provide:
CONTROLS MET:
- control1
- control2

GAPS:
- gap1
- gap2

TOTAL CONTROLS: <number>
"""
        
        try:
            response = await self.call_claude(system_prompt, context)
            
            # Parse response
            controls_met = self._extract_section_list(response, 'CONTROLS MET:')
            gaps = self._extract_section_list(response, 'GAPS:')
            
            # Extract total controls
            total_controls = self._extract_total_controls(response)
            
            # Calculate compliance score
            controls_met_count = len(controls_met)
            compliance_score = (controls_met_count / total_controls * 100) if total_controls > 0 else 0
            
            # Add framework prefix to items
            controls_met = [f"[{framework_id}] {c}" for c in controls_met]
            gaps = [f"[{framework_id}] {g}" for g in gaps]
            
            return {
                'framework': framework_id,
                'total_controls': total_controls,
                'controls_met_count': controls_met_count,
                'controls_met': controls_met,
                'gaps': gaps,
                'compliance_score': round(compliance_score, 1)
            }
            
        except Exception as e:
            self.logger.error(f"Error mapping to {framework_id}: {str(e)}")
            
            # Return default on error
            return {
                'framework': framework_id,
                'total_controls': 10,
                'controls_met_count': 0,
                'controls_met': [],
                'gaps': [f"Could not map to {framework_id}"],
                'compliance_score': 0
            }
    
    def _extract_section_list(
        self,
        text: str,
        section_header: str
    ) -> List[str]:
        """Extract bullet points from a section."""
        items = []
        
        if section_header not in text:
            return items
        
        # Get section text
        section_start = text.find(section_header)
        section_text = text[section_start + len(section_header):]
        
        # Find next section (capitalized words followed by colon)
        import re
        next_section = re.search(r'\n[A-Z\s]+:', section_text)
        if next_section:
            section_text = section_text[:next_section.start()]
        
        # Extract lines with - or numbers
        lines = section_text.split('\n')
        for line in lines:
            line = line.strip()
            
            if line.startswith('-'):
                item = line[1:].strip()
            elif re.match(r'^\d+\.', line):
                item = re.sub(r'^\d+\.\s*', '', line)
            else:
                continue
            
            if item and len(item) > 5:  # Filter out very short items
                items.append(item)
        
        return items
    
    def _extract_total_controls(self, text: str) -> int:
        """Extract total controls count from response."""
        import re
        
        match = re.search(r'TOTAL CONTROLS:\s*(\d+)', text)
        if match:
            return int(match.group(1))
        
        # Default estimate based on framework
        return 15
    
    def _get_compliance_status(self, percentage: float) -> str:
        """Convert compliance percentage to status."""
        if percentage >= 90:
            return "Excellent"
        elif percentage >= 75:
            return "Good"
        elif percentage >= 60:
            return "Fair"
        elif percentage >= 40:
            return "Needs Improvement"
        else:
            return "Critical Gaps"
