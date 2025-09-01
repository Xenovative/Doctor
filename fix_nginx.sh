#!/bin/bash

# Create custom Nginx config that overrides HestiaCP
sudo tee /etc/nginx/conf.d/99-doctor-ai-override.conf > /dev/null <<'EOL'
# Override configuration for app.doctor-ai.io
server {
    listen 80;
    server_name app.doctor-ai.io www.app.doctor-ai.io;
    return 301 https://app.doctor-ai.io$request_uri;
}

server {
    listen 443 ssl http2;
    server_name app.doctor-ai.io;
    
    # Use existing SSL certificates if available
    ssl_certificate /etc/letsencrypt/live/app.doctor-ai.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.doctor-ai.io/privkey.pem;
    
    # Fallback to self-signed if Let's Encrypt not available
    ssl_certificate /etc/ssl/certs/ssl-cert-snakeoil.pem;
    ssl_certificate_key /etc/ssl/private/ssl-cert-snakeoil.key;

    location / {
        proxy_pass http://127.0.0.1:7001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }
}

# Redirect www to non-www
server {
    listen 443 ssl http2;
    server_name www.app.doctor-ai.io;
    
    ssl_certificate /etc/letsencrypt/live/app.doctor-ai.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.doctor-ai.io/privkey.pem;
    
    # Fallback to self-signed
    ssl_certificate /etc/ssl/certs/ssl-cert-snakeoil.pem;
    ssl_certificate_key /etc/ssl/private/ssl-cert-snakeoil.key;
    
    return 301 https://app.doctor-ai.io$request_uri;
}
EOL

# Test and reload Nginx
sudo nginx -t && sudo systemctl reload nginx

echo "✅ Nginx configuration updated"
echo "🔗 Your app should now be accessible at https://app.doctor-ai.io"
