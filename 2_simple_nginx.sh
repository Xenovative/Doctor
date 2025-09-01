#!/bin/bash

echo "=== Creating Simple Nginx Config ==="

# Remove any existing conflicting configs
sudo rm -f /etc/nginx/conf.d/99-doctor-ai-override.conf
sudo rm -f /etc/nginx/conf.d/doctor-ai-simple.conf

# Create simple HTTP-only config first
sudo tee /etc/nginx/conf.d/doctor-ai-simple.conf > /dev/null <<'EOL'
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

echo "✅ Simple config created"

# Test and reload
sudo nginx -t && sudo systemctl reload nginx
echo "✅ Nginx reloaded"
