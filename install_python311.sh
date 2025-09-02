#!/bin/bash

echo "=== Installing Python 3.11 on Ubuntu ==="

# Add deadsnakes PPA for Python 3.11
echo "1. Adding deadsnakes PPA..."
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Install Python 3.11 and related packages
echo "2. Installing Python 3.11..."
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3.11-distutils

# Install pip for Python 3.11
echo "3. Installing pip for Python 3.11..."
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Verify installation
echo "4. Verifying installation..."
python3.11 --version
python3.11 -m pip --version

echo "✅ Python 3.11 installed successfully"
