#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Debugging Connection Refused Error ===${NC}"

# Check if app is running on port 7001
echo -e "${YELLOW}1. Checking what's listening on port 7001:${NC}"
sudo netstat -tlnp | grep :7001 || echo -e "${RED}❌ Nothing listening on port 7001${NC}"

# Check if app process is running
echo -e "\n${YELLOW}2. Checking for Python app processes:${NC}"
ps aux | grep -v grep | grep "app.py\|python.*7001" || echo -e "${RED}❌ No app processes found${NC}"

# Test direct connection to port 7001
echo -e "\n${YELLOW}3. Testing direct connection to localhost:7001:${NC}"
curl -v http://localhost:7001 2>&1 | head -10

# Check Nginx status
echo -e "\n${YELLOW}4. Checking Nginx status:${NC}"
sudo systemctl status nginx --no-pager -l

# Check Nginx error logs
echo -e "\n${YELLOW}5. Recent Nginx errors:${NC}"
sudo tail -5 /var/log/nginx/error.log 2>/dev/null || echo "No error log found"

# Test Nginx proxy
echo -e "\n${YELLOW}6. Testing Nginx proxy:${NC}"
curl -H "Host: app.doctor-ai.io" -v http://localhost 2>&1 | head -10

# Check firewall status
echo -e "\n${YELLOW}7. Checking firewall:${NC}"
sudo ufw status 2>/dev/null || echo "UFW not installed"

echo -e "\n${YELLOW}=== Debug Complete ===${NC}"
