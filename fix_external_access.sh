#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Fixing External Access for app.doctor-ai.io ===${NC}"

# Get server's public IP
SERVER_IP=$(curl -s ifconfig.me)
echo -e "${YELLOW}Server IP: $SERVER_IP${NC}"

# Remove existing config and create new one that listens on all interfaces
echo -e "${YELLOW}1. Creating Nginx config for external access...${NC}"
sudo tee /etc/nginx/sites-available/app.doctor-ai.io > /dev/null <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name app.doctor-ai.io www.app.doctor-ai.io $SERVER_IP;
    
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
sudo ln -sf /etc/nginx/sites-available/app.doctor-ai.io /etc/nginx/sites-enabled/

# Test and reload
echo -e "${YELLOW}2. Testing and reloading Nginx...${NC}"
if sudo nginx -t; then
    sudo systemctl reload nginx
    echo -e "${GREEN}✅ Nginx reloaded${NC}"
else
    echo -e "${RED}❌ Nginx config error${NC}"
    exit 1
fi

# Test external access
echo -e "${YELLOW}3. Testing external access...${NC}"
curl -H "Host: app.doctor-ai.io" http://$SERVER_IP 2>/dev/null | head -5 && echo -e "${GREEN}✅ External access working${NC}" || echo -e "${RED}❌ External access failed${NC}"

echo -e "${GREEN}✅ External access configuration complete${NC}"
echo -e "${YELLOW}Try accessing: http://app.doctor-ai.io${NC}"
