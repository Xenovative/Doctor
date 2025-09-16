#!/bin/bash

# AI Doctor Matching System - Deployment Script
# Usage: ./deploy.sh [port] [host] [ai_provider]
# Example: ./deploy.sh 8081 0.0.0.0 openrouter

set -e  # Exit on any error

# Default values
DEFAULT_PORT=8081
DEFAULT_HOST="0.0.0.0"
DEFAULT_AI_PROVIDER="ollama"

# Parse command line arguments
PORT=${1:-$DEFAULT_PORT}
HOST=${2:-$DEFAULT_HOST}
AI_PROVIDER=${3:-$DEFAULT_AI_PROVIDER}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to start application in foreground
start_foreground() {
    echo ""
    echo -e "${GREEN}🚀 Starting the application...${NC}"
    echo -e "${BLUE}   Access URL: http://$HOST:$PORT${NC}"
    echo -e "${BLUE}   Admin Panel: http://$HOST:$PORT/admin${NC}"
    echo -e "${BLUE}   Profile Management: http://$HOST:$PORT/admin/profile${NC}"
    echo -e "${BLUE}   Bug Reports: http://$HOST:$PORT/admin/bug-reports${NC}"
    echo -e "${BLUE}   Analytics: http://$HOST:$PORT/admin/analytics${NC}"
    echo -e "${BLUE}   Health Check: http://$HOST:$PORT/health${NC}"
    echo -e "${BLUE}   AI Config: http://$HOST:$PORT/ai-config${NC}"
    echo ""
    echo -e "${YELLOW}🔐 Security Features:${NC}"
    echo -e "${YELLOW}   - 2FA authentication available${NC}"
    echo -e "${YELLOW}   - Tab-based permissions system${NC}"
    echo -e "${YELLOW}   - Secure admin profile management${NC}"
    echo ""
    
    # Start WhatsApp server if enabled
    if [[ $ENABLE_WHATSAPP =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}📱 Starting WhatsApp server with PM2...${NC}"
        
        # Create logs directory if it doesn't exist
        mkdir -p logs
        
        # Stop existing WhatsApp server process if running
        pm2 stop whatsapp-server 2>/dev/null || true
        pm2 delete whatsapp-server 2>/dev/null || true
        
        # Start WhatsApp server using PM2
        if pm2 start ecosystem.config.js --only whatsapp-server; then
            echo -e "${GREEN}✅ WhatsApp server started with PM2 on port 8086${NC}"
            echo -e "${BLUE}   Process name: whatsapp-server${NC}"
            echo -e "${BLUE}   View logs: pm2 logs whatsapp-server${NC}"
            echo -e "${YELLOW}   Please scan QR code (check PM2 logs for QR code)${NC}"
            echo ""
        else
            echo -e "${RED}❌ Failed to start WhatsApp server with PM2${NC}"
            echo -e "${YELLOW}   Falling back to direct start...${NC}"
            nohup node whatsapp-server.js > whatsapp-server.log 2>&1 &
            WHATSAPP_PID=$!
            sleep 3
            echo -e "${GREEN}✅ WhatsApp server started directly on port 8086 (PID: $WHATSAPP_PID)${NC}"
            echo ""
        fi
    fi
    
    echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
    echo ""
    
    # Start the application
    python app.py
}

# Function to setup systemd service
setup_systemd_service() {
    local SERVICE_NAME="ai-doctor-matching"
    local SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
    local CURRENT_DIR=$(pwd)
    local VENV_PATH="$CURRENT_DIR/venv"
    local APP_USER=${SUDO_USER:-$(whoami)}
    
    echo -e "${YELLOW}🔧 Creating systemd service...${NC}"
    
    # Create main service file
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=AI Doctor Matching System
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$CURRENT_DIR
Environment=PATH=$VENV_PATH/bin
EnvironmentFile=$CURRENT_DIR/.env
ExecStart=$VENV_PATH/bin/python app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    # Start WhatsApp server with PM2 if enabled
    if [[ $ENABLE_WHATSAPP =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}📱 Setting up WhatsApp server with PM2...${NC}"
        
        # Create logs directory
        mkdir -p logs
        
        # Stop existing processes
        pm2 stop whatsapp-server 2>/dev/null || true
        pm2 delete whatsapp-server 2>/dev/null || true
        
        # Start with PM2
        if pm2 start ecosystem.config.js --only whatsapp-server; then
            # Save PM2 process list and enable startup
            pm2 save
            pm2 startup systemd -u $APP_USER --hp $(eval echo ~$APP_USER)
            echo -e "${GREEN}✅ WhatsApp server configured with PM2${NC}"
            echo -e "${BLUE}   PM2 will auto-start WhatsApp server on boot${NC}"
        else
            echo -e "${RED}❌ Failed to setup WhatsApp server with PM2${NC}"
        fi
    fi
    
    # Set proper permissions
    chmod 644 "$SERVICE_FILE"
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    
    echo -e "${GREEN}✅ Main service created: $SERVICE_NAME${NC}"
    echo -e "${BLUE}Service commands:${NC}"
    echo -e "  Start:   systemctl start $SERVICE_NAME"
    echo -e "  Stop:    systemctl stop $SERVICE_NAME"
    echo -e "  Status:  systemctl status $SERVICE_NAME"
    echo -e "  Logs:    journalctl -u $SERVICE_NAME -f"
    
    if [[ $ENABLE_WHATSAPP =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}WhatsApp PM2 commands:${NC}"
        echo -e "  Status:  pm2 status whatsapp-server"
        echo -e "  Logs:    pm2 logs whatsapp-server"
        echo -e "  Restart: pm2 restart whatsapp-server"
        echo -e "  Stop:    pm2 stop whatsapp-server"
    fi
    echo ""
    
    # Ask if user wants to start the service now
    read -p "Start the service now? (Y/n): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        systemctl start "$SERVICE_NAME"
        sleep 2
        
        # Check service status
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            echo -e "${GREEN}✅ Service started successfully!${NC}"
            echo -e "${BLUE}   Access URL: http://$HOST:$PORT${NC}"
            echo -e "${BLUE}   Admin Panel: http://$HOST:$PORT/admin${NC}"
            echo -e "${BLUE}   Health Check: http://$HOST:$PORT/health${NC}"
            echo -e "${BLUE}   AI Config: http://$HOST:$PORT/ai-config${NC}"
            echo ""
            echo -e "${YELLOW}Check logs with: journalctl -u $SERVICE_NAME -f${NC}"
        else
            echo -e "${RED}❌ Service failed to start. Check logs:${NC}"
            echo -e "${YELLOW}journalctl -u $SERVICE_NAME -n 20${NC}"
        fi
    else
        echo -e "${YELLOW}Service created but not started. Use: systemctl start $SERVICE_NAME${NC}"
    fi
}

echo -e "${BLUE}🏥 AI Doctor Matching System - Deployment Script v3.0${NC}"
echo -e "${BLUE}======================================================${NC}"
echo ""
echo -e "Latest Features:"
echo -e "  - Complete 2FA system with Google Authenticator"
echo -e "  - Fine-grained admin tab permissions"
echo -e "  - Enhanced bug reporting with image upload"
echo -e "  - Improved WhatsApp integration"
echo -e "  - Advanced analytics and user management"
echo -e "  - Profile management system"
echo -e "  - Database migration tools"
echo -e "  - Python 3.11 compatibility check"
echo ""
echo -e "Configuration:"
echo -e "  Port: ${GREEN}$PORT${NC}"
echo -e "  Host: ${GREEN}$HOST${NC}"
echo -e "  AI Provider: ${GREEN}$AI_PROVIDER${NC}"
echo ""

# Check if Python is installed and version compatibility
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 is not installed. Please install Python 3.8-3.11 first.${NC}"
    exit 1
fi

# Check Python version compatibility (must be 3.11 or lower)
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}✅ Python version: $PYTHON_VERSION${NC}"

# Extract major and minor version numbers
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -gt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -gt 11 ]); then
    echo -e "${RED}❌ Python version $PYTHON_VERSION is not supported. Please use Python 3.8-3.11.${NC}"
    echo -e "${YELLOW}   This application requires Python 3.11 or lower for compatibility.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python version $PYTHON_VERSION is compatible${NC}"

# Check if Node.js is installed (for WhatsApp server)
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed. Please install Node.js 16+ for WhatsApp functionality.${NC}"
    echo -e "${YELLOW}   Download from: https://nodejs.org${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Node.js is installed${NC}"
fi

echo -e "${YELLOW}📦 Setting up virtual environment...${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3.11 -m venv venv
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Virtual environment created${NC}"
    else
        echo -e "${RED}❌ Failed to create virtual environment${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo -e "${RED}❌ Virtual environment activation script not found${NC}"
    echo -e "${YELLOW}Trying to recreate virtual environment...${NC}"
    rm -rf venv
    python3.11 -m venv venv
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}❌ Failed to create working virtual environment${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✅ Virtual environment activated${NC}"

# Upgrade pip
echo -e "${YELLOW}📦 Upgrading pip...${NC}"
pip install --upgrade pip

# Install requirements
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Python dependencies installed${NC}"
else
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
fi

# Install Node.js dependencies for WhatsApp server
echo -e "${YELLOW}📦 Installing Node.js dependencies...${NC}"
if [ -f "package.json" ]; then
    npm install
    echo -e "${GREEN}✅ Node.js dependencies installed${NC}"
    
    # Install PM2 globally if not already installed
    if ! command -v pm2 &> /dev/null; then
        echo -e "${YELLOW}📦 Installing PM2 process manager...${NC}"
        npm install -g pm2
        echo -e "${GREEN}✅ PM2 installed globally${NC}"
    else
        echo -e "${GREEN}✅ PM2 is already installed${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  package.json not found - WhatsApp functionality may not work${NC}"
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${BLUE}⚙️ Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ .env file created from template${NC}"
    echo -e "${YELLOW}⚠️ Please edit .env file with your API keys if using OpenRouter${NC}"
fi

# Prompt for admin credentials if not set
echo ""
echo -e "${BLUE}👤 Admin Account Configuration${NC}"
echo "================================"

# Only prompt for admin username if not set
if [ -z "${ADMIN_USERNAME:-}" ]; then
    read -p "Enter admin username (default: admin): " ADMIN_NAME
    ADMIN_NAME=${ADMIN_NAME:-admin}
else
    ADMIN_NAME="$ADMIN_USERNAME"
    echo -e "${GREEN}✅ Using existing admin username from environment: $ADMIN_NAME${NC}"
fi

# Only prompt for admin password if not set
if [ -z "${ADMIN_PASSWORD:-}" ]; then
    while true; do
        read -s -p "Enter admin password (minimum 6 characters): " ADMIN_PASSWORD
        echo ""
        if [ ${#ADMIN_PASSWORD} -lt 6 ]; then
            echo -e "${RED}❌ Password must be at least 6 characters${NC}"
            continue
        fi
        # Ask to confirm password
        read -s -p "Confirm admin password: " ADMIN_PASSWORD_CONFIRM
        echo ""
        if [ "$ADMIN_PASSWORD" != "$ADMIN_PASSWORD_CONFIRM" ]; then
            echo -e "${RED}❌ Passwords do not match${NC}"
            continue
        fi
        break
    done
    echo -e "${GREEN}✅ Admin credentials configured: $ADMIN_NAME${NC}"
else
    echo -e "${GREEN}✅ Using existing admin password from environment${NC}"
fi
echo ""

# Load existing .env file if it exists
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ Loading existing .env file${NC}"
    # Export all variables from .env file
    set -a
    source .env
    set +a
fi

# Set environment variables with fallbacks
export AI_PROVIDER=${AI_PROVIDER:-$DEFAULT_AI_PROVIDER}
export FLASK_HOST=${FLASK_HOST:-$HOST}
export FLASK_PORT=${FLASK_PORT:-$PORT}

# Update .env file with current settings
echo -e "${YELLOW}⚙️  Updating configuration...${NC}"
# Create backup of existing .env
cp -f .env .env.bak 2>/dev/null || true

# Update or add variables in .env
update_env_var() {
    local var_name=$1
    local var_value=$2
    if grep -q "^$var_name=" .env 2>/dev/null; then
        # Variable exists, update it
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # MacOS/BSD sed requires different syntax
            sed -i '' "s/^$var_name=.*/$var_name=$var_value/" .env
        else
            sed -i "s/^$var_name=.*/$var_name=$var_value/" .env
        fi
    else
        # Variable doesn't exist, add it
        echo "$var_name=$var_value" >> .env
    fi
}

# Update or add variables
update_env_var "AI_PROVIDER" "$AI_PROVIDER"
update_env_var "ADMIN_USERNAME" "${ADMIN_NAME:-admin}"
update_env_var "ADMIN_PASSWORD" "${ADMIN_PASSWORD:-}"
update_env_var "FLASK_HOST" "$FLASK_HOST"
update_env_var "FLASK_PORT" "$FLASK_PORT"

# Configure WhatsApp settings
echo ""
echo -e "${BLUE}📱 WhatsApp Configuration${NC}"
echo "========================"

# Check if WhatsApp is already configured via environment variables
if [ -n "${WHATSAPP_TARGET_NUMBER:-}" ] && [ "${WHATSAPP_ENABLED:-false}" = "true" ]; then
    echo -e "${GREEN}✅ Using existing WhatsApp configuration from environment${NC}"
    echo -e "   Target number: $WHATSAPP_TARGET_NUMBER"
    update_env_var "WHATSAPP_ENABLED" "true"
    update_env_var "WHATSAPP_TARGET_NUMBER" "$WHATSAPP_TARGET_NUMBER"
else
    # Only prompt if not configured via environment
    read -p "Enable WhatsApp notifications? (y/N): " -n 1 -r ENABLE_WHATSAPP
    echo ""
    if [[ $ENABLE_WHATSAPP =~ ^[Yy]$ ]]; then
        while true; do
            read -p "Enter target WhatsApp number (format: 852XXXXXXXX@c.us): " WHATSAPP_NUMBER
            if [ -z "$WHATSAPP_NUMBER" ]; then
                echo -e "${RED}❌ WhatsApp number cannot be empty${NC}"
                continue
            fi
            # Basic validation for WhatsApp number format
            if [[ ! $WHATSAPP_NUMBER =~ ^[0-9]+@[a-z0-9.]+$ ]]; then
                echo -e "${YELLOW}⚠️  Invalid format. Expected format: 852XXXXXXXX@c.us${NC}"
                continue
            fi
            break
        done
        
        update_env_var "WHATSAPP_ENABLED" "true"
        update_env_var "WHATSAPP_TARGET_NUMBER" "$WHATSAPP_NUMBER"
        echo -e "${GREEN}✅ WhatsApp notifications enabled for $WHATSAPP_NUMBER${NC}"
    else
        update_env_var "WHATSAPP_ENABLED" "false"
        echo -e "${YELLOW}⚠️  WhatsApp notifications disabled${NC}"
    fi
fi

# Check AI provider setup
echo -e "${YELLOW}🤖 Checking AI provider setup...${NC}"
if [ "$AI_PROVIDER" = "openrouter" ]; then
    if [ -z "$OPENROUTER_API_KEY" ]; then
        echo -e "${YELLOW}⚠️  OpenRouter selected but OPENROUTER_API_KEY not set${NC}"
        echo -e "${YELLOW}   Please set it in .env file or as environment variable${NC}"
    else
        echo -e "${GREEN}✅ OpenRouter API key found${NC}"
    fi
elif [ "$AI_PROVIDER" = "openai" ]; then
    if [ -z "$OPENAI_API_KEY" ]; then
        echo -e "${YELLOW}⚠️  OpenAI selected but OPENAI_API_KEY not set${NC}"
        echo -e "${YELLOW}   Please set it in .env file or as environment variable${NC}"
    else
        echo -e "${GREEN}✅ OpenAI API key found${NC}"
    fi
elif [ "$AI_PROVIDER" = "ollama" ]; then
    if command -v ollama &> /dev/null; then
        echo -e "${GREEN}✅ Ollama is installed${NC}"
        # Check if Ollama is running
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Ollama service is running${NC}"
        else
            echo -e "${YELLOW}⚠️  Ollama service is not running${NC}"
            echo -e "${YELLOW}   Please start it with: ollama serve${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Ollama is not installed${NC}"
        echo -e "${YELLOW}   Please install it from: https://ollama.ai${NC}"
    fi
fi

# Check if doctors data exists
if [ -f "assets/finddoc_doctors_detailed 2.csv" ]; then
    echo -e "${GREEN}✅ Doctors database found${NC}"
elif [ -f "assets/finddoc_doctors_detailed_full_20250905.csv" ]; then
    echo -e "${GREEN}✅ Doctors database found (full version)${NC}"
else
    echo -e "${YELLOW}⚠️  Doctors database not found${NC}"
    echo -e "${YELLOW}   Expected locations:${NC}"
    echo -e "${YELLOW}     - assets/finddoc_doctors_detailed 2.csv${NC}"
    echo -e "${YELLOW}     - assets/finddoc_doctors_detailed_full_20250905.csv${NC}"
fi

# Check for database migration scripts
echo -e "${YELLOW}📊 Checking database migration tools...${NC}"
if [ -f "migrate_2fa_columns.py" ]; then
    echo -e "${GREEN}✅ 2FA migration script found${NC}"
else
    echo -e "${YELLOW}⚠️  2FA migration script missing${NC}"
fi

if [ -f "add_tab_permissions_column.py" ]; then
    echo -e "${GREEN}✅ Tab permissions migration script found${NC}"
else
    echo -e "${YELLOW}⚠️  Tab permissions migration script missing${NC}"
fi

# Check for static assets
if [ -d "static" ]; then
    echo -e "${GREEN}✅ Static assets directory found${NC}"
else
    echo -e "${YELLOW}⚠️  Static assets directory missing${NC}"
fi

if [ -d "templates" ]; then
    echo -e "${GREEN}✅ Templates directory found${NC}"
else
    echo -e "${RED}❌ Templates directory missing - application will not work${NC}"
    exit 1
fi

# Check if running as root or with sudo (typical for web servers)
if [ "$EUID" -eq 0 ] || [ -n "$SUDO_USER" ]; then
    echo -e "${YELLOW}🔧 Detected elevated privileges (web server environment)${NC}"
    echo -e "${YELLOW}Would you like to set up this application as a system service?${NC}"
    echo -e "${BLUE}This will:${NC}"
    echo -e "  - Create a systemd service file"
    echo -e "  - Enable auto-start on boot"
    echo -e "  - Run as a daemon in the background"
    echo ""
    read -p "Setup as service? (y/N): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_systemd_service
    else
        echo -e "${YELLOW}Skipping service setup. Starting in foreground mode...${NC}"
        start_foreground
    fi
else
    echo -e "${YELLOW}Running in development mode${NC}"
    start_foreground
fi
