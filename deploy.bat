@echo off
setlocal enabledelayedexpansion

REM AI Doctor Matching System - Windows Deployment Script
REM Usage: deploy.bat [port] [host] [ai_provider]
REM Example: deploy.bat 8081 0.0.0.0 openrouter

REM Default values
set DEFAULT_PORT=8081
set DEFAULT_HOST=0.0.0.0
set DEFAULT_AI_PROVIDER=ollama

REM Parse command line arguments
if "%1"=="" (set PORT=%DEFAULT_PORT%) else (set PORT=%1)
if "%2"=="" (set HOST=%DEFAULT_HOST%) else (set HOST=%2)
if "%3"=="" (set AI_PROVIDER=%DEFAULT_AI_PROVIDER%) else (set AI_PROVIDER=%3)

echo.
echo ========================================================
echo 🏥 AI Doctor Matching System - Windows Deployment v3.0
echo ========================================================
echo.
echo Latest Features:
echo   - Complete 2FA system with Google Authenticator
echo   - Fine-grained admin tab permissions
echo   - Enhanced bug reporting with image upload
echo   - Improved WhatsApp integration
echo   - Advanced analytics and user management
echo   - Profile management system
echo   - Database migration tools
echo   - Python 3.11 compatibility check
echo.
echo Configuration:
echo   Port: %PORT%
echo   Host: %HOST%
echo   AI Provider: %AI_PROVIDER%
echo.

REM Check if Python is installed and version compatibility
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8-3.11 first.
    pause
    exit /b 1
)

REM Check Python version compatibility (must be 3.11 or lower)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python version: %PYTHON_VERSION%

REM Extract major and minor version numbers
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
)

if %PYTHON_MAJOR% GTR 3 (
    echo ❌ Python version %PYTHON_VERSION% is not supported. Please use Python 3.8-3.11.
    pause
    exit /b 1
)

if %PYTHON_MAJOR% EQU 3 if %PYTHON_MINOR% GTR 11 (
    echo ❌ Python version %PYTHON_VERSION% is not supported. Please use Python 3.8-3.11.
    echo    This application requires Python 3.11 or lower for compatibility.
    pause
    exit /b 1
)

echo ✅ Python version %PYTHON_VERSION% is compatible

REM Check if Node.js is installed (for WhatsApp server)
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed. Please install Node.js 16+ for WhatsApp functionality.
    echo    Download from: https://nodejs.org
    pause
    exit /b 1
) else (
    echo ✅ Node.js is installed
)

echo 📦 Setting up virtual environment...

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

REM Activate virtual environment
call venv\Scripts\activate.bat
echo ✅ Virtual environment activated

REM Upgrade pip
echo 📦 Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo 📦 Installing Python dependencies...
if exist "requirements.txt" (
    pip install -r requirements.txt
    echo ✅ Python dependencies installed
) else (
    echo ❌ requirements.txt not found
    pause
    exit /b 1
)

REM Install Node.js dependencies for WhatsApp server
echo 📦 Installing Node.js dependencies...
if exist "package.json" (
    npm install
    echo ✅ Node.js dependencies installed
    
    REM Install PM2 globally if not already installed
    pm2 --version >nul 2>&1
    if errorlevel 1 (
        echo 📦 Installing PM2 process manager...
        npm install -g pm2
        echo ✅ PM2 installed globally
    ) else (
        echo ✅ PM2 is already installed
    )
) else (
    echo ⚠️ package.json not found - WhatsApp functionality may not work
)

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo ⚙️ Creating .env file...
    copy .env.example .env >nul
    echo ✅ .env file created from template
    echo ⚠️ Please edit .env file with your API keys if using OpenRouter
)

REM Prompt for admin credentials
echo.
echo 👤 Admin Account Configuration
echo ================================
set /p ADMIN_NAME="Enter admin username (default: admin): "
if "%ADMIN_NAME%"=="" set ADMIN_NAME=admin

:password_prompt
set /p ADMIN_PASSWORD="Enter admin password (minimum 6 characters): "
if "%ADMIN_PASSWORD%"=="" (
    echo ❌ Password cannot be empty
    goto password_prompt
)
echo %ADMIN_PASSWORD%| findstr /r "^.......*$" >nul
if errorlevel 1 (
    echo ❌ Password must be at least 6 characters
    goto password_prompt
)

echo ✅ Admin credentials configured: %ADMIN_NAME%
echo.

REM Set environment variables
set AI_PROVIDER=%AI_PROVIDER%
set FLASK_HOST=%HOST%
set FLASK_PORT=%PORT%

REM Update .env file with current settings
echo ⚙️ Updating configuration...
powershell -Command "(Get-Content .env) -replace '^AI_PROVIDER=.*', 'AI_PROVIDER=%AI_PROVIDER%' | Set-Content .env"
powershell -Command "(Get-Content .env) -replace '^ADMIN_USERNAME=.*', 'ADMIN_USERNAME=%ADMIN_NAME%' | Set-Content .env"
powershell -Command "(Get-Content .env) -replace '^ADMIN_PASSWORD=.*', 'ADMIN_PASSWORD=%ADMIN_PASSWORD%' | Set-Content .env"
echo FLASK_HOST=%HOST% >> .env
echo FLASK_PORT=%PORT% >> .env

REM Configure WhatsApp settings
echo.
echo 📱 WhatsApp Configuration
echo ========================
set /p "ENABLE_WHATSAPP=Enable WhatsApp notifications? (y/N): "
if /i "!ENABLE_WHATSAPP!"=="y" (
    set /p "WHATSAPP_NUMBER=Enter target WhatsApp number (format: 852XXXXXXXX@c.us): "
    if "!WHATSAPP_NUMBER!"=="" (
        echo ❌ WhatsApp number cannot be empty
        set ENABLE_WHATSAPP=n
    ) else (
        powershell -Command "(Get-Content .env) -replace '^WHATSAPP_ENABLED=.*', 'WHATSAPP_ENABLED=true' | Set-Content .env"
        powershell -Command "(Get-Content .env) -replace '^WHATSAPP_TARGET_NUMBER=.*', 'WHATSAPP_TARGET_NUMBER=!WHATSAPP_NUMBER!' | Set-Content .env"
        echo ✅ WhatsApp notifications enabled for !WHATSAPP_NUMBER!
    )
) else (
    powershell -Command "(Get-Content .env) -replace '^WHATSAPP_ENABLED=.*', 'WHATSAPP_ENABLED=false' | Set-Content .env"
    echo ⚠️ WhatsApp notifications disabled
)

REM Check AI provider setup
echo 🤖 Checking AI provider setup...
if "%AI_PROVIDER%"=="openrouter" (
    if "%OPENROUTER_API_KEY%"=="" (
        echo ⚠️ OpenRouter selected but OPENROUTER_API_KEY not set
        echo    Please set it in .env file or as environment variable
    ) else (
        echo ✅ OpenRouter API key found
    )
) else if "%AI_PROVIDER%"=="openai" (
    if "%OPENAI_API_KEY%"=="" (
        echo ⚠️ OpenAI selected but OPENAI_API_KEY not set
        echo    Please set it in .env file or as environment variable
    ) else (
        echo ✅ OpenAI API key found
    )
) else if "%AI_PROVIDER%"=="ollama" (
    where ollama >nul 2>&1
    if errorlevel 1 (
        echo ⚠️ Ollama is not installed
        echo    Please install it from: https://ollama.ai
    ) else (
        echo ✅ Ollama is installed
        REM Check if Ollama is running
        curl -s http://localhost:11434/api/tags >nul 2>&1
        if errorlevel 1 (
            echo ⚠️ Ollama service is not running
            echo    Please start it with: ollama serve
        ) else (
            echo ✅ Ollama service is running
        )
    )
)

REM Check if doctors data exists
if exist "assets\finddoc_doctors_detailed 2.csv" (
    echo ✅ Doctors database found
) else if exist "assets\finddoc_doctors_detailed_full_20250905.csv" (
    echo ✅ Doctors database found (full version)
) else (
    echo ⚠️ Doctors database not found
    echo    Expected locations:
    echo      - assets\finddoc_doctors_detailed 2.csv
    echo      - assets\finddoc_doctors_detailed_full_20250905.csv
)

REM Check for database migration scripts
echo 📊 Checking database migration tools...
if exist "migrate_2fa_columns.py" (
    echo ✅ 2FA migration script found
) else (
    echo ⚠️ 2FA migration script missing
)

if exist "add_tab_permissions_column.py" (
    echo ✅ Tab permissions migration script found
) else (
    echo ⚠️ Tab permissions migration script missing
)

REM Check for static assets
if exist "static" (
    echo ✅ Static assets directory found
) else (
    echo ⚠️ Static assets directory missing
)

if exist "templates" (
    echo ✅ Templates directory found
) else (
    echo ❌ Templates directory missing - application will not work
    pause
    exit /b 1
)

REM Check if running as administrator (typical for web servers)
net session >nul 2>&1
if %errorLevel% == 0 (
    echo 🔧 Detected administrator privileges (web server environment)
    echo Would you like to set up this application as a Windows service?
    echo This will:
    echo   - Create a Windows service
    echo   - Enable auto-start on boot
    echo   - Run as a background service
    echo.
    set /p "setup_service=Setup as service? (y/N): "
    
    if /i "!setup_service!"=="y" (
        call :setup_windows_service
    ) else (
        echo Skipping service setup. Starting in foreground mode...
        call :start_foreground
    )
) else (
    echo Running in development mode
    call :start_foreground
)
goto :eof

:start_foreground
echo.
echo 🚀 Starting the application...
echo    Access URL: http://%HOST%:%PORT%
echo    Admin Panel: http://%HOST%:%PORT%/admin
echo    Profile Management: http://%HOST%:%PORT%/admin/profile
echo    Bug Reports: http://%HOST%:%PORT%/admin/bug-reports
echo    Analytics: http://%HOST%:%PORT%/admin/analytics
echo    Health Check: http://%HOST%:%PORT%/health
echo    AI Config: http://%HOST%:%PORT%/ai-config
echo.
echo 🔐 Security Features:
echo    - 2FA authentication available
echo    - Tab-based permissions system
echo    - Secure admin profile management
echo.

REM Start WhatsApp server if enabled
if /i "!ENABLE_WHATSAPP!"=="y" (
    echo 📱 Starting WhatsApp server with PM2...
    
    REM Create logs directory if it doesn't exist
    if not exist "logs" mkdir logs
    
    REM Stop existing WhatsApp server process if running
    pm2 stop whatsapp-server 2>nul
    pm2 delete whatsapp-server 2>nul
    
    REM Start WhatsApp server using PM2
    pm2 start ecosystem.config.js --only whatsapp-server
    
    if !errorLevel! == 0 (
        echo ✅ WhatsApp server started with PM2 on port 8086
        echo    Process name: whatsapp-server
        echo    View logs: pm2 logs whatsapp-server
        echo    Please scan QR code (check PM2 logs for QR code)
        echo.
    ) else (
        echo ❌ Failed to start WhatsApp server with PM2
        echo    Falling back to direct start...
        start "WhatsApp Server" cmd /c "node whatsapp-server.js"
        timeout /t 3 >nul
        echo ✅ WhatsApp server started directly on port 8086
        echo.
    )
)

echo Press Ctrl+C to stop the server
echo.
python app.py
goto :eof

:setup_windows_service
echo 🔧 Setting up Windows service...
echo.
echo Installing python-windows-service package...
pip install python-windows-service pywin32

REM Create service wrapper script
echo Creating service wrapper...
(
echo import sys
echo import os
echo import win32serviceutil
echo import win32service
echo import win32event
echo import servicemanager
echo import socket
echo import subprocess
echo.
echo class AIDoctorService^(win32serviceutil.ServiceFramework^):
echo     _svc_name_ = "AIDoctorMatching"
echo     _svc_display_name_ = "AI Doctor Matching System"
echo     _svc_description_ = "AI-powered doctor matching and recommendation system"
echo.
echo     def __init__^(self, args^):
echo         win32serviceutil.ServiceFramework.__init__^(self, args^)
echo         self.hWaitStop = win32event.CreateEvent^(None, 0, 0, None^)
echo         socket.setdefaulttimeout^(60^)
echo         self.process = None
echo.
echo     def SvcStop^(self^):
echo         self.ReportServiceStatus^(win32service.SERVICE_STOP_PENDING^)
echo         if self.process:
echo             self.process.terminate^(^)
echo         win32event.SetEvent^(self.hWaitStop^)
echo.
echo     def SvcDoRun^(self^):
echo         servicemanager.LogMsg^(servicemanager.EVENTLOG_INFORMATION_TYPE,
echo                               servicemanager.PYS_SERVICE_STARTED,
echo                               ^(self._svc_name_, ''^^)^)
echo         self.main^(^)
echo.
echo     def main^(self^):
echo         # Change to application directory
echo         os.chdir^(r'%CD%'^)
echo         
echo         # Start the Flask application
echo         self.process = subprocess.Popen^([
echo             r'%CD%\venv\Scripts\python.exe',
echo             'app.py'
echo         ]^)
echo         
 echo         # Wait for stop signal
echo         win32event.WaitForSingleObject^(self.hWaitStop, win32event.INFINITE^)
echo.
echo if __name__ == '__main__':
echo     win32serviceutil.HandleCommandLine^(AIDoctorService^)
) > service_wrapper.py

echo ✅ Service wrapper created
echo.
echo Installing Windows service...
python service_wrapper.py install

if %errorLevel% == 0 (
    echo ✅ Service installed successfully: AIDoctorMatching
    echo.
    echo Service commands:
    echo   Start:   net start AIDoctorMatching
    echo   Stop:    net stop AIDoctorMatching
    echo   Remove:  python service_wrapper.py remove
    echo.
    
    set /p "start_service=Start the service now? (Y/n): "
    if /i not "!start_service!"=="n" (
        net start AIDoctorMatching
        if !errorLevel! == 0 (
            echo ✅ Service started successfully!
            echo    Access URL: http://%HOST%:%PORT%
            echo    Health Check: http://%HOST%:%PORT%/health
            echo    AI Config: http://%HOST%:%PORT%/ai-config
            echo.
            echo Check Windows Event Viewer for service logs
        ) else (
            echo ❌ Service failed to start. Check Event Viewer for details.
        )
    ) else (
        echo Service created but not started. Use: net start AIDoctorMatching
    )
) else (
    echo ❌ Failed to install service
)
goto :eof
