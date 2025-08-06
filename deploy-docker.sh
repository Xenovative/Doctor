#!/bin/bash

# AI Doctor Matching System - Docker Deployment Script
# Usage: ./deploy-docker.sh [ollama|openrouter] [--with-nginx]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

AI_PROVIDER=${1:-ollama}
WITH_NGINX=${2}

echo -e "${BLUE}🐳 AI Doctor Matching System - Docker Deployment${NC}"
echo -e "${BLUE}AI Provider: ${AI_PROVIDER}${NC}"
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

# Check Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    log_info "Docker requirements check passed ✓"
}

# Create environment file
create_env_file() {
    log_info "Creating environment file..."
    
    cat > .env << EOF
AI_PROVIDER=$AI_PROVIDER
OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-}
OPENROUTER_MODEL=${OPENROUTER_MODEL:-anthropic/claude-3.5-sonnet}
OPENROUTER_MAX_TOKENS=${OPENROUTER_MAX_TOKENS:-4000}
OLLAMA_MODEL=${OLLAMA_MODEL:-llama3.1:8b}
EOF

    log_info "Environment file created ✓"
}

# Create nginx config
create_nginx_config() {
    if [[ "$WITH_NGINX" == "--with-nginx" ]]; then
        log_info "Creating nginx configuration..."
        
        cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream app {
        server ai-doctor-app:8081;
    }
    
    server {
        listen 80;
        server_name _;
        
        client_max_body_size 50M;
        
        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 300;
            proxy_connect_timeout 300;
            proxy_send_timeout 300;
        }
        
        location /health {
            proxy_pass http://app/health;
            access_log off;
        }
    }
}
EOF
        
        log_info "Nginx configuration created ✓"
    fi
}

# Pull Ollama model
setup_ollama_model() {
    if [[ "$AI_PROVIDER" == "ollama" ]]; then
        log_info "Setting up Ollama model..."
        
        # Start Ollama service first
        docker-compose --profile ollama up -d ollama
        
        # Wait for Ollama to be ready
        log_info "Waiting for Ollama to be ready..."
        sleep 10
        
        # Pull the model
        docker-compose exec ollama ollama pull llama3.1:8b
        
        log_info "Ollama model setup complete ✓"
    fi
}

# Deploy application
deploy_app() {
    log_info "Building and deploying application..."
    
    # Build the application
    docker-compose build ai-doctor-app
    
    # Determine which services to start
    PROFILES=""
    if [[ "$AI_PROVIDER" == "ollama" ]]; then
        PROFILES="--profile ollama"
    fi
    
    if [[ "$WITH_NGINX" == "--with-nginx" ]]; then
        PROFILES="$PROFILES --profile nginx"
    fi
    
    # Start services
    docker-compose $PROFILES up -d
    
    log_info "Application deployed ✓"
}

# Wait for services
wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    # Wait for application
    for i in {1..30}; do
        if curl -f http://localhost:8081/health > /dev/null 2>&1; then
            log_info "Application is ready ✓"
            break
        fi
        
        if [[ $i -eq 30 ]]; then
            log_error "Application failed to start"
            docker-compose logs ai-doctor-app
            exit 1
        fi
        
        sleep 2
    done
}

# Show status
show_status() {
    echo ""
    echo -e "${GREEN}🎉 Docker deployment completed!${NC}"
    echo ""
    echo -e "${BLUE}Services Status:${NC}"
    docker-compose ps
    echo ""
    echo -e "${BLUE}Application URLs:${NC}"
    
    if [[ "$WITH_NGINX" == "--with-nginx" ]]; then
        echo "  • Application: http://localhost"
        echo "  • Health Check: http://localhost/health"
    else
        echo "  • Application: http://localhost:8081"
        echo "  • Health Check: http://localhost:8081/health"
    fi
    
    if [[ "$AI_PROVIDER" == "ollama" ]]; then
        echo "  • Ollama API: http://localhost:11434"
    fi
    
    echo ""
    echo -e "${BLUE}Useful Commands:${NC}"
    echo "  • View logs: docker-compose logs -f"
    echo "  • Stop services: docker-compose down"
    echo "  • Restart: docker-compose restart"
    echo "  • Update: docker-compose pull && docker-compose up -d"
    echo ""
    
    if [[ "$AI_PROVIDER" == "openrouter" ]] && [[ -z "$OPENROUTER_API_KEY" ]]; then
        echo -e "${YELLOW}⚠️  Set OPENROUTER_API_KEY in .env file and restart:${NC}"
        echo "     docker-compose restart ai-doctor-app"
        echo ""
    fi
}

# Cleanup function
cleanup() {
    log_info "Stopping services..."
    docker-compose down
}

# Trap cleanup on exit
trap cleanup EXIT

# Main function
main() {
    check_docker
    create_env_file
    create_nginx_config
    setup_ollama_model
    deploy_app
    wait_for_services
    show_status
    
    # Remove trap since we succeeded
    trap - EXIT
}

# Run main function
main "$@"
