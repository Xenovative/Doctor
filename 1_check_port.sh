#!/bin/bash

echo "=== Checking Port 7001 ==="

# Check if anything is listening on port 7001
echo "1. What's listening on port 7001:"
sudo netstat -tlnp | grep :7001 || echo "❌ Nothing listening on port 7001"

# Test direct connection to port 7001
echo -e "\n2. Testing direct connection to localhost:7001:"
curl -I http://localhost:7001 2>/dev/null && echo "✅ App responding on port 7001" || echo "❌ No response from port 7001"

# Check all listening ports
echo -e "\n3. All listening ports:"
sudo netstat -tlnp | grep LISTEN | sort
