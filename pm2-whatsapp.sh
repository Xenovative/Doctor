#!/bin/bash

# PM2 WhatsApp Server Management Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

if [ $# -eq 0 ]; then
    echo -e "${BLUE}Usage: ./pm2-whatsapp.sh [command]${NC}"
    echo ""
    echo -e "${YELLOW}Commands:${NC}"
    echo -e "  start    - Start WhatsApp server"
    echo -e "  stop     - Stop WhatsApp server"
    echo -e "  restart  - Restart WhatsApp server"
    echo -e "  status   - Show server status"
    echo -e "  logs     - Show server logs"
    echo -e "  delete   - Delete server process"
    echo ""
    echo -e "${BLUE}Examples:${NC}"
    echo -e "  ./pm2-whatsapp.sh start"
    echo -e "  ./pm2-whatsapp.sh logs"
    exit 0
fi

case "$1" in
    start)
        echo -e "${YELLOW}Starting WhatsApp server with PM2...${NC}"
        mkdir -p logs
        pm2 start ecosystem.config.js --only whatsapp-server
        ;;
    stop)
        echo -e "${YELLOW}Stopping WhatsApp server...${NC}"
        pm2 stop whatsapp-server
        ;;
    restart)
        echo -e "${YELLOW}Restarting WhatsApp server...${NC}"
        pm2 restart whatsapp-server
        ;;
    status)
        echo -e "${BLUE}WhatsApp server status:${NC}"
        pm2 status whatsapp-server
        ;;
    logs)
        echo -e "${BLUE}Showing WhatsApp server logs (Ctrl+C to exit):${NC}"
        pm2 logs whatsapp-server
        ;;
    delete)
        echo -e "${YELLOW}Deleting WhatsApp server process...${NC}"
        pm2 delete whatsapp-server
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo -e "${BLUE}Use './pm2-whatsapp.sh' without arguments to see usage${NC}"
        exit 1
        ;;
esac
