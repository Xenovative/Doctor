#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Clean Reverse Proxy Setup for app.doctor-ai.io ===${NC}"

# Step 1: Clean up existing configurations
echo -e "${YELLOW}1. Cleaning up existing configurations...${NC}"
sudo rm -f /etc/nginx/sites-enabled/app.doctor-ai.io
sudo rm -f /etc/nginx/sites-available/app.doctor-ai.io
sudo rm -f /etc/nginx/conf.d/app-doctor-ai.conf
sudo rm -f /etc/nginx/conf.d/doctor-ai-simple.conf
sudo rm -f /etc/nginx/conf.d/99-doctor-ai-override.conf
sudo rm -f /etc/nginx/conf.d/zzz-doctor-ai-final.conf

# Step 2: Create clean Nginx configuration
echo -e "${YELLOW}2. Creating clean Nginx configuration...${NC}"
sudo tee /etc/nginx/sites-available/app.doctor-ai.io > /dev/null <<'EOF'
server {
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

# Step 3: Enable the site
echo -e "${YELLOW}3. Enabling site...${NC}"
sudo ln -sf /etc/nginx/sites-available/app.doctor-ai.io /etc/nginx/sites-enabled/

# Step 4: Test configuration
echo -e "${YELLOW}4. Testing Nginx configuration...${NC}"
if sudo nginx -t; then
    echo -e "${GREEN}✅ Nginx configuration is valid${NC}"
    
    # Step 5: Reload Nginx
    echo -e "${YELLOW}5. Reloading Nginx...${NC}"
    sudo systemctl reload nginx
    echo -e "${GREEN}✅ Nginx reloaded successfully${NC}"
    
    # Step 6: Test the proxy
    echo -e "${YELLOW}6. Testing proxy...${NC}"
    if curl -s -H "Host: app.doctor-ai.io" http://localhost > /dev/null; then
        echo -e "${GREEN}✅ Proxy is working${NC}"
    else
        echo -e "${RED}❌ Proxy test failed - check if app is running on port 7001${NC}"
    fi
    
else
    echo -e "${RED}❌ Nginx configuration test failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Reverse proxy setup complete!${NC}"
echo -e "${YELLOW}Your app should now be accessible at: http://app.doctor-ai.io${NC}"
