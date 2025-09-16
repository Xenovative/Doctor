# AI Doctor Matching System - Deployment Guide v3.0

## Overview

The AI Doctor Matching System is a Flask-based web application that provides AI-powered doctor recommendations with advanced admin features including 2FA authentication, fine-grained permissions, and comprehensive analytics.

## Latest Features (v3.0)

- **Complete 2FA System**: Google Authenticator integration with backup codes
- **Fine-grained Admin Permissions**: Tab-based access control system
- **Enhanced Bug Reporting**: Image upload support and WhatsApp integration
- **Profile Management**: Secure admin profile and password management
- **Advanced Analytics**: Comprehensive user tracking and reporting
- **Database Migration Tools**: Automated schema updates
- **Python 3.11 Compatibility**: Version checking and compatibility enforcement

## Core Features

- AI-powered symptom analysis and doctor matching
- Multi-language support (English, Traditional Chinese, Simplified Chinese)
- Admin dashboard with role-based access control
- WhatsApp integration for notifications and bug reports
- Comprehensive logging and error handling
- Multiple AI provider support (OpenRouter, OpenAI, Ollama)
- Secure authentication with 2FA support
- Real-time analytics and user management

## Requirements

- **Python**: 3.8-3.11 (3.12+ not supported due to compatibility issues)
- **Node.js**: 16+ (for WhatsApp functionality)
- **Database**: SQLite (auto-created)
- **Internet**: Required for AI APIs
- **Storage**: ~100MB for application + database

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
   - Validates Python version (3.8-3.11 required)
   - Checks Node.js installation
   - Verifies required files and directories
   - Tests AI provider connectivity
   - Validates database migration scripts

4. **Database Setup**
   - Initializes SQLite databases
   - Runs migration scripts for 2FA and permissions
   - Creates default admin user
   - Sets up analytics tables

5. **Service Configuration**
   - Configures WhatsApp integration (optional)
   - Sets up admin credentials
   - Enables 2FA if requested
   - Configures tab permissions

6. **Deployment Options**
   - **Development Mode**: Runs in foreground with console output
   - **Service Mode**: Creates system service (Windows Service/systemd)
   - **PM2 Integration**: Manages WhatsApp server process

## Access URLs

After successful deployment, the application will be available at:

- **Main Application**: `http://HOST:PORT/`
- **Admin Panel**: `http://HOST:PORT/admin`
- **Profile Management**: `http://HOST:PORT/admin/profile`
- **Bug Reports**: `http://HOST:PORT/admin/bug-reports`
- **Analytics Dashboard**: `http://HOST:PORT/admin/analytics`
- **Health Check**: `http://HOST:PORT/health`
- **AI Configuration**: `http://HOST:PORT/ai-config`

## Security Features

### Two-Factor Authentication (2FA)
- Google Authenticator integration
- Backup codes for recovery
- Per-user 2FA settings
- QR code setup process

### Admin Permissions System
- **Dashboard**: Basic admin access
- **Analytics**: View user data and reports
- **Config**: System configuration (super admin only)
- **Doctors**: Manage doctor database
- **Users**: User management and reports
- **Bug Reports**: View and manage bug reports

### Profile Management
- Secure password changes
- Profile information updates
- 2FA setup and management
- Session management

## AI Provider Configuration

### OpenRouter (Recommended)
```bash
# Set in .env file
OPENROUTER_API_KEY=your_api_key_here
AI_PROVIDER=openrouter
```

### OpenAI
```bash
# Set in .env file
OPENAI_API_KEY=your_api_key_here
AI_PROVIDER=openai
```

### Ollama (Local)
```bash
# Install Ollama first
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull required model
ollama pull llama2

# Set in .env file
AI_PROVIDER=ollama
```

## WhatsApp Integration

### Setup Requirements
1. WhatsApp Business API access
2. Node.js WhatsApp server
3. PM2 process manager

### Configuration
```bash
# Enable WhatsApp in .env
WHATSAPP_ENABLED=true
WHATSAPP_TARGET_NUMBER=852XXXXXXXX@c.us
WHATSAPP_SOCKET_URL=http://localhost:8086
```

### Features
- Bug report notifications
- System alerts
- User query notifications
- Diagnosis report sharing

## Database Migration

The system includes automated migration scripts:

### 2FA Migration
```bash
python migrate_2fa_columns.py
```

### Tab Permissions Migration
```bash
python add_tab_permissions_column.py
```

### Manual Database Operations
```python
# Connect to admin database
import sqlite3
conn = sqlite3.connect('admin_data.db')

# View tables
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cursor.fetchall())
```

## Troubleshooting

### Common Issues

#### Python Version Error
```
Error: This application requires Python 3.11 or lower.
```
**Solution**: Install Python 3.8-3.11. Python 3.12+ has compatibility issues.

#### Missing Dependencies
```
ModuleNotFoundError: No module named 'flask'
```
**Solution**: Ensure virtual environment is activated and run `pip install -r requirements.txt`

#### Database Errors
```
sqlite3.OperationalError: no such table: admin_users
```
**Solution**: Run database migration scripts or delete databases to recreate.

#### WhatsApp Connection Issues
```
Failed to start WhatsApp server with PM2
```
**Solution**: 
1. Check Node.js installation
2. Install PM2: `npm install -g pm2`
3. Verify WhatsApp server configuration

#### 2FA Setup Issues
```
Invalid TOTP token
```
**Solution**:
1. Check device time synchronization
2. Regenerate QR code
3. Use backup codes if available

### Log Files

- **Application Logs**: Console output or service logs
- **WhatsApp Logs**: `pm2 logs whatsapp-server`
- **System Logs**: 
  - Windows: Event Viewer
  - Linux: `journalctl -u ai-doctor-matching`

### Performance Optimization

#### Database Optimization
```python
# Regular cleanup (runs automatically)
python -c "from app import cleanup_old_diagnosis_reports; cleanup_old_diagnosis_reports()"
```

#### Memory Management
- Monitor virtual environment size
- Clear old log files periodically
- Optimize doctor database queries

## Production Deployment

### Security Checklist
- [ ] Change default admin credentials
- [ ] Enable 2FA for all admin users
- [ ] Set strong session secrets
- [ ] Configure HTTPS (reverse proxy)
- [ ] Set up firewall rules
- [ ] Regular database backups
- [ ] Monitor log files

### Scaling Considerations
- Use reverse proxy (nginx/Apache)
- Database connection pooling
- Load balancing for multiple instances
- CDN for static assets
- Redis for session storage

### Backup Strategy
```bash
# Backup databases
cp admin_data.db admin_data.db.backup
cp doctors.db doctors.db.backup

# Backup configuration
cp .env .env.backup

# Backup uploaded files
tar -czf uploads_backup.tar.gz static/uploads/
```

## Support

### Getting Help
1. Check deployment logs for errors
2. Review this documentation
3. Verify all requirements are met
4. Test with minimal configuration first

### Version Information
- **Current Version**: 3.0
- **Python Compatibility**: 3.8-3.11
- **Last Updated**: September 2024
- **Breaking Changes**: Python 3.12+ no longer supported

### Migration from v2.0
1. Update requirements.txt
2. Run migration scripts
3. Update .env configuration
4. Test 2FA functionality
5. Verify tab permissions
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
