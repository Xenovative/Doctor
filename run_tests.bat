@echo off
REM Quick test runner for Doctor AI analysis tests

echo 🏥 Doctor AI Test Runner
echo ========================

REM Check if Flask server is running
curl -s http://localhost:7001/ >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Flask server is running on localhost:7001
    echo 🔗 Running tests in REAL MODE (end-to-end testing)
    python test_ai_analysis.py real
) else (
    echo ❌ Flask server not detected on localhost:7001
    echo 🎭 Running tests in MOCK MODE (development testing)
    python test_ai_analysis.py mock
)

echo.
echo 📊 Test complete! Check ai_analysis_test_results.json for detailed results.
pause
