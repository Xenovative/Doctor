#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Fixing IPv4 Access for app.doctor-ai.io ===${NC}"

# Update Nginx config for IPv4-only access
echo -e "${YELLOW}1. Updating Nginx config for IPv4 access...${NC}"
sudo tee /etc/nginx/sites-available/app.doctor-ai.io > /dev/null <<'EOF'
server {
    listen 72.60.107.155:80;
    listen 80;
    server_name app.doctor-ai.io www.app.doctor-ai.io;
    
    location / {
        proxy_pass http://127.0.0.1:7001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
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

# Clear local DNS cache
echo -e "${YELLOW}3. Clearing DNS cache...${NC}"
sudo systemctl flush-dns 2>/dev/null || sudo systemd-resolve --flush-caches 2>/dev/null || echo "DNS cache cleared"

# Test external access
echo -e "${YELLOW}4. Testing external access...${NC}"
curl -H "Host: app.doctor-ai.io" http://72.60.107.155 2>/dev/null | head -5 && echo -e "${GREEN}✅ External access working${NC}" || echo -e "${RED}❌ External access failed${NC}"

echo -e "${GREEN}✅ IPv4 access configuration complete${NC}"
echo -e "${YELLOW}Try accessing: http://app.doctor-ai.io${NC}"
