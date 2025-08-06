@echo off
setlocal enabledelayedexpansion

REM AI Doctor Matching System - Windows Installation Script
echo.
echo 🏥 AI Doctor Matching System - Installation Script
echo ==================================================
echo.

REM Configuration variables
set DEFAULT_PORT=8081
set DEFAULT_HOST=0.0.0.0
set DEFAULT_AI_PROVIDER=ollama

REM Check if Python is installed
echo [INFO] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)
echo [INFO] Python found: 
python --version

REM Create virtual environment
echo.
echo [INFO] Creating virtual environment...
if exist venv (
    echo [WARNING] Virtual environment already exists. Removing old one...
    rmdir /s /q venv
)
python -m venv venv
echo [INFO] Virtual environment created successfully

REM Activate virtual environment
echo.
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo.
echo [INFO] Installing Python dependencies...
python -m pip install --upgrade pip

REM Fix numpy/pandas compatibility issues
echo [INFO] Installing numpy first to avoid compatibility issues...
pip uninstall -y numpy pandas >nul 2>&1
pip install numpy==1.24.3
pip install pandas==2.0.3

REM Install remaining dependencies
pip install -r requirements.txt
pip install python-dotenv
echo [INFO] Dependencies installed successfully

REM Get user configuration
echo.
echo [INFO] Configuration Setup
echo.
set /p PORT="Enter port number (default: %DEFAULT_PORT%): "
if "%PORT%"=="" set PORT=%DEFAULT_PORT%

set /p HOST="Enter host/domain (default: %DEFAULT_HOST%): "
if "%HOST%"=="" set HOST=%DEFAULT_HOST%

set /p AI_PROVIDER="Choose AI provider (ollama/openrouter, default: %DEFAULT_AI_PROVIDER%): "
if "%AI_PROVIDER%"=="" set AI_PROVIDER=%DEFAULT_AI_PROVIDER%

if /i "%AI_PROVIDER%"=="openrouter" (
    set /p OPENROUTER_API_KEY="Enter OpenRouter API Key: "
    set /p OPENROUTER_MODEL="Enter OpenRouter Model (default: anthropic/claude-3.5-sonnet): "
    if "!OPENROUTER_MODEL!"=="" set OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
)

if /i "%AI_PROVIDER%"=="ollama" (
    set /p OLLAMA_MODEL="Enter Ollama Model (default: llama3.1:8b): "
    if "!OLLAMA_MODEL!"=="" set OLLAMA_MODEL=llama3.1:8b
)

REM Create environment file
echo.
echo [INFO] Creating environment configuration...
(
echo # AI Provider Configuration
echo AI_PROVIDER=%AI_PROVIDER%
echo.
echo # Server Configuration
echo HOST=%HOST%
echo PORT=%PORT%
echo.
) > .env

if /i "%AI_PROVIDER%"=="openrouter" (
    (
    echo # OpenRouter Configuration
    echo OPENROUTER_API_KEY=%OPENROUTER_API_KEY%
    echo OPENROUTER_MODEL=%OPENROUTER_MODEL%
    echo OPENROUTER_MAX_TOKENS=4000
    echo.
    ) >> .env
)

if /i "%AI_PROVIDER%"=="ollama" (
    (
    echo # Ollama Configuration
    echo OLLAMA_MODEL=%OLLAMA_MODEL%
    echo.
    ) >> .env
)

echo [INFO] Environment file created: .env

REM Create launcher script
echo.
echo [INFO] Creating launch script...
(
echo #!/usr/bin/env python3
echo import os
echo from dotenv import load_dotenv
echo.
echo # Load environment variables
echo load_dotenv^(^)
echo.
echo # Import the main app
echo from app import app
echo.
echo if __name__ == '__main__':
echo     host = os.getenv^('HOST', '0.0.0.0'^)
echo     port = int^(os.getenv^('PORT', 8081^)^)
echo     debug = os.getenv^('DEBUG', 'True'^).lower^(^) == 'true'
echo     
echo     print^(f"Starting server on {host}:{port}"^)
echo     app.run^(debug=debug, host=host, port=port^)
) > launch.py

echo [INFO] Launch script created: launch.py

REM Create startup scripts
echo.
echo [INFO] Creating startup scripts...

REM Windows startup script
(
echo @echo off
echo echo Starting AI Doctor Matching System...
echo call venv\Scripts\activate.bat
echo python launch.py
echo pause
) > start.bat

REM Unix startup script for compatibility
(
echo #!/bin/bash
echo source venv/bin/activate
echo python launch.py
) > start.sh

echo [INFO] Startup scripts created: start.bat and start.sh

REM Installation completed
echo.
echo ================================================
echo [INFO] Installation completed successfully! 🎉
echo ================================================
echo.
echo [INFO] To start the application:
echo   Windows: start.bat
echo   Or manually: venv\Scripts\activate.bat ^&^& python launch.py
echo.
echo [INFO] Application will be available at: http://%HOST%:%PORT%
echo.

if /i "%AI_PROVIDER%"=="ollama" (
    echo [WARNING] Don't forget to start Ollama service: ollama serve
    echo.
)

echo [INFO] Check system status at: http://%HOST%:%PORT%/health
echo.
echo Press any key to exit...
pause >nul
