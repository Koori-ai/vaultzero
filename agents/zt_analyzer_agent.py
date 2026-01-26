"""
Zero Trust Analyzer Agent (Integrated with AWS MCP)
Evaluates organization against 7 Zero Trust pillars (NIST 800-207)

Enhanced version that combines:
- Document analysis (policies, controls, technologies)
- REAL evidence from AWS MCP Reader (IAM, S3, CloudTrail)
"""

from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
import logging

# Import AWS Zero Trust Reader (MCP Tool)
try:
    from tools.aws_zt_reader import AWSZeroTrustReader
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False


class ZeroTrustAnalyzerAgent(BaseAgent):
    """
    Analyzes Zero Trust maturity against NIST 800-207 framework.
    
    ENHANCED: Now integrates with AWS MCP Reader for REAL evidence!
    
    Evaluates 7 pillars:
    1. Identity       <- AWS IAM evidence
    2. Devices
    3. Networks
    4. Applications/Workloads
    5. Data           <- AWS S3 evidence
    6. Visibility & Analytics  <- AWS CloudTrail evidence
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
    
    # Map AWS evidence to ZT pillars
    AWS_PILLAR_MAPPING = {
        'Identity': 'Identity',
        'Data': 'Data',
        'Visibility': 'Visibility & Analytics'
    }
    
    def __init__(self, use_aws_evidence: bool = True, **kwargs):
        """
        Initialize the ZT Analyzer Agent.
        
        Args:
            use_aws_evidence: If True, collect real evidence from AWS (default: True)
        """
        super().__init__(
            name="ZeroTrustAnalyzerAgent",
            model="claude-sonnet-4-20250514",
            **kwargs
        )
        
        self.use_aws_evidence = use_aws_evidence and AWS_AVAILABLE
        self.aws_reader: Optional[AWSZeroTrustReader] = None
        self.aws_evidence: Optional[Dict[str, Any]] = None
        
        if self.use_aws_evidence:
            try:
                self.aws_reader = AWSZeroTrustReader()
                self.logger.info("✅ AWS MCP Reader initialized - will collect real evidence")
            except Exception as e:
                self.logger.warning(f"⚠️ AWS Reader not available: {e}")
                self.use_aws_evidence = False
        else:
            self.logger.info("ℹ️ AWS evidence collection disabled")
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze Zero Trust maturity.
        
        ENHANCED: Now collects AWS evidence before analysis!
        
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
            - aws_evidence_collected: Boolean indicating if AWS data was used
        """
        self.logger.info("Starting Zero Trust analysis")
        
        # Get extracted data from previous agent
        technologies = state.get('extracted_technologies', [])
        controls = state.get('extracted_controls', [])
        policies = state.get('extracted_policies', [])
        
        self.logger.info(f"Analyzing: {len(technologies)} technologies, "
                        f"{len(controls)} controls, {len(policies)} policies")
        
        # =====================================================================
        # NEW: Collect AWS Evidence (if enabled)
        # =====================================================================
        if self.use_aws_evidence and self.aws_reader:
            self.logger.info("🔍 Collecting REAL evidence from AWS...")
            try:
                self.aws_evidence = await self.aws_reader.collect_all_evidence()
                self.logger.info(f"✅ AWS evidence collected! Overall AWS score: {self.aws_evidence.get('overall_score', 'N/A')}/5")
            except Exception as e:
                self.logger.error(f"❌ Failed to collect AWS evidence: {e}")
                self.aws_evidence = None
        
        # Analyze each pillar
        pillar_scores = {}
        all_gaps = []
        all_strengths = []
        all_recommendations = []
        
        for pillar in self.ZT_PILLARS:
            self.logger.info(f"Analyzing pillar: {pillar}")
            
            # Get AWS evidence for this pillar (if available)
            aws_pillar_evidence = self._get_aws_evidence_for_pillar(pillar)
            
            analysis = await self._analyze_pillar(
                pillar=pillar,
                technologies=technologies,
                controls=controls,
                policies=policies,
                aws_evidence=aws_pillar_evidence  # NEW: Pass AWS evidence
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
            'analysis_complete': True,
            'aws_evidence_collected': self.aws_evidence is not None,
            'aws_evidence_summary': self._summarize_aws_evidence() if self.aws_evidence else None
        }
        
        return self.update_state(state, updates)
    
    def _get_aws_evidence_for_pillar(self, pillar: str) -> Optional[Dict[str, Any]]:
        """
        Get AWS evidence relevant to a specific ZT pillar.
        
        Args:
            pillar: The ZT pillar name
            
        Returns:
            AWS evidence dict or None if not available
        """
        if not self.aws_evidence:
            return None
        
        pillars_data = self.aws_evidence.get('pillars', {})
        
        # Map ZT pillar to AWS evidence
        if pillar == 'Identity':
            return pillars_data.get('Identity')
        elif pillar == 'Data':
            return pillars_data.get('Data')
        elif pillar == 'Visibility & Analytics':
            return pillars_data.get('Visibility')
        
        return None
    
    def _summarize_aws_evidence(self) -> Dict[str, Any]:
        """Create a summary of AWS evidence for reporting."""
        if not self.aws_evidence:
            return {}
        
        summary = {
            'source': 'AWS',
            'region': self.aws_evidence.get('region'),
            'collected_at': self.aws_evidence.get('collected_at'),
            'overall_aws_score': self.aws_evidence.get('overall_score'),
            'pillars_assessed': list(self.aws_evidence.get('pillars', {}).keys())
        }
        
        return summary
    
    async def _analyze_pillar(
        self,
        pillar: str,
        technologies: List[str],
        controls: List[str],
        policies: List[str],
        aws_evidence: Optional[Dict[str, Any]] = None  # NEW parameter
    ) -> Dict[str, Any]:
        """
        Analyze a single Zero Trust pillar.
        
        ENHANCED: Now incorporates real AWS evidence!
        
        Returns:
            - score: 0-5 maturity score
            - gaps: List of identified gaps
            - strengths: List of strengths
            - recommendations: List of recommendations
        """
        
        # Build system prompt
        system_prompt = f"""You are a Zero Trust security expert analyzing the {pillar} pillar.

Based on NIST 800-207 guidelines, evaluate the organization's maturity in this pillar.

Maturity Levels:
0 - No implementation
1 - Initial/Ad-hoc (some basic controls)
2 - Developing (documented processes, inconsistent)
3 - Defined (standardized, consistently applied)
4 - Managed (measured, controlled)
5 - Optimized (continuously improving, automated)

{"IMPORTANT: You have REAL AWS EVIDENCE to analyze. Weight this heavily in your scoring - actual system data is more reliable than policy documents alone!" if aws_evidence else ""}

Provide:
1. SCORE: Single number 0-5
2. GAPS: Specific weaknesses or missing controls
3. STRENGTHS: What's working well
4. RECOMMENDATIONS: Specific next steps

Be realistic and critical - most organizations are at level 2-3."""
        
        # Build context from extracted data
        context = f"""
PILLAR: {pillar}

TECHNOLOGIES IDENTIFIED (from documents):
{chr(10).join(['- ' + t for t in technologies]) if technologies else '- None identified'}

CONTROLS IDENTIFIED (from documents):
{chr(10).join(['- ' + c for c in controls]) if controls else '- None identified'}

POLICIES IDENTIFIED (from documents):
{chr(10).join(['- ' + p for p in policies]) if policies else '- None identified'}
"""
        
        # =====================================================================
        # NEW: Add AWS Evidence to Context
        # =====================================================================
        if aws_evidence:
            findings = aws_evidence.get('findings', {})
            aws_score = aws_evidence.get('maturity_score', 'N/A')
            
            context += f"""

═══════════════════════════════════════════════════════════════
🔒 REAL AWS EVIDENCE (Live Data from AWS Account)
═══════════════════════════════════════════════════════════════
Source: {aws_evidence.get('source', 'AWS')}
Collection Time: {aws_evidence.get('collected_at', 'Unknown')}
AWS Calculated Score: {aws_score}/5.0

ACTUAL FINDINGS:
"""
            # Add specific findings based on pillar
            if pillar == 'Identity':
                context += f"""
- Total IAM Users: {findings.get('total_users', 'Unknown')}
- MFA Enabled Users: {findings.get('mfa_enabled_count', 'Unknown')}
- MFA Adoption Rate: {findings.get('mfa_adoption_percent', 'Unknown')}%
- Users WITHOUT MFA: {findings.get('users_without_mfa', [])}
- Root Account MFA: {'✅ Enabled' if findings.get('root_account_mfa') else '❌ DISABLED'}
- Password Policy Exists: {'✅ Yes' if findings.get('password_policy', {}).get('exists') else '❌ No'}
- Access Keys > 90 days old: {findings.get('access_keys_over_90_days', 'Unknown')}
- Access Keys > 365 days old: {findings.get('access_keys_over_365_days', 'Unknown')}
"""
            elif pillar == 'Data':
                context += f"""
- Total S3 Buckets: {findings.get('total_buckets', 'Unknown')}
- Public Buckets: {findings.get('public_buckets_count', 'Unknown')} {findings.get('public_buckets', [])}
- Unencrypted Buckets: {findings.get('unencrypted_buckets_count', 'Unknown')} {findings.get('unencrypted_buckets', [])}
- Buckets without Versioning: {findings.get('no_versioning_count', 'Unknown')}
"""
            elif pillar == 'Visibility & Analytics':
                context += f"""
- CloudTrail Trails: {findings.get('total_trails', 'Unknown')}
- Multi-Region Logging: {'✅ Enabled' if findings.get('has_multi_region_logging') else '❌ DISABLED'}
- Active Logging Trails: {findings.get('logging_enabled_count', 'Unknown')}
"""
            
            context += """
═══════════════════════════════════════════════════════════════

Use the AWS evidence above to provide accurate scoring. Document claims should be validated against actual system state.
"""
        
        context += "\nAnalyze this pillar and provide score, gaps, strengths, and recommendations."
        
        try:
            response = await self.call_claude(system_prompt, context)
            
            # Parse response
            parsed = self._parse_pillar_analysis(response, pillar)
            
            # Add AWS evidence indicator
            if aws_evidence:
                parsed['aws_evidence_used'] = True
                parsed['aws_score'] = aws_evidence.get('maturity_score', 0)
            
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
        import re
        
        # Extract score
        score = 0
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
        import re
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
