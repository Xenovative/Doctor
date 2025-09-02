#!/bin/bash

echo "=== Direct Fix: Modify Existing HestiaCP Config ==="

# The simplest approach - directly modify the existing domain config
# that's already handling app.doctor-ai.io

# Find the existing config file
EXISTING_CONFIG=$(find /etc/nginx -name "*.conf" -exec grep -l "app.doctor-ai.io\|doctor-ai" {} \; 2>/dev/null | head -1)

if [ -n "$EXISTING_CONFIG" ]; then
    echo "Found existing config: $EXISTING_CONFIG"
    
    # Backup the original
    sudo cp "$EXISTING_CONFIG" "$EXISTING_CONFIG.backup"
    
    # Replace the proxy_pass line to point to port 7001
    sudo sed -i 's|proxy_pass.*|proxy_pass http://127.0.0.1:7001;|g' "$EXISTING_CONFIG"
    
    echo "✅ Modified existing config to point to port 7001"
else
    echo "No existing config found, creating new one..."
    
    # Create a config that uses a different approach
    sudo tee /etc/nginx/conf.d/zzz-doctor-ai-final.conf > /dev/null <<'EOL'
# Final override for app.doctor-ai.io - loads last due to zzz prefix
server {
    listen 8080;
    server_name app.doctor-ai.io;
    
    location / {
        proxy_pass http://127.0.0.1:7001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect port 80 requests to port 8080 internally
server {
    listen 80;
    server_name app.doctor-ai.io;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOL
    
    echo "✅ Created fallback config"
fi

# Test and reload
sudo nginx -t && sudo systemctl reload nginx

echo "✅ Configuration updated - test with: curl -H 'Host: app.doctor-ai.io' http://localhost"
