#!/bin/bash

echo "=== Checking Nginx Configuration ==="

# Check current Nginx config files
echo "1. Current Nginx config files:"
find /etc/nginx -name "*.conf" -exec grep -l "app.doctor-ai.io\|doctor-ai" {} \; 2>/dev/null

# Test which server block handles the request
echo -e "\n2. Testing server block handling:"
curl -H "Host: app.doctor-ai.io" -I http://localhost 2>/dev/null

# Check Nginx error logs
echo -e "\n3. Recent Nginx errors:"
sudo tail -10 /var/log/nginx/error.log 2>/dev/null || echo "No error log found"

# Show current Nginx test result
echo -e "\n4. Nginx configuration test:"
sudo nginx -t
