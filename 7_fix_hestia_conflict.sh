#!/bin/bash

echo "=== Fixing HestiaCP Port Conflict ==="

# Remove our conflicting config
sudo rm -f /etc/nginx/conf.d/doctor-ai-simple.conf

# Check if domain exists in HestiaCP
echo "1. Checking if domain exists in HestiaCP:"
v-list-web-domains xenovative | grep -i doctor-ai || echo "Domain not found in HestiaCP"

# Add domain to HestiaCP if it doesn't exist
echo -e "\n2. Adding domain to HestiaCP:"
v-add-web-domain xenovative app.doctor-ai.io

# Create custom Nginx template in HestiaCP directory
echo -e "\n3. Creating custom Nginx template:"
sudo mkdir -p /home/xenovative/conf/web/app.doctor-ai.io/

sudo tee /home/xenovative/conf/web/app.doctor-ai.io/nginx.conf_custom > /dev/null <<'EOL'
location / {
    proxy_pass http://127.0.0.1:7001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 300s;
    proxy_connect_timeout 300s;
}
EOL

# Rebuild domain configuration
echo -e "\n4. Rebuilding domain configuration:"
v-rebuild-web-domain xenovative app.doctor-ai.io

# Test and reload
sudo nginx -t && sudo systemctl reload nginx
echo "✅ HestiaCP configuration updated"
