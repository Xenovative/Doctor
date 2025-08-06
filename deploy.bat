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

echo.
echo 🚀 Starting the application...
echo    Access URL: http://%HOST%:%PORT%
echo    Health Check: http://%HOST%:%PORT%/health
echo    AI Config: http://%HOST%:%PORT%/ai-config
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the application
python app.py
