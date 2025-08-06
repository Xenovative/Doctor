#!/bin/bash

# Quick fix for hanging Gunicorn workers
# Usage: ./fix-hanging-workers.sh

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_DIR="/opt/ai-doctor-matching"
SERVICE_NAME="ai-doctor-matching"

echo -e "${BLUE}🔧 Fixing Hanging Gunicorn Workers${NC}"
echo ""

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Stop service and kill hanging processes
stop_and_cleanup() {
    log_info "Stopping service and cleaning up processes..."
    
    systemctl stop $SERVICE_NAME
    sleep 2
    
    # Kill any remaining gunicorn processes
    pkill -f "gunicorn.*ai-doctor-matching" || true
    pkill -f "gunicorn.*app:app" || true
    
    # Kill any Python processes running from the app directory
    pkill -f "$APP_DIR" || true
    
    sleep 2
    log_info "Cleanup completed ✓"
}

# Fix common issues
fix_common_issues() {
    log_info "Fixing common issues..."
    
    # Fix file permissions
    chown -R doctor-app:doctor-app $APP_DIR
    chmod +x $APP_DIR/app.py
    
    # Ensure CSV file exists and is readable
    if [[ -f "$APP_DIR/assets/finddoc_doctors_detailed 2.csv" ]]; then
        chown doctor-app:doctor-app "$APP_DIR/assets/finddoc_doctors_detailed 2.csv"
        chmod 644 "$APP_DIR/assets/finddoc_doctors_detailed 2.csv"
        log_info "CSV file permissions fixed ✓"
    else
        log_warn "CSV file not found - this may cause the app to hang"
    fi
    
    # Fix environment file
    if [[ -f "$APP_DIR/.env" ]]; then
        chown doctor-app:doctor-app "$APP_DIR/.env"
        chmod 600 "$APP_DIR/.env"
        log_info "Environment file permissions fixed ✓"
    fi
}

# Update systemd service for better debugging
update_systemd_service() {
    log_info "Updating systemd service for better debugging..."
    
    cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=AI Doctor Matching System
After=network.target

[Service]
Type=exec
User=doctor-app
Group=doctor-app
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn --bind 0.0.0.0:7000 --workers 1 --timeout 300 --log-level info --access-logfile - --error-logfile - app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    log_info "Systemd service updated ✓"
}

# Test app import before starting
test_app_import() {
    log_info "Testing app import..."
    
    if sudo -u doctor-app bash -c "cd $APP_DIR && source venv/bin/activate && timeout 30 python -c 'from app import app; print(\"App imported successfully\")'" 2>/dev/null; then
        log_info "App import test passed ✓"
        return 0
    else
        log_error "App import test failed ✗"
        
        # Show the actual error
        echo "Error details:"
        sudo -u doctor-app bash -c "cd $APP_DIR && source venv/bin/activate && python -c 'from app import app'" 2>&1 | head -20
        return 1
    fi
}

# Start service with monitoring
start_with_monitoring() {
    log_info "Starting service with monitoring..."
    
    systemctl start $SERVICE_NAME
    
    # Monitor startup for 30 seconds
    for i in {1..30}; do
        if systemctl is-active --quiet $SERVICE_NAME; then
            log_info "Service started successfully ✓"
            
            # Test health endpoint
            sleep 5
            if curl -f http://localhost:7000/health &>/dev/null; then
                log_info "Health check passed ✓"
                echo ""
                echo -e "${GREEN}🎉 Service is running and healthy!${NC}"
                echo "Access your app at: http://your-server:7000"
                return 0
            else
                log_warn "Service started but health check failed"
                echo "Recent logs:"
                journalctl -u $SERVICE_NAME -n 10 --no-pager
            fi
            break
        fi
        
        echo -n "."
        sleep 1
    done
    
    if ! systemctl is-active --quiet $SERVICE_NAME; then
        log_error "Service failed to start"
        echo "Recent logs:"
        journalctl -u $SERVICE_NAME -n 20 --no-pager
        return 1
    fi
}

# Main fix process
main() {
    if [[ $EUID -ne 0 ]]; then
        echo "This script must be run as root"
        exit 1
    fi
    
    stop_and_cleanup
    fix_common_issues
    update_systemd_service
    
    if test_app_import; then
        start_with_monitoring
    else
        log_error "Cannot start service - app import failed"
        log_info "Run './diagnose-app.sh' for detailed diagnostics"
        exit 1
    fi
}

# Run the fix
main "$@"
