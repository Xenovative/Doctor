#!/bin/bash

echo "=== Alternative Fix: Use Existing HestiaCP Domain ==="

# Since HestiaCP is managing the domain, let's work with it
# First, check what domains exist
echo "1. Current domains in HestiaCP:"
v-list-web-domains xenovative

# Create custom config in the existing domain directory
echo -e "\n2. Creating custom config for existing domain:"

# Check if idleai domain exists and use it as template
if [ -d "/home/xenovative/conf/web/idleai.xenovative-ltd.com" ]; then
    echo "Using idleai domain as template..."
    
    # Create app.doctor-ai.io domain
    v-add-web-domain xenovative doctor-ai.io
    
    # Add subdomain
    v-add-web-domain-alias xenovative doctor-ai.io app.doctor-ai.io
    
    # Create custom Nginx config
    sudo tee /home/xenovative/conf/web/doctor-ai.io/nginx.conf_custom > /dev/null <<'EOL'
server {
    listen 80;
    server_name app.doctor-ai.io;
    
    location / {
        proxy_pass http://127.0.0.1:7001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOL

    # Rebuild the domain
    v-rebuild-web-domain xenovative doctor-ai.io
    
else
    echo "Creating new domain structure..."
    
    # Alternative: modify existing domain config directly
    sudo tee /etc/nginx/conf.d/app-doctor-ai.conf > /dev/null <<'EOL'
# Direct override for app.doctor-ai.io
upstream doctor_ai_app {
    server 127.0.0.1:7001;
}

server {
    listen 8080;  # Use different port to avoid conflict
    server_name app.doctor-ai.io;
    
    location / {
        proxy_pass http://doctor_ai_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOL

fi

# Test and reload
sudo nginx -t && sudo systemctl reload nginx
echo "✅ Alternative configuration applied"
