#!/bin/bash

# Quick fix for numpy/pandas compatibility issue
# Run this script to fix the current deployment

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_DIR="/opt/ai-doctor-matching"
SERVICE_NAME="ai-doctor-matching"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo -e "${BLUE}🔧 Fixing numpy/pandas compatibility issue${NC}"
echo ""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    RUNNING_AS_ROOT=true
else
    RUNNING_AS_ROOT=false
fi

# Stop the service
log_info "Stopping service..."
if [[ $RUNNING_AS_ROOT == true ]]; then
    systemctl stop $SERVICE_NAME || true
else
    sudo systemctl stop $SERVICE_NAME || true
fi

# Fix the compatibility issue
log_info "Fixing numpy/pandas compatibility..."

if [[ $RUNNING_AS_ROOT == true ]]; then
    # Uninstall problematic packages
    su - doctor-app -c "$APP_DIR/venv/bin/pip uninstall -y numpy pandas" || true
    
    # Clear pip cache
    su - doctor-app -c "$APP_DIR/venv/bin/pip cache purge" || true
    
    # Install compatible versions in correct order
    log_info "Installing numpy 1.24.3..."
    su - doctor-app -c "$APP_DIR/venv/bin/pip install --no-cache-dir --force-reinstall numpy==1.24.3"
    
    log_info "Installing pandas 2.0.3..."
    su - doctor-app -c "$APP_DIR/venv/bin/pip install --no-cache-dir --force-reinstall pandas==2.0.3"
    
    # Reinstall other dependencies if needed
    log_info "Reinstalling Flask and requests..."
    su - doctor-app -c "$APP_DIR/venv/bin/pip install --no-cache-dir --force-reinstall Flask==2.3.3 requests==2.31.0"
    
else
    # Uninstall problematic packages
    sudo -u doctor-app $APP_DIR/venv/bin/pip uninstall -y numpy pandas || true
    
    # Clear pip cache
    sudo -u doctor-app $APP_DIR/venv/bin/pip cache purge || true
    
    # Install compatible versions in correct order
    log_info "Installing numpy 1.24.3..."
    sudo -u doctor-app $APP_DIR/venv/bin/pip install --no-cache-dir --force-reinstall numpy==1.24.3
    
    log_info "Installing pandas 2.0.3..."
    sudo -u doctor-app $APP_DIR/venv/bin/pip install --no-cache-dir --force-reinstall pandas==2.0.3
    
    # Reinstall other dependencies if needed
    log_info "Reinstalling Flask and requests..."
    sudo -u doctor-app $APP_DIR/venv/bin/pip install --no-cache-dir --force-reinstall Flask==2.3.3 requests==2.31.0
fi

# Test the fix
log_info "Testing the fix..."
if [[ $RUNNING_AS_ROOT == true ]]; then
    su - doctor-app -c "cd $APP_DIR && $APP_DIR/venv/bin/python -c 'import pandas; import numpy; print(\"✓ Import test passed\")'"
else
    sudo -u doctor-app bash -c "cd $APP_DIR && $APP_DIR/venv/bin/python -c 'import pandas; import numpy; print(\"✓ Import test passed\")'"
fi

# Start the service
log_info "Starting service..."
if [[ $RUNNING_AS_ROOT == true ]]; then
    systemctl start $SERVICE_NAME
    sleep 3
    if systemctl is-active --quiet $SERVICE_NAME; then
        log_info "Service started successfully ✓"
    else
        log_error "Service failed to start"
        systemctl status $SERVICE_NAME
        exit 1
    fi
else
    sudo systemctl start $SERVICE_NAME
    sleep 3
    if sudo systemctl is-active --quiet $SERVICE_NAME; then
        log_info "Service started successfully ✓"
    else
        log_error "Service failed to start"
        sudo systemctl status $SERVICE_NAME
        exit 1
    fi
fi

# Test the application
log_info "Testing application..."
sleep 2
if curl -f http://localhost:$(grep -o 'bind 0.0.0.0:[0-9]*' /etc/systemd/system/$SERVICE_NAME.service | cut -d: -f2)/health > /dev/null 2>&1; then
    log_info "Application is working ✓"
    echo ""
    echo -e "${GREEN}🎉 Fix completed successfully!${NC}"
    echo "Your application should now be working properly."
else
    log_warn "Application health check failed - check logs"
    echo "Run: sudo journalctl -u $SERVICE_NAME -f"
fi

echo ""
