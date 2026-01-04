"""
VaultZero Agents Module
Includes both v1.0 and v2.0 agents
"""

# v1.0 agents (existing)
from .assessment_agent import AssessmentAgent
from .benchmark_agent import BenchmarkAgent
from .recommendation_agent import RecommendationAgent

# v2.0 agents (new - LangGraph multi-agent)
from .base_agent import BaseAgent
from .document_agent import DocumentAgent
from .zt_analyzer_agent import ZeroTrustAnalyzerAgent
from .compliance_agent import ComplianceAgent
from .report_writer_agent import ReportWriterAgent

__all__ = [
    # v1.0
    'AssessmentAgent',
    'BenchmarkAgent',
    'RecommendationAgent',
    # v2.0
    'BaseAgent',
    'DocumentAgent',
    'ZeroTrustAnalyzerAgent',
    'ComplianceAgent',
    'ReportWriterAgent',
]