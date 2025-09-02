#!/bin/bash

echo "=== Complete Virtual Environment Rebuild ==="

# Remove entire virtual environment
echo "1. Removing old virtual environment..."
rm -rf venv

# Create fresh virtual environment with Python 3.11
echo "2. Creating fresh virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip first
echo "3. Upgrading pip..."
pip install --upgrade pip

# Install packages in specific order to avoid conflicts
echo "4. Installing dependencies in correct order..."
pip install numpy==1.24.3
pip install pandas==2.0.3
pip install Flask==2.3.3
pip install requests==2.31.0
pip install python-dotenv==1.0.0
pip install "python-socketio>=5.0.0"
pip install "websocket-client>=1.0.0"

# Test imports
echo "5. Testing imports..."
python -c "import numpy; import pandas; import flask; print('✅ All imports successful')"

echo "✅ Virtual environment completely rebuilt"
