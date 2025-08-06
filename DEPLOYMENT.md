# Deployment Guide

## Quick Start

### Windows
```cmd
# Basic deployment (default: port 8081, host 0.0.0.0, ollama)
deploy.bat

# Custom port and host
deploy.bat 3000 localhost

# Use OpenRouter
deploy.bat 8081 0.0.0.0 openrouter
```

### Linux/macOS
```bash
# Make script executable (first time only)
chmod +x deploy.sh

# Basic deployment
./deploy.sh

# Custom configuration
./deploy.sh 3000 localhost openrouter
```

## Script Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| Port | 8081 | Server port |
| Host | 0.0.0.0 | Server host (0.0.0.0 for all interfaces) |
| AI Provider | ollama | AI service (ollama/openrouter) |

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

4. **Application Launch**
   - Starts Flask development server
   - Displays access URLs

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

## Production Deployment

For production deployment, consider:

1. **Use production WSGI server:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8081 app:app
   ```

2. **Set production environment:**
   ```bash
   export FLASK_DEBUG=False
   ```

3. **Use reverse proxy (nginx/Apache)**

4. **Set up SSL/HTTPS**

5. **Configure firewall and security**
