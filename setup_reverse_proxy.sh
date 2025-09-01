#!/bin/bash

# Update package lists
sudo apt update

# Install Nginx
sudo apt install -y nginx

# Install Certbot and Nginx plugin
sudo apt install -y certbot python3-certbot-nginx

# Create Nginx config for your domain
DOMAIN="yourdomain.com"
UPSTREAM_PORT=7001  # Your app's port

# Create Nginx config
sudo tee /etc/nginx/sites-available/$DOMAIN > /dev/null <<EOL
server {
    listen 443 ssl http2;
    server_name app.doctor-ai.io;
    
    ssl_certificate /path/to/ssl/certificate.pem;
    ssl_certificate_key /path/to/ssl/private.key;

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

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
}

# Redirect www to non-www
server {
    listen 443 ssl http2;
    server_name www.app.doctor-ai.io;
    return 301 https://app.doctor-ai.io$request_uri;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name app.doctor-ai.io www.app.doctor-ai.io;
    return 301 https://app.doctor-ai.io$request_uri;
}
}
EOL

# Enable the site
sudo ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

# Set up SSL with Let's Encrypt
echo "Please enter your email for Let's Encrypt:"
read EMAIL

sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos -m $EMAIL

# Set up automatic renewal
echo "0 0,12 * * * root python3 -c 'import random; import time; time.sleep(random.random() * 3600)' && certbot renew -q" | sudo tee -a /etc/crontab > /dev/null

echo "Reverse proxy with SSL has been set up successfully!"
echo "Your application is now accessible at https://$DOMAIN"
