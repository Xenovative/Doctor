#!/bin/bash

# Install Chrome/Chromium for WhatsApp automation
echo "🔄 Installing Chrome/Chromium for WhatsApp automation..."

# Update package list
apt-get update

# Install wget if not present
apt-get install -y wget

# Add Google Chrome repository
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Update package list again
apt-get update

# Try to install Google Chrome stable
if apt-get install -y google-chrome-stable; then
    echo "✅ Google Chrome installed successfully"
    CHROME_PATH="/usr/bin/google-chrome-stable"
elif apt-get install -y chromium-browser; then
    echo "✅ Chromium browser installed successfully"
    CHROME_PATH="/usr/bin/chromium-browser"
elif apt-get install -y chromium; then
    echo "✅ Chromium installed successfully"  
    CHROME_PATH="/usr/bin/chromium"
else
    echo "❌ Failed to install Chrome/Chromium"
    exit 1
fi

# Set executable permissions
chmod +x "$CHROME_PATH"

# Export Chrome path
echo "export CHROME_PATH=$CHROME_PATH" >> ~/.bashrc

echo "🎉 Chrome/Chromium installation complete!"
echo "Chrome path: $CHROME_PATH"
echo "Please restart your terminal or run: source ~/.bashrc"
