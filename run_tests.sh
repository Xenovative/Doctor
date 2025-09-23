#!/bin/bash
# Quick test runner for Doctor AI analysis tests

echo "🏥 Doctor AI Test Runner"
echo "========================"

# Check if Flask server is running
if curl -s http://localhost:7001/ > /dev/null; then
    echo "✅ Flask server is running on localhost:7001"
    echo "🔗 Running tests in REAL MODE (end-to-end testing)"
    python test_ai_analysis.py real
else
    echo "❌ Flask server not detected on localhost:7001"
    echo "🎭 Running tests in MOCK MODE (development testing)"
    python test_ai_analysis.py mock
fi

echo ""
echo "📊 Test complete! Check ai_analysis_test_results.json for detailed results."
