#!/bin/bash

# AI Doctor Matching System - Installation Script
# This script sets up the virtual environment and configures the application

set -e  # Exit on any error

echo "🏥 AI Doctor Matching System - Installation Script"
echo "=================================================="

# Configuration variables
DEFAULT_PORT=8081
DEFAULT_HOST="0.0.0.0"
DEFAULT_AI_PROVIDER="ollama"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check if Python is installed
check_python() {
    print_header "Checking Python installation..."
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        print_status "Python3 found: $(python3 --version)"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
        print_status "Python found: $(python --version)"
    else
        print_error "Python is not installed. Please install Python 3.8+ first."
        exit 1
    fi
}

# Create virtual environment
create_venv() {
    print_header "Creating virtual environment..."
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Removing old one..."
        rm -rf venv
    fi
    
    $PYTHON_CMD -m venv venv
    print_status "Virtual environment created successfully"
}

# Activate virtual environment
activate_venv() {
    print_header "Activating virtual environment..."
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    print_status "Virtual environment activated"
}

# Install dependencies
install_dependencies() {
    print_header "Installing Python dependencies..."
    pip install --upgrade pip
    
    # Fix numpy/pandas compatibility issues
    print_status "Installing numpy first to avoid compatibility issues..."
    pip uninstall -y numpy pandas 2>/dev/null || true
    pip install numpy==1.24.3
    pip install pandas==2.0.3
    
    # Install remaining dependencies
    pip install -r requirements.txt
    print_status "Dependencies installed successfully"
}

# Get user configuration
get_user_config() {
    print_header "Configuration Setup"
    
    # Port configuration
    echo -n "Enter port number (default: $DEFAULT_PORT): "
    read PORT
    PORT=${PORT:-$DEFAULT_PORT}
    
    # Host configuration
    echo -n "Enter host/domain (default: $DEFAULT_HOST): "
    read HOST
    HOST=${HOST:-$DEFAULT_HOST}
    
    # AI Provider configuration
    echo -n "Choose AI provider (ollama/openrouter, default: $DEFAULT_AI_PROVIDER): "
    read AI_PROVIDER
    AI_PROVIDER=${AI_PROVIDER:-$DEFAULT_AI_PROVIDER}
    
    if [ "$AI_PROVIDER" = "openrouter" ]; then
        echo -n "Enter OpenRouter API Key: "
        read -s OPENROUTER_API_KEY
        echo
        echo -n "Enter OpenRouter Model (default: anthropic/claude-3.5-sonnet): "
        read OPENROUTER_MODEL
        OPENROUTER_MODEL=${OPENROUTER_MODEL:-"anthropic/claude-3.5-sonnet"}
    fi
    
    if [ "$AI_PROVIDER" = "ollama" ]; then
        echo -n "Enter Ollama Model (default: llama3.1:8b): "
        read OLLAMA_MODEL
        OLLAMA_MODEL=${OLLAMA_MODEL:-"llama3.1:8b"}
    fi
}

# Create environment file
create_env_file() {
    print_header "Creating environment configuration..."
    
    cat > .env << EOF
# AI Provider Configuration
AI_PROVIDER=$AI_PROVIDER

# Server Configuration
HOST=$HOST
PORT=$PORT

EOF

    if [ "$AI_PROVIDER" = "openrouter" ]; then
        cat >> .env << EOF
# OpenRouter Configuration
OPENROUTER_API_KEY=$OPENROUTER_API_KEY
OPENROUTER_MODEL=$OPENROUTER_MODEL
OPENROUTER_MAX_TOKENS=4000

EOF
    fi
    
    if [ "$AI_PROVIDER" = "ollama" ]; then
        cat >> .env << EOF
# Ollama Configuration
OLLAMA_MODEL=$OLLAMA_MODEL

EOF
    fi
    
    print_status "Environment file created: .env"
}

# Update app.py to use environment variables for host and port
update_app_config() {
    print_header "Updating application configuration..."
    
    # Create a simple launcher script
    cat > launch.py << 'EOF'
#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the main app
from app import app

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8081))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    print(f"Starting server on {host}:{port}")
    app.run(debug=debug, host=host, port=port)
EOF
    
    print_status "Launch script created: launch.py"
}

# Create startup scripts
create_startup_scripts() {
    print_header "Creating startup scripts..."
    
    # Unix startup script
    cat > start.sh << EOF
#!/bin/bash
source venv/bin/activate
python launch.py
EOF
    chmod +x start.sh
    
    # Windows startup script
    cat > start.bat << EOF
@echo off
call venv\\Scripts\\activate
python launch.py
pause
EOF
    
    print_status "Startup scripts created: start.sh and start.bat"
}

# Install python-dotenv if not in requirements
install_dotenv() {
    print_header "Installing python-dotenv..."
    pip install python-dotenv
    print_status "python-dotenv installed"
}

# Main installation process
main() {
    print_header "Starting installation process..."
    
    check_python
    create_venv
    activate_venv
    install_dependencies
    install_dotenv
    get_user_config
    create_env_file
    update_app_config
    create_startup_scripts
    
    print_header "Installation completed successfully! 🎉"
    echo
    print_status "To start the application:"
    echo "  Unix/Linux/macOS: ./start.sh"
    echo "  Windows: start.bat"
    echo "  Or manually: source venv/bin/activate && python launch.py"
    echo
    print_status "Application will be available at: http://$HOST:$PORT"
    echo
    
    if [ "$AI_PROVIDER" = "ollama" ]; then
        print_warning "Don't forget to start Ollama service: ollama serve"
    fi
    
    print_status "Check system status at: http://$HOST:$PORT/health"
}

# Run main function
main
