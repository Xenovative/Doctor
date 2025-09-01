#!/bin/bash

echo "=== Testing Proxy Setup ==="

# Test direct app connection
echo "1. Testing direct app connection:"
curl -I http://localhost:7001 2>/dev/null && echo "✅ App responds directly" || echo "❌ App not responding"

# Test proxy through Nginx
echo -e "\n2. Testing proxy through Nginx:"
curl -H "Host: app.doctor-ai.io" -I http://localhost 2>/dev/null && echo "✅ Proxy working" || echo "❌ Proxy not working"

# Test external domain (if DNS is set up)
echo -e "\n3. Testing external domain:"
curl -I http://app.doctor-ai.io 2>/dev/null && echo "✅ External domain working" || echo "❌ External domain not working"

# Show what's actually being served
echo -e "\n4. What's being served:"
curl -H "Host: app.doctor-ai.io" http://localhost 2>/dev/null | head -5
