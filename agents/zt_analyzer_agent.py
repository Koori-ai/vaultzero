"""
Zero Trust Analyzer Agent
Evaluates organization against 7 Zero Trust pillars (NIST 800-207)
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class ZeroTrustAnalyzerAgent(BaseAgent):
    """
    Analyzes Zero Trust maturity against NIST 800-207 framework.
    
    Evaluates 7 pillars:
    1. Identity
    2. Devices
    3. Networks
    4. Applications/Workloads
    5. Data
    6. Visibility & Analytics
    7. Automation & Orchestration
    
    Scores each on 0-5 maturity scale:
    0 - No implementation
    1 - Initial/Ad-hoc
    2 - Developing
    3 - Defined
    4 - Managed
    5 - Optimized
    """
    
    ZT_PILLARS = [
        'Identity',
        'Devices',
        'Networks',
        'Applications/Workloads',
        'Data',
        'Visibility & Analytics',
        'Automation & Orchestration'
    ]
    
    def __init__(self, **kwargs):
        super().__init__(
            name="ZeroTrustAnalyzerAgent",
            model="claude-sonnet-4-20250514",  # Use Sonnet 4 for analysis
            **kwargs
        )
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze Zero Trust maturity.
        
        Expected state keys:
            - extracted_technologies: List of technologies
            - extracted_controls: List of ZT controls
            - extracted_policies: List of policies
            - combined_document_text: Text from documents (optional)
            
        Returns updated state with:
            - zt_scores: Dict of pillar -> score (0-5)
            - zt_gaps: List of identified gaps
            - zt_strengths: List of strengths
            - zt_recommendations: List of recommendations
            - overall_maturity_level: Average score
        """
        self.logger.info("Starting Zero Trust analysis")
        
        # Get extracted data from previous agent
        technologies = state.get('extracted_technologies', [])
        controls = state.get('extracted_controls', [])
        policies = state.get('extracted_policies', [])
        
        self.logger.info(f"Analyzing: {len(technologies)} technologies, "
                        f"{len(controls)} controls, {len(policies)} policies")
        
        # Analyze each pillar
        pillar_scores = {}
        all_gaps = []
        all_strengths = []
        all_recommendations = []
        
        for pillar in self.ZT_PILLARS:
            self.logger.info(f"Analyzing pillar: {pillar}")
            
            analysis = await self._analyze_pillar(
                pillar=pillar,
                technologies=technologies,
                controls=controls,
                policies=policies
            )
            
            pillar_scores[pillar] = analysis['score']
            all_gaps.extend(analysis['gaps'])
            all_strengths.extend(analysis['strengths'])
            all_recommendations.extend(analysis['recommendations'])
        
        # Calculate overall maturity
        overall_maturity = sum(pillar_scores.values()) / len(pillar_scores)
        maturity_level = self._get_maturity_level(overall_maturity)
        
        self.logger.info(f"Overall maturity: {overall_maturity:.2f}/5.0 ({maturity_level})")
        
        # Update state
        updates = {
            'zt_scores': pillar_scores,
            'zt_gaps': all_gaps,
            'zt_strengths': all_strengths,
            'zt_recommendations': all_recommendations,
            'overall_maturity_score': round(overall_maturity, 2),
            'overall_maturity_level': maturity_level,
            'analysis_complete': True
        }
        
        return self.update_state(state, updates)
    
    async def _analyze_pillar(
        self,
        pillar: str,
        technologies: List[str],
        controls: List[str],
        policies: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze a single Zero Trust pillar.
        
        Returns:
            - score: 0-5 maturity score
            - gaps: List of identified gaps
            - strengths: List of strengths
            - recommendations: List of recommendations
        """
        
        system_prompt = f"""You are a Zero Trust security expert analyzing the {pillar} pillar.

Based on NIST 800-207 guidelines, evaluate the organization's maturity in this pillar.

Maturity Levels:
0 - No implementation
1 - Initial/Ad-hoc (some basic controls)
2 - Developing (documented processes, inconsistent)
3 - Defined (standardized, consistently applied)
4 - Managed (measured, controlled)
5 - Optimized (continuously improving, automated)

Provide:
1. SCORE: Single number 0-5
2. GAPS: Specific weaknesses or missing controls
3. STRENGTHS: What's working well
4. RECOMMENDATIONS: Specific next steps

Be realistic and critical - most organizations are at level 2-3."""
        
        # Build context from extracted data
        context = f"""
PILLAR: {pillar}

TECHNOLOGIES IDENTIFIED:
{chr(10).join(['- ' + t for t in technologies]) if technologies else '- None identified'}

CONTROLS IDENTIFIED:
{chr(10).join(['- ' + c for c in controls]) if controls else '- None identified'}

POLICIES IDENTIFIED:
{chr(10).join(['- ' + p for p in policies]) if policies else '- None identified'}

Analyze this pillar and provide score, gaps, strengths, and recommendations."""
        
        try:
            response = await self.call_claude(system_prompt, context)
            
            # Parse response
            parsed = self._parse_pillar_analysis(response, pillar)
            
            return parsed
            
        except Exception as e:
            self.logger.error(f"Error analyzing {pillar}: {str(e)}")
            
            # Return default on error
            return {
                'score': 0,
                'gaps': [f"Could not analyze {pillar}"],
                'strengths': [],
                'recommendations': [f"Manual review needed for {pillar}"]
            }
    
    def _parse_pillar_analysis(
        self,
        response: str,
        pillar: str
    ) -> Dict[str, Any]:
        """Parse Claude's analysis response."""
        
        # Extract score
        score = 0
        import re
        score_match = re.search(r'SCORE:\s*(\d)', response)
        if score_match:
            score = int(score_match.group(1))
            # Validate 0-5 range
            score = max(0, min(5, score))
        
        # Extract lists
        gaps = self._extract_section_list(response, 'GAPS:')
        strengths = self._extract_section_list(response, 'STRENGTHS:')
        recommendations = self._extract_section_list(response, 'RECOMMENDATIONS:')
        
        # Add pillar context to items
        gaps = [f"[{pillar}] {g}" for g in gaps]
        strengths = [f"[{pillar}] {s}" for s in strengths]
        recommendations = [f"[{pillar}] {r}" for r in recommendations]
        
        return {
            'score': score,
            'gaps': gaps,
            'strengths': strengths,
            'recommendations': recommendations
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
        
        # Find next section (capitalized word followed by colon)
        next_section = re.search(r'\n[A-Z]+:', section_text)
        if next_section:
            section_text = section_text[:next_section.start()]
        
        # Extract lines with - or numbers
        lines = section_text.split('\n')
        for line in lines:
            line = line.strip()
            
            # Remove leading - or numbers
            if line.startswith('-'):
                item = line[1:].strip()
            elif re.match(r'^\d+\.', line):
                item = re.sub(r'^\d+\.\s*', '', line)
            else:
                continue
            
            if item:
                items.append(item)
        
        return items
    
    def _get_maturity_level(self, score: float) -> str:
        """Convert numeric score to maturity level name."""
        if score < 1.0:
            return "Initial"
        elif score < 2.0:
            return "Developing"
        elif score < 3.0:
            return "Defined"
        elif score < 4.0:
            return "Managed"
        else:
            return "Optimized"
