# Deployment Guide - v2.0

## What's New in v2.0

- **Enhanced AI Error Handling**: Graceful error messages without exposing LLM providers
- **Selective Analytics Export**: Choose specific data types and date ranges for export
- **Improved Admin Dashboard**: Better analytics visualization and user management
- **UTF-8 Support**: Full international character support for Chinese medical data
- **OpenAI Integration**: Added support for OpenAI API alongside OpenRouter and Ollama

## Quick Start

### Windows
```cmd
# Basic deployment (default: port 8081, host 0.0.0.0, ollama)
deploy.bat

# Custom port and host
deploy.bat 3000 localhost

# Use OpenRouter or OpenAI
deploy.bat 8081 0.0.0.0 openrouter
deploy.bat 8081 0.0.0.0 openai
```

### Linux/macOS
```bash
# Make script executable (first time only)
chmod +x deploy.sh

# Basic deployment
./deploy.sh

# Custom configuration
./deploy.sh 3000 localhost openrouter
./deploy.sh 8081 0.0.0.0 openai
```

## Script Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| Port | 8081 | Server port |
| Host | 0.0.0.0 | Server host (0.0.0.0 for all interfaces) |
| AI Provider | ollama | AI service (ollama/openrouter/openai) |

## What the Script Does

1. **Environment Setup**
   - Creates Python virtual environment
   - Installs dependencies from requirements.txt
   - Activates virtual environment

2. **Configuration**
   - Creates .env file from template
   - Sets AI provider and server configuration
   - Updates environment variables

3. **Health Checks**
   - Verifies Python installation
   - Checks AI provider setup
   - Validates doctors database

4. **Service Setup (Web Server Mode)**
   - Detects elevated privileges
   - Offers system service installation
   - Creates systemd service (Linux) or Windows service
   - Configures auto-start on boot

5. **Application Launch**
   - Starts as system service or foreground process
   - Displays access URLs and management commands

## Manual Configuration

If you need to manually configure the application:

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate.bat  # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env file with your settings
   ```

4. **Run application:**
   ```bash
   python app.py
   ```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_PROVIDER` | AI service provider | ollama |
| `OPENROUTER_API_KEY` | OpenRouter API key | - |
| `OPENROUTER_MODEL` | OpenRouter model | anthropic/claude-3.5-sonnet |
| `OPENROUTER_MAX_TOKENS` | Max tokens for OpenRouter | 4000 |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OPENAI_MODEL` | OpenAI model | gpt-4 |
| `OPENAI_MAX_TOKENS` | Max tokens for OpenAI | 4000 |
| `OLLAMA_MODEL` | Ollama model | llama3.1:8b |
| `FLASK_HOST` | Server host | 0.0.0.0 |
| `FLASK_PORT` | Server port | 8081 |
| `FLASK_DEBUG` | Debug mode | True |

## Troubleshooting

### Common Issues

1. **Python not found**
   - Install Python 3.8+ from python.org
   - Ensure Python is in your PATH

2. **Ollama not running**
   ```bash
   ollama serve
   ```

3. **OpenRouter API key missing**
   - Set `OPENROUTER_API_KEY` in .env file
   - Or export as environment variable

4. **Port already in use**
   - Use different port: `deploy.bat 3000`
   - Or kill process using the port

5. **Doctors database missing**
   - Ensure `assets/finddoc_doctors_detailed 2.csv` exists
   - Check file path and permissions

### Health Check URLs

- Application: `http://localhost:8081`
- Health status: `http://localhost:8081/health`
- AI configuration: `http://localhost:8081/ai-config`

## Service Deployment

### Automatic Service Setup

When running the deployment script with elevated privileges (sudo/administrator), you'll be prompted to set up the application as a system service.

**Linux (systemd):**
```bash
sudo ./deploy.sh 8081 0.0.0.0 openrouter
# Will prompt for service setup
```

**Windows (Windows Service):**
```cmd
# Run as Administrator
deploy.bat 8081 0.0.0.0 openrouter
# Will prompt for service setup
```

### Service Management

**Linux:**
```bash
# Service commands
sudo systemctl start ai-doctor-matching
sudo systemctl stop ai-doctor-matching
sudo systemctl status ai-doctor-matching
sudo systemctl enable ai-doctor-matching   # Auto-start on boot
sudo systemctl disable ai-doctor-matching  # Disable auto-start

# View logs
journalctl -u ai-doctor-matching -f
```

**Windows:**
```cmd
# Service commands
net start AIDoctorMatching
net stop AIDoctorMatching
sc query AIDoctorMatching

# Remove service
python service_wrapper.py remove

# View logs in Event Viewer
# Windows Logs > Application
```

## Production Deployment

For production deployment, consider:

1. **Use production WSGI server:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8081 wsgi:application
   ```

2. **Set production environment:**
   ```bash
   export FLASK_DEBUG=False
   ```

3. **Use reverse proxy (nginx/Apache)**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8081;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

4. **Set up SSL/HTTPS**

5. **Configure firewall and security**

6. **Use systemd service for production:**
   - The deployment script creates production-ready systemd services
   - Services automatically restart on failure
   - Logs are managed by systemd/journald
