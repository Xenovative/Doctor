#!/bin/bash

# AI Doctor Matching System - Application Diagnostics
# Usage: ./diagnose-app.sh

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_DIR="/opt/ai-doctor-matching"
SERVICE_NAME="ai-doctor-matching"

echo -e "${BLUE}🔍 AI Doctor Application Diagnostics${NC}"
echo ""

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Test Python environment
test_python_env() {
    echo -e "${BLUE}=== Python Environment Test ===${NC}"
    
    if [[ -d "$APP_DIR/venv" ]]; then
        log_info "Virtual environment exists ✓"
        
        # Test Python imports
        echo "Testing Python imports..."
        sudo -u doctor-app $APP_DIR/venv/bin/python -c "
import sys
print(f'Python version: {sys.version}')

try:
    import flask
    print(f'Flask version: {flask.__version__}')
except ImportError as e:
    print(f'Flask import error: {e}')

try:
    import pandas
    print(f'Pandas version: {pandas.__version__}')
except ImportError as e:
    print(f'Pandas import error: {e}')

try:
    import requests
    print(f'Requests version: {requests.__version__}')
except ImportError as e:
    print(f'Requests import error: {e}')
"
    else
        log_error "Virtual environment not found"
    fi
    echo ""
}

# Test app.py directly
test_app_direct() {
    echo -e "${BLUE}=== Direct App Test ===${NC}"
    
    if [[ -f "$APP_DIR/app.py" ]]; then
        log_info "Testing app.py import..."
        
        # Test app import
        sudo -u doctor-app bash -c "
cd $APP_DIR
source venv/bin/activate
timeout 30 python -c '
import sys
sys.path.insert(0, \".\")

try:
    print(\"Importing app...\")
    from app import app
    print(\"App imported successfully ✓\")
    
    print(\"Testing app configuration...\")
    print(f\"Debug mode: {app.debug}\")
    print(f\"Testing mode: {app.testing}\")
    
    print(\"Testing routes...\")
    with app.test_client() as client:
        response = client.get(\"/health\")
        print(f\"Health endpoint status: {response.status_code}\")
        if response.status_code == 200:
            print(f\"Health response: {response.get_json()}\")
        else:
            print(f\"Health error: {response.data}\")
            
except Exception as e:
    import traceback
    print(f\"Error importing/testing app: {e}\")
    traceback.print_exc()
'
"
    else
        log_error "app.py not found"
    fi
    echo ""
}

# Test environment variables
test_env_vars() {
    echo -e "${BLUE}=== Environment Variables ===${NC}"
    
    if [[ -f "$APP_DIR/.env" ]]; then
        log_info ".env file exists ✓"
        echo "Environment variables:"
        sudo -u doctor-app cat "$APP_DIR/.env" | grep -v "API_KEY" | head -10
        
        # Test environment loading
        sudo -u doctor-app bash -c "
cd $APP_DIR
source venv/bin/activate
python -c '
import os
from dotenv import load_dotenv
load_dotenv()

print(f\"AI_PROVIDER: {os.getenv(\\\"AI_PROVIDER\\\", \\\"Not set\\\")}\"
print(f\"PORT: {os.getenv(\\\"PORT\\\", \\\"Not set\\\")}\"
print(f\"FLASK_ENV: {os.getenv(\\\"FLASK_ENV\\\", \\\"Not set\\\")}\"
'
"
    else
        log_error ".env file not found"
    fi
    echo ""
}

# Test data files
test_data_files() {
    echo -e "${BLUE}=== Data Files ===${NC}"
    
    if [[ -d "$APP_DIR/assets" ]]; then
        log_info "Assets directory exists ✓"
        echo "Assets contents:"
        ls -la "$APP_DIR/assets/"
        
        # Test CSV loading
        sudo -u doctor-app bash -c "
cd $APP_DIR
source venv/bin/activate
python -c '
import pandas as pd
import os

csv_path = os.path.join(\"assets\", \"finddoc_doctors_detailed 2.csv\")
if os.path.exists(csv_path):
    print(f\"CSV file exists: {csv_path}\")
    try:
        df = pd.read_csv(csv_path)
        print(f\"CSV loaded successfully: {len(df)} rows\")
    except Exception as e:
        print(f\"Error loading CSV: {e}\")
else:
    print(f\"CSV file not found: {csv_path}\")
'
"
    else
        log_error "Assets directory not found"
    fi
    echo ""
}

# Test AI service
test_ai_service() {
    echo -e "${BLUE}=== AI Service Test ===${NC}"
    
    sudo -u doctor-app bash -c "
cd $APP_DIR
source venv/bin/activate
python -c '
import os
from dotenv import load_dotenv
load_dotenv()

ai_provider = os.getenv(\"AI_PROVIDER\", \"ollama\")
print(f\"AI Provider: {ai_provider}\")

if ai_provider == \"ollama\":
    import requests
    try:
        response = requests.get(\"http://localhost:11434\", timeout=5)
        print(f\"Ollama service: Available (status {response.status_code})\")
    except Exception as e:
        print(f\"Ollama service: Not available ({e})\")
elif ai_provider == \"openrouter\":
    api_key = os.getenv(\"OPENROUTER_API_KEY\")
    if api_key:
        print(\"OpenRouter API key: Set ✓\")
    else:
        print(\"OpenRouter API key: Not set ✗\")
'
"
    echo ""
}

# Test manual app start
test_manual_start() {
    echo -e "${BLUE}=== Manual App Start Test ===${NC}"
    
    log_info "Attempting to start app manually (will timeout after 10 seconds)..."
    
    sudo -u doctor-app bash -c "
cd $APP_DIR
source venv/bin/activate
timeout 10 python app.py 2>&1
" || echo "Manual start timed out or failed"
    
    echo ""
}

# Show recent logs with more detail
show_detailed_logs() {
    echo -e "${BLUE}=== Detailed Service Logs ===${NC}"
    
    echo "Last 50 lines of service logs:"
    journalctl -u $SERVICE_NAME -n 50 --no-pager
    
    echo ""
    echo "Python error logs (if any):"
    journalctl -u $SERVICE_NAME --no-pager | grep -i "error\|exception\|traceback" | tail -20
    
    echo ""
}

# Provide fix suggestions
suggest_fixes() {
    echo -e "${BLUE}=== Suggested Fixes ===${NC}"
    
    echo "1. Stop the service and check for hanging processes:"
    echo "   sudo systemctl stop $SERVICE_NAME"
    echo "   sudo pkill -f gunicorn"
    echo ""
    
    echo "2. Test app manually with debug output:"
    echo "   cd $APP_DIR"
    echo "   sudo -u doctor-app venv/bin/python -c 'from app import app; app.run(debug=True, port=7000)'"
    echo ""
    
    echo "3. Check for missing dependencies:"
    echo "   cd $APP_DIR"
    echo "   sudo -u doctor-app venv/bin/pip list"
    echo ""
    
    echo "4. Reinstall dependencies:"
    echo "   cd $APP_DIR"
    echo "   sudo -u doctor-app venv/bin/pip install -r requirements.txt --force-reinstall"
    echo ""
    
    echo "5. Check CSV file permissions:"
    echo "   sudo chown -R doctor-app:doctor-app $APP_DIR/assets/"
    echo ""
    
    echo "6. Restart with single worker for debugging:"
    echo "   sudo systemctl stop $SERVICE_NAME"
    echo "   cd $APP_DIR"
    echo "   sudo -u doctor-app venv/bin/gunicorn --bind 0.0.0.0:7000 --workers 1 --timeout 120 --log-level debug app:app"
    echo ""
}

# Main function
main() {
    test_python_env
    test_env_vars
    test_data_files
    test_ai_service
    test_app_direct
    test_manual_start
    show_detailed_logs
    suggest_fixes
}

# Run diagnostics
main "$@"
