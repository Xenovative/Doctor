#!/bin/bash

# Quick fix for numpy/pandas compatibility issue
echo "🔧 Fixing numpy/pandas compatibility issue..."

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo "❌ Virtual environment not found. Please run install.sh first."
    exit 1
fi

# Uninstall problematic packages
echo "Uninstalling numpy and pandas..."
pip uninstall -y numpy pandas 2>/dev/null || true

# Install compatible versions
echo "Installing compatible numpy version..."
pip install numpy==1.24.3

echo "Installing compatible pandas version..."
pip install pandas==2.0.3

# Reinstall other dependencies to ensure compatibility
echo "Reinstalling other dependencies..."
pip install -r requirements.txt

echo "✅ Fix completed! Try running the application now:"
echo "   python launch.py"
