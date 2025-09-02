#!/bin/bash

echo "=== Fixing Python 3.12 Dependencies ==="

# Install system dependencies for pandas/numpy compilation
echo "1. Installing system dependencies..."
sudo apt update
sudo apt install -y python3-dev python3-pip build-essential libatlas-base-dev gfortran

# Upgrade pip and install wheel
echo "2. Upgrading pip and installing build tools..."
pip install --upgrade pip setuptools wheel

# Install numpy first (pandas dependency)
echo "3. Installing numpy..."
pip install "numpy>=1.24.0,<2.0.0"

# Install pandas with specific version for Python 3.12
echo "4. Installing pandas (Python 3.12 compatible)..."
pip install "pandas>=2.1.0"

# Install other requirements
echo "5. Installing remaining requirements..."
pip install Flask==2.3.3
pip install requests==2.31.0
pip install python-dotenv==1.0.0
pip install "python-socketio>=5.0.0"
pip install "websocket-client>=1.0.0"

echo "✅ Dependencies installed successfully"
