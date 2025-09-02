#!/bin/bash

echo "=== Complete Python 3.11 Setup ==="

# Install Python 3.11
echo "1. Installing Python 3.11..."
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3.11-distutils

# Install pip for Python 3.11
echo "2. Installing pip for Python 3.11..."
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Remove old venv and create new one with Python 3.11
echo "3. Setting up virtual environment with Python 3.11..."
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate

# Install requirements
echo "4. Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

# Verify Python version in venv
echo "5. Verifying setup..."
python --version
echo "✅ Python 3.11 setup complete"
