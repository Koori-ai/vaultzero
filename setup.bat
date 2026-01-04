@echo off
REM VaultZero v2.0 Setup Script
REM Run this from C:\projects\vaultzero

echo ========================================
echo VaultZero v2.0 - Agent Setup
echo ========================================
echo.

echo [1/5] Installing LangGraph dependencies...
pip install langgraph langchain langchain-anthropic --break-system-packages
if %errorlevel% neq 0 (
    echo ERROR: Failed to install LangGraph
    pause
    exit /b 1
)
echo ✓ LangGraph installed

echo.
echo [2/5] Installing document processing libraries...
pip install python-docx PyPDF2 python-pptx openpyxl pandas --break-system-packages
if %errorlevel% neq 0 (
    echo ERROR: Failed to install document libraries
    pause
    exit /b 1
)
echo ✓ Document libraries installed

echo.
echo [3/5] Installing testing dependencies...
pip install pytest pytest-asyncio pytest-cov --break-system-packages
if %errorlevel% neq 0 (
    echo ERROR: Failed to install test libraries
    pause
    exit /b 1
)
echo ✓ Test libraries installed

echo.
echo [4/5] Verifying installation...
python -c "import langgraph; import langchain; import anthropic; print('✓ All imports successful')"
if %errorlevel% neq 0 (
    echo ERROR: Import verification failed
    pause
    exit /b 1
)

echo.
echo [5/5] Running basic tests...
python -m pytest tests/test_agents.py -v --tb=short
if %errorlevel% neq 0 (
    echo WARNING: Some tests failed (this is OK if you haven't set API key yet)
)

echo.
echo ========================================
echo ✓ Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Set your API key:
echo    set ANTHROPIC_API_KEY=your_key_here
echo.
echo 2. Test the orchestrator:
echo    python orchestrator.py
echo.
echo 3. Run the Streamlit app:
echo    streamlit run app.py --server.port 8080
echo.
echo For more info, see README.md
echo ========================================
pause
