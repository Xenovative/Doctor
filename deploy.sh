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
    echo -e "${BLUE}   Health Check: http://$HOST:$PORT/health${NC}"
    echo -e "${BLUE}   AI Config: http://$HOST:$PORT/ai-config${NC}"
    echo ""
    
    # Start WhatsApp server if enabled
    if [[ $ENABLE_WHATSAPP =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}📱 Starting WhatsApp server...${NC}"
        nohup npm start > whatsapp-server.log 2>&1 &
        WHATSAPP_PID=$!
        sleep 3
        echo -e "${GREEN}✅ WhatsApp server started on port 8085 (PID: $WHATSAPP_PID)${NC}"
        echo -e "${YELLOW}   Please scan QR code - check whatsapp-server.log for details${NC}"
        echo ""
    fi
    
    echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
    echo ""
    
    # Start the application
    python app.py
}

# Function to setup systemd service
setup_systemd_service() {
    local SERVICE_NAME="ai-doctor-matching"
    local WHATSAPP_SERVICE_NAME="ai-doctor-whatsapp"
    local SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
    local WHATSAPP_SERVICE_FILE="/etc/systemd/system/${WHATSAPP_SERVICE_NAME}.service"
    local CURRENT_DIR=$(pwd)
    local VENV_PATH="$CURRENT_DIR/venv"
    local APP_USER=${SUDO_USER:-$(whoami)}
    
    echo -e "${YELLOW}🔧 Creating systemd services...${NC}"
    
    # Create main service file
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=AI Doctor Matching System
After=network.target
Wants=ai-doctor-whatsapp.service

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

    # Create WhatsApp service file if enabled
    if [[ $ENABLE_WHATSAPP =~ ^[Yy]$ ]]; then
        cat > "$WHATSAPP_SERVICE_FILE" << EOF
[Unit]
Description=AI Doctor WhatsApp Server
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$CURRENT_DIR
EnvironmentFile=$CURRENT_DIR/.env
ExecStart=/usr/bin/node whatsapp-server.js
Restart=always
RestartSec=5
StandardOutput=append:$CURRENT_DIR/whatsapp-server.log
StandardError=append:$CURRENT_DIR/whatsapp-server.log

[Install]
WantedBy=multi-user.target
EOF
        
        # Set proper permissions for WhatsApp service
        chmod 644 "$WHATSAPP_SERVICE_FILE"
        systemctl daemon-reload
        systemctl enable "$WHATSAPP_SERVICE_NAME"
        echo -e "${GREEN}✅ WhatsApp service created: $WHATSAPP_SERVICE_NAME${NC}"
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
        echo -e "${BLUE}WhatsApp service commands:${NC}"
        echo -e "  Start:   systemctl start $WHATSAPP_SERVICE_NAME"
        echo -e "  Stop:    systemctl stop $WHATSAPP_SERVICE_NAME"
        echo -e "  Status:  systemctl status $WHATSAPP_SERVICE_NAME"
        echo -e "  Logs:    journalctl -u $WHATSAPP_SERVICE_NAME -f"
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

echo -e "${BLUE}🏥 AI Doctor Matching System - Deployment Script v2.0${NC}"
echo -e "${BLUE}======================================================${NC}"
echo ""
echo -e "New Features:"
echo -e "  - Enhanced AI error handling"
echo -e "  - Selective analytics export"
echo -e "  - Improved admin dashboard"
echo -e "  - UTF-8 support for international data"
echo ""
echo -e "Configuration:"
echo -e "  Port: ${GREEN}$PORT${NC}"
echo -e "  Host: ${GREEN}$HOST${NC}"
echo -e "  AI Provider: ${GREEN}$AI_PROVIDER${NC}"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 is not installed. Please install Python 3.8+ first.${NC}"
    exit 1
fi

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
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate
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

# Prompt for admin credentials
echo ""
echo -e "${BLUE}👤 Admin Account Configuration${NC}"
echo "================================"
read -p "Enter admin username (default: admin): " ADMIN_NAME
ADMIN_NAME=${ADMIN_NAME:-admin}

while true; do
    read -s -p "Enter admin password (minimum 6 characters): " ADMIN_PASSWORD
    echo ""
    if [ ${#ADMIN_PASSWORD} -lt 6 ]; then
        echo -e "${RED}❌ Password must be at least 6 characters${NC}"
        continue
    fi
    break
done

echo -e "${GREEN}✅ Admin credentials configured: $ADMIN_NAME${NC}"
echo ""

# Set environment variables
export AI_PROVIDER=$AI_PROVIDER
export FLASK_HOST=$HOST
export FLASK_PORT=$PORT

# Update .env file with current settings
echo -e "${YELLOW}⚙️  Updating configuration...${NC}"
sed -i.bak "s/^AI_PROVIDER=.*/AI_PROVIDER=$AI_PROVIDER/" .env
sed -i.bak "s/^ADMIN_USERNAME=.*/ADMIN_USERNAME=$ADMIN_NAME/" .env
sed -i.bak "s/^ADMIN_PASSWORD=.*/ADMIN_PASSWORD=$ADMIN_PASSWORD/" .env
echo "FLASK_HOST=$HOST" >> .env
echo "FLASK_PORT=$PORT" >> .env

# Configure WhatsApp settings
echo ""
echo -e "${BLUE}📱 WhatsApp Configuration${NC}"
echo "========================"
read -p "Enable WhatsApp notifications? (y/N): " -n 1 -r ENABLE_WHATSAPP
echo ""
if [[ $ENABLE_WHATSAPP =~ ^[Yy]$ ]]; then
    read -p "Enter target WhatsApp number (format: 852XXXXXXXX@c.us): " WHATSAPP_NUMBER
    if [ -z "$WHATSAPP_NUMBER" ]; then
        echo -e "${RED}❌ WhatsApp number cannot be empty${NC}"
        ENABLE_WHATSAPP="n"
    else
        sed -i.bak "s/^WHATSAPP_ENABLED=.*/WHATSAPP_ENABLED=true/" .env
        sed -i.bak "s/^WHATSAPP_TARGET_NUMBER=.*/WHATSAPP_TARGET_NUMBER=$WHATSAPP_NUMBER/" .env
        echo -e "${GREEN}✅ WhatsApp notifications enabled for $WHATSAPP_NUMBER${NC}"
    fi
else
    sed -i.bak "s/^WHATSAPP_ENABLED=.*/WHATSAPP_ENABLED=false/" .env
    echo -e "${YELLOW}⚠️  WhatsApp notifications disabled${NC}"
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
else
    echo -e "${YELLOW}⚠️  Doctors database not found at assets/finddoc_doctors_detailed 2.csv${NC}"
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
