#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Testing External Domain Access ===${NC}"

# Check current Nginx configuration
echo -e "${YELLOW}1. Checking current Nginx site configuration:${NC}"
cat /etc/nginx/sites-enabled/app.doctor-ai.io 2>/dev/null || echo -e "${RED}❌ No site config found${NC}"

# Test DNS resolution
echo -e "\n${YELLOW}2. Testing DNS resolution:${NC}"
nslookup app.doctor-ai.io || echo -e "${RED}❌ DNS resolution failed${NC}"

# Check what server IP the domain points to
echo -e "\n${YELLOW}3. Checking domain IP:${NC}"
dig +short app.doctor-ai.io || echo -e "${RED}❌ No A record found${NC}"

# Check server's public IP
echo -e "\n${YELLOW}4. Server's public IP:${NC}"
curl -s ifconfig.me || curl -s ipinfo.io/ip || echo -e "${RED}❌ Cannot get public IP${NC}"

# Test external HTTP access
echo -e "\n${YELLOW}5. Testing external HTTP access:${NC}"
curl -v -H "Host: app.doctor-ai.io" http://$(curl -s ifconfig.me) 2>&1 | head -10

# Check if port 80 is accessible externally
echo -e "\n${YELLOW}6. Testing port 80 accessibility:${NC}"
timeout 5 nc -zv $(curl -s ifconfig.me) 80 2>&1 || echo -e "${RED}❌ Port 80 not accessible externally${NC}"

# Show all Nginx server blocks
echo -e "\n${YELLOW}7. All Nginx server blocks listening on port 80:${NC}"
grep -r "listen.*80" /etc/nginx/ 2>/dev/null | grep -v "#"

echo -e "\n${YELLOW}=== Test Complete ===${NC}"
