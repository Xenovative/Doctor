#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== DNS Setup Check ===${NC}"

# Get server IPs
echo -e "${YELLOW}1. Server IP addresses:${NC}"
echo "IPv6: $(curl -s -6 ifconfig.me 2>/dev/null || echo 'Not available')"
echo "IPv4: $(curl -s -4 ifconfig.me 2>/dev/null || echo 'Not available')"

# Check if domain exists at all
echo -e "\n${YELLOW}2. Checking parent domain doctor-ai.io:${NC}"
nslookup doctor-ai.io || echo -e "${RED}❌ Parent domain doesn't exist${NC}"

# Check subdomain
echo -e "\n${YELLOW}3. Checking subdomain app.doctor-ai.io:${NC}"
nslookup app.doctor-ai.io || echo -e "${RED}❌ Subdomain doesn't exist${NC}"

# Check from external DNS servers
echo -e "\n${YELLOW}4. Checking from Google DNS (8.8.8.8):${NC}"
nslookup app.doctor-ai.io 8.8.8.8 || echo -e "${RED}❌ Not found on Google DNS${NC}"

echo -e "\n${YELLOW}5. Checking from Cloudflare DNS (1.1.1.1):${NC}"
nslookup app.doctor-ai.io 1.1.1.1 || echo -e "${RED}❌ Not found on Cloudflare DNS${NC}"

echo -e "\n${YELLOW}=== DNS Check Complete ===${NC}"
echo -e "${YELLOW}You need to:${NC}"
echo -e "${YELLOW}1. Register the domain doctor-ai.io OR${NC}"
echo -e "${YELLOW}2. Use a subdomain of an existing domain you own${NC}"
echo -e "${YELLOW}3. Add A record pointing to your server's IPv4: $(curl -s -4 ifconfig.me 2>/dev/null)${NC}"
echo -e "${YELLOW}4. Add AAAA record pointing to your server's IPv6: $(curl -s -6 ifconfig.me 2>/dev/null)${NC}"
