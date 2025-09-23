#!/usr/bin/env python3
"""
Doctor AI Test Runner
Automatically detects server status and runs appropriate test mode
"""

import subprocess
import sys
import os

def check_server():
    """Check if Flask server is running"""
    try:
        import requests
        response = requests.get('http://localhost:7001/', timeout=3)
        return response.status_code == 200
    except:
        return False

def main():
    print("🏥 Doctor AI Test Runner")
    print("=" * 30)

    # Check server status
    server_running = check_server()

    if server_running:
        print("✅ Flask server detected on localhost:7001")
        print("🔗 Running in REAL MODE (end-to-end testing)")
        mode = "real"
    else:
        print("❌ Flask server not detected on localhost:7001")
        print("🎭 Running in MOCK MODE (development testing)")
        mode = "mock"

    print("\n🚀 Starting tests...")
    print("-" * 30)

    # Run the test
    try:
        result = subprocess.run([sys.executable, "test_ai_analysis.py", mode],
                              capture_output=False, text=True, cwd=os.getcwd())
        return result.returncode
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    if exit_code == 0:
        print("\n✅ Tests completed successfully!")
        print("📊 Check ai_analysis_test_results.json for detailed results.")
    else:
        print(f"\n❌ Tests failed with exit code: {exit_code}")
    input("\nPress Enter to exit...")
