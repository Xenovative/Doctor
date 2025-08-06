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
echo 🏥 AI Doctor Matching System - Windows Deployment
echo ========================================================
echo.
echo Configuration:
echo   Port: %PORT%
echo   Host: %HOST%
echo   AI Provider: %AI_PROVIDER%
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
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
echo 📦 Installing dependencies...
if exist "requirements.txt" (
    pip install -r requirements.txt
    echo ✅ Dependencies installed
) else (
    echo ❌ requirements.txt not found
    pause
    exit /b 1
)

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo ⚙️ Creating .env file...
    copy .env.example .env >nul
    echo ✅ .env file created from template
    echo ⚠️ Please edit .env file with your API keys if using OpenRouter
)

REM Set environment variables
set AI_PROVIDER=%AI_PROVIDER%
set FLASK_HOST=%HOST%
set FLASK_PORT=%PORT%

REM Update .env file with current settings
echo ⚙️ Updating configuration...
powershell -Command "(Get-Content .env) -replace '^AI_PROVIDER=.*', 'AI_PROVIDER=%AI_PROVIDER%' | Set-Content .env"
echo FLASK_HOST=%HOST% >> .env
echo FLASK_PORT=%PORT% >> .env

REM Check AI provider setup
echo 🤖 Checking AI provider setup...
if "%AI_PROVIDER%"=="openrouter" (
    if "%OPENROUTER_API_KEY%"=="" (
        echo ⚠️ OpenRouter selected but OPENROUTER_API_KEY not set
        echo    Please set it in .env file or as environment variable
    ) else (
        echo ✅ OpenRouter API key found
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
) else (
    echo ⚠️ Doctors database not found at assets\finddoc_doctors_detailed 2.csv
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
echo    Health Check: http://%HOST%:%PORT%/health
echo    AI Config: http://%HOST%:%PORT%/ai-config
echo.
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
