#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Checking if App is Running on Port 7001 ===${NC}"

# Check if port 7001 is in use
echo -e "${YELLOW}1. Checking port 7001...${NC}"
if sudo netstat -tlnp | grep :7001; then
    echo -e "${GREEN}✅ Something is listening on port 7001${NC}"
else
    echo -e "${RED}❌ Nothing listening on port 7001${NC}"
    echo -e "${YELLOW}Starting the app...${NC}"
    
    # Try to start the app
    cd /root/Doctor
    source venv/bin/activate
    nohup python app.py > app.log 2>&1 &
    sleep 2
    
    if sudo netstat -tlnp | grep :7001; then
        echo -e "${GREEN}✅ App started on port 7001${NC}"
    else
        echo -e "${RED}❌ Failed to start app${NC}"
        echo -e "${YELLOW}Check app.log for errors${NC}"
    fi
fi

# Test direct connection
echo -e "${YELLOW}2. Testing direct connection to port 7001...${NC}"
if curl -s http://localhost:7001 > /dev/null; then
    echo -e "${GREEN}✅ App responds on port 7001${NC}"
else
    echo -e "${RED}❌ App not responding on port 7001${NC}"
fi
