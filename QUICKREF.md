# VaultZero v2.0 - Quick Reference

## 📋 Phase 1 Checklist (Today - Sunday)

### ✅ COMPLETED
- [x] Install LangGraph dependencies
- [x] Create agents/ folder structure
- [x] Build BaseAgent class
- [x] Build DocumentAgent (proactive extraction)
- [x] Build ZeroTrustAnalyzerAgent (NIST 800-207 scoring)
- [x] Build ComplianceAgent (framework mapping)
- [x] Build ReportWriterAgent (DOCX generation)
- [x] Create LangGraph orchestrator
- [x] Write tests
- [x] Create README

### 🔄 NEXT: Copy to Your Project

```bash
cd C:\projects\vaultzero

# Copy these files:
agents\__init__.py
agents\base_agent.py
agents\document_agent.py
agents\zt_analyzer_agent.py
agents\compliance_agent.py
agents\report_writer_agent.py
orchestrator.py
tests\test_agents.py
```

### 🔄 THEN: Test Locally

```bash
# 1. Run setup
setup.bat

# 2. Set API key
set ANTHROPIC_API_KEY=your_key_here

# 3. Test agents
python -m pytest tests/test_agents.py -v

# 4. Test orchestrator (with sample files)
python orchestrator.py
```

## 🎯 Agent Overview

| Agent | Purpose | Model | Output |
|-------|---------|-------|--------|
| **DocumentAgent** | Parse & extract | Sonnet 4 | Technologies, controls, policies |
| **ZTAnalyzerAgent** | Maturity scoring | Sonnet 4 | Scores (0-5), gaps, strengths |
| **ComplianceAgent** | Framework mapping | Sonnet 4 | Compliance matrix, gaps |
| **ReportWriterAgent** | DOCX generation | Sonnet 4 + Haiku | Professional report |

## 🔧 Common Commands

```bash
# Install dependencies
pip install langgraph langchain langchain-anthropic --break-system-packages

# Run tests
python -m pytest tests/test_agents.py -v

# Run with coverage
python -m pytest tests/ --cov=agents --cov-report=html

# Test orchestrator
python orchestrator.py

# Run Streamlit app
streamlit run app.py --server.port 8080
```

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| "No module langgraph" | `pip install langgraph langchain --break-system-packages` |
| "API key not found" | `set ANTHROPIC_API_KEY=your_key` |
| "Document parsing error" | `pip install python-docx PyPDF2 --break-system-packages` |
| Tests fail | Normal if API key not set; check with `--tb=short` |

## 📊 Expected Test Results

```
tests/test_agents.py::TestBaseAgent::test_base_agent_initialization PASSED
tests/test_agents.py::TestBaseAgent::test_state_validation PASSED
tests/test_agents.py::TestBaseAgent::test_update_state PASSED
tests/test_agents.py::TestDocumentAgent::test_empty_files_list PASSED
tests/test_agents.py::TestZTAnalyzer::test_maturity_scoring PASSED
tests/test_agents.py::TestComplianceAgent::test_compliance_frameworks PASSED
tests/test_agents.py::TestReportWriter::test_score_conversion PASSED
tests/test_agents.py::TestOrchestrator::test_orchestrator_initialization PASSED

========================= 8+ passed =========================
```

## 🚀 Demo Flow (Tuesday)

1. **Setup** (30 seconds)
   - User uploads 3-5 documents
   - Enters API key
   - Clicks "Run AI Assessment"

2. **Processing** (2-3 minutes)
   ```
   📄 Analyzing documents... (30s)
   🔍 Evaluating Zero Trust maturity... (45s)
   ✅ Mapping compliance frameworks... (45s)
   📝 Generating report... (30s)
   ```

3. **Results** (instant)
   - Maturity score: 2.8/5.0 (Defined)
   - Compliance: 67.5%
   - Download professional DOCX report

**Value Prop:** Days of manual assessment → 3 minutes automated

## 📁 File Structure After Setup

```
C:\projects\vaultzero\
├── agents\               ← NEW
│   ├── __init__.py
│   ├── base_agent.py
│   ├── document_agent.py
│   ├── zt_analyzer_agent.py
│   ├── compliance_agent.py
│   └── report_writer_agent.py
│
├── orchestrator.py       ← NEW
├── app.py               ← UPDATE (add AI mode)
├── requirements.txt     ← UPDATE
│
├── tools\               ← EXISTING (Days 1-2)
│   ├── kevs_tool.py
│   └── nvd_tool.py
│
├── tests\
│   ├── test_kevs_tool.py    ← EXISTING
│   ├── test_nvd_tool.py     ← EXISTING
│   └── test_agents.py       ← NEW
│
└── rag\                 ← EXISTING (v1.0)
    └── rag_system.py
```

## ⏰ Time Remaining Today

**Phase 1 Complete!** (1.5 hours used)

**Remaining phases (4.5-6.5 hours):**
- Phase 2: Integration testing (1 hour)
- Phase 3: Streamlit UI update (1.5 hours)
- Phase 4: Local testing (1 hour)
- Phase 5: Git commits (0.5 hour)

**You're ahead of schedule!** ✅

## 📞 If You Get Stuck

1. Check README.md for detailed instructions
2. Review test output: `pytest -v --tb=short`
3. Verify imports: `python -c "import langgraph"`
4. Check API key: `echo %ANTHROPIC_API_KEY%`

---

**Ready to continue!** Next step: Copy files and test locally.
