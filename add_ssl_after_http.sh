#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Adding SSL to Working HTTP Proxy ===${NC}"

# Only run this AFTER HTTP proxy is confirmed working
echo -e "${YELLOW}1. Getting SSL certificate with Certbot...${NC}"
sudo certbot --nginx -d app.doctor-ai.io -d www.app.doctor-ai.io --non-interactive --agree-tos -m your-email@example.com --redirect

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ SSL certificate installed successfully${NC}"
    echo -e "${GREEN}✅ Your app is now accessible at: https://app.doctor-ai.io${NC}"
else
    echo -e "${RED}❌ SSL certificate installation failed${NC}"
    echo -e "${YELLOW}Make sure:${NC}"
    echo -e "${YELLOW}  - DNS points to your server${NC}"
    echo -e "${YELLOW}  - Ports 80 and 443 are open${NC}"
    echo -e "${YELLOW}  - Replace your-email@example.com with your actual email${NC}"
fi
