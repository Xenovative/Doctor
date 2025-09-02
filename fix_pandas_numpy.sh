#!/bin/bash

echo "=== Fixing Pandas/Numpy Binary Incompatibility ==="

# Activate virtual environment
source venv/bin/activate

# Uninstall pandas and numpy completely
echo "1. Uninstalling pandas and numpy..."
pip uninstall -y pandas numpy

# Clear pip cache
echo "2. Clearing pip cache..."
pip cache purge

# Install numpy first, then pandas
echo "3. Installing compatible versions..."
pip install numpy==1.24.3
pip install pandas==2.0.3

# Verify installation
echo "4. Verifying installation..."
python -c "import numpy; print(f'NumPy version: {numpy.__version__}')"
python -c "import pandas; print(f'Pandas version: {pandas.__version__}')"

echo "✅ Dependencies fixed"
