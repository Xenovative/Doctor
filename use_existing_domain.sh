#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Using Existing Domain Setup ===${NC}"

# Get server IPv4 (since most DNS providers prefer IPv4)
SERVER_IPV4=$(curl -s -4 ifconfig.me 2>/dev/null)
SERVER_IPV6=$(curl -s -6 ifconfig.me 2>/dev/null)

echo -e "${YELLOW}Server IPv4: $SERVER_IPV4${NC}"
echo -e "${YELLOW}Server IPv6: $SERVER_IPV6${NC}"

# Check if xenovative-ltd.com exists (from earlier configs)
echo -e "\n${YELLOW}1. Checking existing domain xenovative-ltd.com:${NC}"
nslookup xenovative-ltd.com || echo -e "${RED}❌ Domain not found${NC}"

# Create Nginx config using existing working domain pattern
echo -e "\n${YELLOW}2. Creating Nginx config for app.xenovative-ltd.com:${NC}"
sudo tee /etc/nginx/sites-available/app.xenovative-ltd.com > /dev/null <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name app.xenovative-ltd.com;
    
    location / {
        proxy_pass http://127.0.0.1:7001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/app.xenovative-ltd.com /etc/nginx/sites-enabled/

# Test and reload
if sudo nginx -t; then
    sudo systemctl reload nginx
    echo -e "${GREEN}✅ Nginx configured for app.xenovative-ltd.com${NC}"
else
    echo -e "${RED}❌ Nginx config error${NC}"
fi

echo -e "\n${YELLOW}=== Next Steps ===${NC}"
echo -e "${YELLOW}Add these DNS records to xenovative-ltd.com:${NC}"
echo -e "${GREEN}A record: app -> $SERVER_IPV4${NC}"
echo -e "${GREEN}AAAA record: app -> $SERVER_IPV6${NC}"
echo -e "\n${YELLOW}Then access: http://app.xenovative-ltd.com${NC}"
