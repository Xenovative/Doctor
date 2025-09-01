#!/bin/bash

echo "=== Starting Your App on Port 7001 ==="

# Check if app.py exists and start it
if [ -f "app.py" ]; then
    echo "1. Found app.py, starting Flask app on port 7001..."
    
    # Activate virtual environment if it exists
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo "✅ Virtual environment activated"
    fi
    
    # Start the app in background
    nohup python app.py --port 7001 > app.log 2>&1 &
    APP_PID=$!
    echo "✅ App started with PID: $APP_PID"
    
    # Wait a moment and check if it's running
    sleep 2
    if ps -p $APP_PID > /dev/null; then
        echo "✅ App is running on port 7001"
    else
        echo "❌ App failed to start, check app.log"
    fi
else
    echo "❌ app.py not found in current directory"
fi

# Alternative: if using PM2
echo -e "\n2. Alternative: Starting with PM2 (if available):"
if command -v pm2 &> /dev/null; then
    pm2 start app.py --name doctor-ai --interpreter python3 -- --port 7001
    echo "✅ Started with PM2"
else
    echo "PM2 not available"
fi
