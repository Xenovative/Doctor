#!/bin/bash

# AI Doctor Matching System - Troubleshooting Script
# Usage: ./troubleshoot.sh

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_NAME="ai-doctor-matching"
APP_PORT=8081
SERVICE_NAME="ai-doctor-matching"

echo -e "${BLUE}🔍 AI Doctor Matching System - Troubleshooting${NC}"
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

# Check service status
check_service() {
    echo -e "${BLUE}=== Service Status ===${NC}"
    
    if systemctl is-active --quiet $SERVICE_NAME; then
        log_info "Service is running ✓"
        systemctl status $SERVICE_NAME --no-pager -l
    else
        log_error "Service is not running ✗"
        echo "Service status:"
        systemctl status $SERVICE_NAME --no-pager -l
        echo ""
        echo "Recent logs:"
        journalctl -u $SERVICE_NAME -n 20 --no-pager
    fi
    echo ""
}

# Check port binding
check_port() {
    echo -e "${BLUE}=== Port Status ===${NC}"
    
    if netstat -tlnp | grep ":$APP_PORT " > /dev/null; then
        log_info "Port $APP_PORT is bound ✓"
        netstat -tlnp | grep ":$APP_PORT "
    else
        log_error "Port $APP_PORT is not bound ✗"
        echo "All listening ports:"
        netstat -tlnp | grep LISTEN
    fi
    echo ""
}

# Check firewall
check_firewall() {
    echo -e "${BLUE}=== Firewall Status ===${NC}"
    
    if command -v ufw &> /dev/null; then
        echo "UFW Status:"
        ufw status verbose || echo "UFW not accessible"
        
        if ufw status | grep -q "$APP_PORT"; then
            log_info "Port $APP_PORT is allowed in UFW ✓"
        else
            log_warn "Port $APP_PORT not explicitly allowed in UFW"
            echo "To fix: sudo ufw allow $APP_PORT/tcp"
        fi
    else
        echo "UFW not installed"
    fi
    
    echo ""
    echo "iptables rules:"
    iptables -L INPUT -n | grep "$APP_PORT" || echo "No specific iptables rules for port $APP_PORT"
    echo ""
}

# Check application logs
check_logs() {
    echo -e "${BLUE}=== Application Logs ===${NC}"
    
    echo "Recent service logs:"
    journalctl -u $SERVICE_NAME -n 50 --no-pager
    echo ""
}

# Check network connectivity
check_network() {
    echo -e "${BLUE}=== Network Connectivity ===${NC}"
    
    echo "Testing local connectivity:"
    if curl -f http://localhost:$APP_PORT/health &>/dev/null; then
        log_info "Local health check passed ✓"
        curl -s http://localhost:$APP_PORT/health | jq . 2>/dev/null || curl -s http://localhost:$APP_PORT/health
    else
        log_error "Local health check failed ✗"
        echo "Curl output:"
        curl -v http://localhost:$APP_PORT/health 2>&1 || echo "Curl failed"
    fi
    echo ""
    
    echo "Testing external connectivity:"
    if command -v nc &> /dev/null; then
        if nc -z localhost $APP_PORT; then
            log_info "Port $APP_PORT is reachable via netcat ✓"
        else
            log_error "Port $APP_PORT is not reachable via netcat ✗"
        fi
    fi
    echo ""
}

# Check application files
check_files() {
    echo -e "${BLUE}=== Application Files ===${NC}"
    
    APP_DIR="/opt/$APP_NAME"
    
    if [[ -d "$APP_DIR" ]]; then
        log_info "Application directory exists ✓"
        echo "Directory contents:"
        ls -la "$APP_DIR"
        echo ""
        
        if [[ -f "$APP_DIR/app.py" ]]; then
            log_info "app.py exists ✓"
        else
            log_error "app.py missing ✗"
        fi
        
        if [[ -f "$APP_DIR/.env" ]]; then
            log_info ".env file exists ✓"
            echo "Environment variables:"
            cat "$APP_DIR/.env" | grep -v "API_KEY"
        else
            log_error ".env file missing ✗"
        fi
        
        if [[ -d "$APP_DIR/venv" ]]; then
            log_info "Virtual environment exists ✓"
        else
            log_error "Virtual environment missing ✗"
        fi
    else
        log_error "Application directory missing ✗"
    fi
    echo ""
}

# Check system resources
check_resources() {
    echo -e "${BLUE}=== System Resources ===${NC}"
    
    echo "Memory usage:"
    free -h
    echo ""
    
    echo "Disk usage:"
    df -h /
    echo ""
    
    echo "CPU load:"
    uptime
    echo ""
}

# Provide fix suggestions
suggest_fixes() {
    echo -e "${BLUE}=== Suggested Fixes ===${NC}"
    
    echo "1. Restart the service:"
    echo "   sudo systemctl restart $SERVICE_NAME"
    echo ""
    
    echo "2. Check and fix firewall:"
    echo "   sudo ufw allow $APP_PORT/tcp"
    echo "   sudo ufw reload"
    echo ""
    
    echo "3. Manual service start (for debugging):"
    echo "   sudo systemctl stop $SERVICE_NAME"
    echo "   cd /opt/$APP_NAME"
    echo "   sudo -u doctor-app /opt/$APP_NAME/venv/bin/python app.py"
    echo ""
    
    echo "4. Check application configuration:"
    echo "   sudo nano /opt/$APP_NAME/.env"
    echo ""
    
    echo "5. View real-time logs:"
    echo "   sudo journalctl -u $SERVICE_NAME -f"
    echo ""
    
    echo "6. Reset and redeploy:"
    echo "   sudo systemctl stop $SERVICE_NAME"
    echo "   sudo systemctl disable $SERVICE_NAME"
    echo "   sudo rm -rf /opt/$APP_NAME"
    echo "   ./deploy.sh production [ollama|openrouter]"
    echo ""
}

# Main troubleshooting function
main() {
    check_service
    check_port
    check_firewall
    check_network
    check_files
    check_resources
    check_logs
    suggest_fixes
}

# Run troubleshooting
main "$@"
