#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Starting App on Port 7001 ===${NC}"

# Kill any existing app processes
echo -e "${YELLOW}1. Stopping any existing app processes...${NC}"
pkill -f "app.py" 2>/dev/null || echo "No existing processes"

# Navigate to app directory
cd /root/Doctor || { echo -e "${RED}❌ Cannot find /root/Doctor directory${NC}"; exit 1; }

# Activate virtual environment
echo -e "${YELLOW}2. Activating virtual environment...${NC}"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✅ Virtual environment activated${NC}"
else
    echo -e "${RED}❌ Virtual environment not found${NC}"
    exit 1
fi

# Check if app.py exists
if [ ! -f "app.py" ]; then
    echo -e "${RED}❌ app.py not found${NC}"
    exit 1
fi

# Start the app on port 7001
echo -e "${YELLOW}3. Starting app on port 7001...${NC}"
export FLASK_APP=app.py
export FLASK_ENV=production
nohup python app.py --host=0.0.0.0 --port=7001 > app.log 2>&1 &
APP_PID=$!

# Wait and check if app started
sleep 3
if ps -p $APP_PID > /dev/null; then
    echo -e "${GREEN}✅ App started with PID: $APP_PID${NC}"
    
    # Test if port is listening
    if netstat -tlnp | grep :7001; then
        echo -e "${GREEN}✅ App is listening on port 7001${NC}"
        
        # Test connection
        if curl -s http://localhost:7001 > /dev/null; then
            echo -e "${GREEN}✅ App is responding${NC}"
        else
            echo -e "${RED}❌ App not responding${NC}"
        fi
    else
        echo -e "${RED}❌ App not listening on port 7001${NC}"
    fi
else
    echo -e "${RED}❌ App failed to start${NC}"
    echo -e "${YELLOW}Check app.log for errors:${NC}"
    tail -10 app.log 2>/dev/null || echo "No log file found"
fi
