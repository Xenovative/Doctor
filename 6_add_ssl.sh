#!/bin/bash

echo "=== Adding SSL to Working HTTP Config ==="

# Only run this AFTER the HTTP proxy is working

# Create HTTPS config
sudo tee /etc/nginx/conf.d/doctor-ai-ssl.conf > /dev/null <<'EOL'
server {
    listen 80;
    server_name app.doctor-ai.io www.app.doctor-ai.io;
    return 301 https://app.doctor-ai.io$request_uri;
}

server {
    listen 443 ssl;
    http2 on;
    server_name app.doctor-ai.io;
    
    ssl_certificate /etc/ssl/certs/ssl-cert-snakeoil.pem;
    ssl_certificate_key /etc/ssl/private/ssl-cert-snakeoil.key;
    
    location / {
        proxy_pass http://127.0.0.1:7001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOL

# Remove the HTTP-only config
sudo rm -f /etc/nginx/conf.d/doctor-ai-simple.conf

# Test and reload
sudo nginx -t && sudo systemctl reload nginx
echo "✅ SSL config applied"

# Get Let's Encrypt certificate
echo "Getting Let's Encrypt certificate..."
sudo certbot --nginx -d app.doctor-ai.io -d www.app.doctor-ai.io --email your-email@example.com --agree-tos --non-interactive --redirect
