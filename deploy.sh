#!/bin/bash

# AI Doctor Matching System - Server Deployment Script
# Usage: ./deploy.sh [production|staging] [ollama|openrouter]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${1:-production}
AI_PROVIDER=${2:-ollama}
APP_NAME="ai-doctor-matching"
APP_PORT=${PORT:-8081}
APP_USER="doctor-app"
APP_DIR="/opt/${APP_NAME}"
SERVICE_NAME="${APP_NAME}"
DOMAIN=""

echo -e "${BLUE}🚀 AI Doctor Matching System Deployment Script${NC}"
echo -e "${BLUE}Environment: ${ENVIRONMENT}${NC}"
echo -e "${BLUE}AI Provider: ${AI_PROVIDER}${NC}"
echo ""

# Function to print colored output
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root for security reasons"
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is not installed"
        exit 1
    fi
    
    # Check git
    if ! command -v git &> /dev/null; then
        log_error "git is not installed"
        exit 1
    fi
    
    # Check nginx (optional)
    if ! command -v nginx &> /dev/null; then
        log_warn "nginx is not installed - will run without reverse proxy"
    fi
    
    log_info "System requirements check passed ✓"
}

# Create application user
create_app_user() {
    if ! id "$APP_USER" &>/dev/null; then
        log_info "Creating application user: $APP_USER"
        sudo useradd --system --shell /bin/bash --home-dir $APP_DIR --create-home $APP_USER
    else
        log_info "Application user $APP_USER already exists ✓"
    fi
}

# Setup application directory
setup_app_directory() {
    log_info "Setting up application directory: $APP_DIR"
    
    sudo mkdir -p $APP_DIR
    sudo chown $APP_USER:$APP_USER $APP_DIR
    
    # Copy application files
    log_info "Copying application files..."
    sudo -u $APP_USER cp -r . $APP_DIR/
    
    # Set proper permissions
    sudo chown -R $APP_USER:$APP_USER $APP_DIR
    sudo chmod +x $APP_DIR/app.py
}

# Install Python dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."
    
    # Create virtual environment
    sudo -u $APP_USER python3 -m venv $APP_DIR/venv
    
    # Install dependencies
    sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip
    sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt
    
    # Install production dependencies
    sudo -u $APP_USER $APP_DIR/venv/bin/pip install gunicorn supervisor
    
    log_info "Dependencies installed ✓"
}

# Setup Ollama (if selected)
setup_ollama() {
    if [[ "$AI_PROVIDER" == "ollama" ]]; then
        log_info "Setting up Ollama..."
        
        # Install Ollama
        if ! command -v ollama &> /dev/null; then
            log_info "Installing Ollama..."
            curl -fsSL https://ollama.ai/install.sh | sh
        else
            log_info "Ollama already installed ✓"
        fi
        
        # Start Ollama service
        sudo systemctl enable ollama
        sudo systemctl start ollama
        
        # Pull the model
        log_info "Pulling Ollama model..."
        sudo -u $APP_USER ollama pull llama3.1:8b
        
        log_info "Ollama setup complete ✓"
    fi
}

# Create environment file
create_env_file() {
    log_info "Creating environment configuration..."
    
    ENV_FILE="$APP_DIR/.env"
    sudo -u $APP_USER cat > $ENV_FILE << EOF
# Environment Configuration
FLASK_ENV=$ENVIRONMENT
PORT=$APP_PORT

# AI Configuration
AI_PROVIDER=$AI_PROVIDER

# Ollama Configuration
OLLAMA_MODEL=llama3.1:8b

# OpenRouter Configuration (set these if using OpenRouter)
OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-}
OPENROUTER_MODEL=${OPENROUTER_MODEL:-anthropic/claude-3.5-sonnet}
OPENROUTER_MAX_TOKENS=${OPENROUTER_MAX_TOKENS:-4000}
EOF

    if [[ "$AI_PROVIDER" == "openrouter" ]]; then
        if [[ -z "$OPENROUTER_API_KEY" ]]; then
            log_warn "OPENROUTER_API_KEY not set. Please set it in $ENV_FILE"
        fi
    fi
    
    sudo chown $APP_USER:$APP_USER $ENV_FILE
    sudo chmod 600 $ENV_FILE
    
    log_info "Environment file created ✓"
}

# Create systemd service
create_systemd_service() {
    log_info "Creating systemd service..."
    
    sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << EOF
[Unit]
Description=AI Doctor Matching System
After=network.target

[Service]
Type=exec
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn --bind 0.0.0.0:$APP_PORT --workers 4 --timeout 120 app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME
    
    log_info "Systemd service created ✓"
}

# Prompt for domain name
prompt_domain() {
    echo ""
    log_info "Setting up domain configuration..."
    
    # Check if domain is already set via environment variable
    if [[ -z "$DOMAIN" ]]; then
        echo -e "${YELLOW}Please enter your domain name (or press Enter for localhost):${NC}"
        read -p "Domain: " user_domain
        
        if [[ -n "$user_domain" ]]; then
            DOMAIN="$user_domain"
        else
            DOMAIN="localhost"
        fi
    fi
    
    log_info "Using domain: $DOMAIN"
}

# Setup nginx reverse proxy
setup_nginx() {
    if command -v nginx &> /dev/null; then
        log_info "Setting up nginx reverse proxy..."
        
        sudo tee /etc/nginx/sites-available/$APP_NAME > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    client_max_body_size 50M;
    
    location / {
        proxy_pass http://127.0.0.1:$APP_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
    
    location /static {
        alias $APP_DIR/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

        # Enable site
        sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
        
        # Test nginx configuration
        sudo nginx -t
        
        # Reload nginx
        sudo systemctl reload nginx
        
        log_info "Nginx setup complete ✓"
    else
        log_warn "Nginx not installed - skipping reverse proxy setup"
    fi
}

# Setup firewall
setup_firewall() {
    if command -v ufw &> /dev/null; then
        log_info "Configuring firewall..."
        
        sudo ufw allow ssh
        sudo ufw allow 80/tcp
        sudo ufw allow 443/tcp
        
        if [[ "$AI_PROVIDER" == "ollama" ]]; then
            sudo ufw allow 11434/tcp  # Ollama port
        fi
        
        # Enable firewall if not already enabled
        sudo ufw --force enable
        
        log_info "Firewall configured ✓"
    else
        log_warn "UFW not installed - skipping firewall setup"
    fi
}

# Create backup script
create_backup_script() {
    log_info "Creating backup script..."
    
    sudo tee /usr/local/bin/backup-${APP_NAME} > /dev/null << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/ai-doctor-matching"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/opt/ai-doctor-matching"

mkdir -p $BACKUP_DIR

# Backup application files
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz -C $APP_DIR .

# Keep only last 7 backups
find $BACKUP_DIR -name "app_backup_*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/app_backup_$DATE.tar.gz"
EOF

    sudo chmod +x /usr/local/bin/backup-${APP_NAME}
    
    # Add to crontab for daily backups
    (sudo crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup-${APP_NAME}") | sudo crontab -
    
    log_info "Backup script created ✓"
}

# Start services
start_services() {
    log_info "Starting services..."
    
    # Start application
    sudo systemctl start $SERVICE_NAME
    
    # Check status
    if sudo systemctl is-active --quiet $SERVICE_NAME; then
        log_info "Application service started ✓"
    else
        log_error "Failed to start application service"
        sudo systemctl status $SERVICE_NAME
        exit 1
    fi
    
    # Wait a moment for service to fully start
    sleep 5
    
    # Test application
    if curl -f http://localhost:$APP_PORT/health > /dev/null 2>&1; then
        log_info "Application health check passed ✓"
    else
        log_warn "Application health check failed - check logs"
    fi
}

# Show deployment summary
show_summary() {
    echo ""
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}Application Details:${NC}"
    echo "  • Service: $SERVICE_NAME"
    echo "  • Directory: $APP_DIR"
    echo "  • Port: $APP_PORT"
    echo "  • AI Provider: $AI_PROVIDER"
    echo ""
    echo -e "${BLUE}Useful Commands:${NC}"
    echo "  • Check status: sudo systemctl status $SERVICE_NAME"
    echo "  • View logs: sudo journalctl -u $SERVICE_NAME -f"
    echo "  • Restart: sudo systemctl restart $SERVICE_NAME"
    echo "  • Backup: sudo /usr/local/bin/backup-${APP_NAME}"
    echo ""
    echo -e "${BLUE}URLs:${NC}"
    if [[ "$DOMAIN" != "localhost" ]] && command -v nginx &> /dev/null; then
        echo "  • Application: http://$DOMAIN"
        echo "  • Health Check: http://$DOMAIN/health"
        echo "  • AI Config: http://$DOMAIN/ai-config"
        echo "  • Direct Access: http://localhost:$APP_PORT"
    else
        echo "  • Application: http://localhost:$APP_PORT"
        echo "  • Health Check: http://localhost:$APP_PORT/health"
        echo "  • AI Config: http://localhost:$APP_PORT/ai-config"
    fi
    echo ""
    
    if [[ "$AI_PROVIDER" == "openrouter" ]] && [[ -z "$OPENROUTER_API_KEY" ]]; then
        echo -e "${YELLOW}⚠️  Don't forget to set OPENROUTER_API_KEY in $APP_DIR/.env${NC}"
        echo ""
    fi
}

# Main deployment function
main() {
    log_info "Starting deployment process..."
    
    check_root
    check_requirements
    prompt_domain
    create_app_user
    setup_app_directory
    install_dependencies
    setup_ollama
    create_env_file
    create_systemd_service
    setup_nginx
    setup_firewall
    create_backup_script
    start_services
    show_summary
}

# Run main function
main "$@"
