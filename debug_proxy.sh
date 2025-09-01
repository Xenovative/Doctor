#!/bin/bash

echo "=== Debugging Reverse Proxy Issue ==="

# Check if app is running on port 7001
echo "1. Checking if app is running on port 7001:"
curl -I http://localhost:7001 2>/dev/null || echo "❌ No app running on port 7001"

# Check what's listening on port 7001
echo -e "\n2. Checking what's listening on port 7001:"
sudo netstat -tlnp | grep :7001 || echo "❌ Nothing listening on port 7001"

# Check if our Nginx config exists and is loaded
echo -e "\n3. Checking if our Nginx config exists:"
ls -la /etc/nginx/conf.d/99-doctor-ai-override.conf 2>/dev/null || echo "❌ Config file not found"

# Check Nginx configuration test
echo -e "\n4. Testing Nginx configuration:"
sudo nginx -t

# Check which server block is handling the request
echo -e "\n5. Testing which server block handles app.doctor-ai.io:"
curl -H "Host: app.doctor-ai.io" -I http://localhost 2>/dev/null

# Remove the problematic config and create a simpler one
echo -e "\n6. Creating a simple working config:"
sudo rm -f /etc/nginx/conf.d/99-doctor-ai-override.conf

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
sudo nginx -t && sudo systemctl reload nginx
echo "✅ Nginx reloaded"
