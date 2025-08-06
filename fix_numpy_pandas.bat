@echo off
echo 🔧 Fixing numpy/pandas compatibility issue...

REM Activate virtual environment
if exist venv (
    call venv\Scripts\activate.bat
    echo ✓ Virtual environment activated
) else (
    echo ❌ Virtual environment not found. Please run install.bat first.
    pause
    exit /b 1
)

REM Uninstall problematic packages
echo Uninstalling numpy and pandas...
pip uninstall -y numpy pandas >nul 2>&1

REM Install compatible versions
echo Installing compatible numpy version...
pip install numpy==1.24.3

echo Installing compatible pandas version...
pip install pandas==2.0.3

REM Reinstall other dependencies to ensure compatibility
echo Reinstalling other dependencies...
pip install -r requirements.txt

echo ✅ Fix completed! Try running the application now:
echo    python launch.py
pause
