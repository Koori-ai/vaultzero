"""
Tests for VaultZero Agents
"""

import pytest
import asyncio
from agents import (
    BaseAgent,
    DocumentAgent,
    ZeroTrustAnalyzerAgent,
    ComplianceAgent,
    ReportWriterAgent
)
from orchestrator import VaultZeroOrchestrator


class TestBaseAgent:
    """Test BaseAgent functionality."""
    
    def test_base_agent_initialization(self):
        """Test agent can be initialized."""
        
        class TestAgent(BaseAgent):
            async def process(self, state):
                return state
        
        agent = TestAgent(name="TestAgent")
        
        assert agent.name == "TestAgent"
        assert agent.model == "claude-sonnet-4-20250514"
        assert agent.temperature == 0.0
    
    def test_state_validation(self):
        """Test state validation."""
        
        class TestAgent(BaseAgent):
            async def process(self, state):
                return state
        
        agent = TestAgent(name="TestAgent")
        
        # Valid state
        state = {'key1': 'value1', 'key2': 'value2'}
        assert agent.validate_state(state, ['key1', 'key2'])
        
        # Invalid state
        with pytest.raises(ValueError):
            agent.validate_state(state, ['key3'])
    
    def test_update_state(self):
        """Test state update."""
        
        class TestAgent(BaseAgent):
            async def process(self, state):
                return state
        
        agent = TestAgent(name="TestAgent")
        
        state = {'existing': 'value'}
        updates = {'new_key': 'new_value'}
        
        new_state = agent.update_state(state, updates)
        
        assert new_state['existing'] == 'value'
        assert new_state['new_key'] == 'new_value'
        assert 'last_updated' in new_state
        assert new_state['last_agent'] == 'TestAgent'


class TestDocumentAgent:
    """Test DocumentAgent functionality."""
    
    @pytest.mark.asyncio
    async def test_empty_files_list(self):
        """Test handling of empty files list."""
        
        agent = DocumentAgent()
        
        state = {'uploaded_files': []}
        result = await agent.process(state)
        
        assert result['documents_analyzed'] == 0
        assert result['extraction_status'] == 'no_files'


class TestZTAnalyzer:
    """Test ZeroTrustAnalyzerAgent."""
    
    @pytest.mark.asyncio
    async def test_maturity_scoring(self):
        """Test maturity level calculation."""
        
        agent = ZeroTrustAnalyzerAgent()
        
        # Test score to level conversion
        assert agent._get_maturity_level(0.5) == "Initial"
        assert agent._get_maturity_level(1.5) == "Developing"
        assert agent._get_maturity_level(2.5) == "Defined"
        assert agent._get_maturity_level(3.5) == "Managed"
        assert agent._get_maturity_level(4.5) == "Optimized"


class TestComplianceAgent:
    """Test ComplianceAgent."""
    
    def test_compliance_frameworks(self):
        """Test framework definitions."""
        
        agent = ComplianceAgent()
        
        assert 'NIST 800-207' in agent.FRAMEWORKS
        assert 'CMS ARS 5.1' in agent.FRAMEWORKS
        assert 'CISA BOD 22-01' in agent.FRAMEWORKS
    
    def test_compliance_status(self):
        """Test compliance status calculation."""
        
        agent = ComplianceAgent()
        
        assert agent._get_compliance_status(95) == "Excellent"
        assert agent._get_compliance_status(80) == "Good"
        assert agent._get_compliance_status(65) == "Fair"
        assert agent._get_compliance_status(45) == "Needs Improvement"
        assert agent._get_compliance_status(20) == "Critical Gaps"


class TestReportWriter:
    """Test ReportWriterAgent."""
    
    def test_score_conversion(self):
        """Test score to maturity level conversion."""
        
        agent = ReportWriterAgent()
        
        assert agent._score_to_level(0.5) == "Initial"
        assert agent._score_to_level(1.5) == "Developing"
        assert agent._score_to_level(2.5) == "Defined"
        assert agent._score_to_level(3.5) == "Managed"
        assert agent._score_to_level(4.5) == "Optimized"


class TestOrchestrator:
    """Test VaultZeroOrchestrator."""
    
    def test_orchestrator_initialization(self):
        """Test orchestrator can be initialized."""
        
        orchestrator = VaultZeroOrchestrator()
        
        assert orchestrator.document_agent is not None
        assert orchestrator.zt_analyzer is not None
        assert orchestrator.compliance_agent is not None
        assert orchestrator.report_writer is not None
        assert orchestrator.workflow is not None
    
    def test_progress_calculation(self):
        """Test workflow progress calculation."""
        
        orchestrator = VaultZeroOrchestrator()
        
        # No steps complete
        state = {}
        assert orchestrator._calculate_progress(state) == 0
        
        # All steps complete
        state = {
            'extraction_status': 'complete',
            'analysis_complete': True,
            'compliance_mapping_complete': True,
            'report_generated': True
        }
        assert orchestrator._calculate_progress(state) == 100
        
        # 2 steps complete
        state = {
            'extraction_status': 'complete',
            'analysis_complete': True,
            'compliance_mapping_complete': False,
            'report_generated': False
        }
        assert orchestrator._calculate_progress(state) == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
