# WhatsApp Integration Setup Guide

## Overview
This guide explains how to set up WhatsApp notifications for the AI Doctor system. When users click on doctor links, the system will automatically send diagnosis reports to a designated WhatsApp number.

## Prerequisites

### 1. Install wa-automate-socket-client
The system uses `wa-automate-socket-client-python` to send WhatsApp messages. This is already added to `requirements.txt`.

### 2. Set up WhatsApp Web Automation Server
The WhatsApp server runs as a PM2 process for better process management and reliability.

#### Using PM2 Process Manager (Recommended)
The system includes a pre-configured PM2 ecosystem file for the WhatsApp server.

**Installation:**
```bash
# Install PM2 globally (done automatically by deploy.bat)
npm install -g pm2

# Install project dependencies
npm install
```

**Starting the WhatsApp Server:**
```bash
# Using the provided management script
pm2-whatsapp.bat start

# Or directly with PM2
pm2 start ecosystem.config.js --only whatsapp-server
```

**Managing the WhatsApp Server:**
```bash
# Check status
pm2-whatsapp.bat status

# View logs (including QR code)
pm2-whatsapp.bat logs

# Restart server
pm2-whatsapp.bat restart

# Stop server
pm2-whatsapp.bat stop
```

#### Manual Setup (Alternative)
If you prefer to run without PM2:
```bash
# Run directly
node whatsapp-server.js
```

#### Option B: Using Docker
```bash
# Pull the wa-automate Docker image
docker pull openwa/wa-automate:latest

# Run the container
docker run -it -p 8085:8080 openwa/wa-automate:latest
```

## Configuration

### 1. Environment Variables
Copy `.env.example` to `.env` and configure the WhatsApp settings:

```env
# WhatsApp Configuration
WHATSAPP_ENABLED=true
WHATSAPP_SOCKET_URL=http://localhost:8086
WHATSAPP_API_KEY=your_api_key_here
WHATSAPP_TARGET_NUMBER=852XXXXXXXX@c.us
WHATSAPP_SESSION_NAME=default

# WhatsApp Server Port (for PM2 process)
WHATSAPP_PORT=8086
```

### 2. Configuration Details

- **WHATSAPP_ENABLED**: Set to `true` to enable WhatsApp notifications
- **WHATSAPP_SOCKET_URL**: URL of your WhatsApp automation server (default: http://localhost:8086)
- **WHATSAPP_API_KEY**: API key for authentication (optional, depends on your server setup)
- **WHATSAPP_TARGET_NUMBER**: Target WhatsApp number in format `852XXXXXXXX@c.us`
  - Replace `852XXXXXXXX` with the actual Hong Kong phone number
  - The `@c.us` suffix is required for individual contacts
  - For group chats, use `@g.us` suffix
- **WHATSAPP_SESSION_NAME**: Session name for the WhatsApp client (default: 'default')

### 3. Phone Number Format
- Hong Kong numbers: `852XXXXXXXX@c.us` (e.g., `85212345678@c.us`)
- International numbers: `COUNTRYCODEXXXXXXXX@c.us`
- Group chats: `GROUPID@g.us`

## Setup Steps

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up WhatsApp Server
Choose one of the options above to set up your WhatsApp automation server.

### 3. Configure Environment
1. Copy `.env.example` to `.env`
2. Set `WHATSAPP_ENABLED=true`
3. Configure your target phone number
4. Set the correct socket URL

### 4. Scan QR Code
1. Start your WhatsApp server
2. Open the browser interface (usually http://localhost:8080)
3. Scan the QR code with your WhatsApp mobile app
4. Wait for the connection to be established

### 5. Test the Integration
1. Start the Flask application: `python app.py`
2. Use the doctor search feature
3. Click on a doctor link
4. Check if the WhatsApp message is sent

## Message Format

When a user clicks on a doctor link, the system sends a formatted message containing:

- 📅 Timestamp
- 👤 Patient information (age, symptoms, language, location)
- 🔍 AI diagnosis results and recommended specialty
- 👨‍⚕️ Selected doctor information
- 📊 Complete diagnosis (truncated to 500 characters)

Example message:
```
🏥 *AI醫療診斷報告*
📅 時間: 2024-01-15 14:30:25

👤 *患者信息*
年齡: 35歲
症狀: 頭痛和發燒
語言: 中文
地區: 香港島

🔍 *AI診斷結果*
推薦專科: 內科

👨‍⚕️ *選擇的醫生*
醫生姓名: Dr. Smith
專科: 內科

📊 *完整診斷*
根據症狀分析，可能是感冒或流感...

---
AI香港醫療配對系統
```

## Troubleshooting

### Common Issues

1. **WhatsApp client not connecting**
   - Check if the WhatsApp server is running
   - Verify the socket URL is correct
   - Ensure QR code is scanned and session is active

2. **Messages not sending**
   - Check the target phone number format
   - Verify the phone number is registered with WhatsApp
   - Check server logs for error messages

3. **Connection timeout**
   - Increase timeout settings in your WhatsApp server
   - Check network connectivity
   - Restart the WhatsApp server

### Debugging

Enable debug logging by setting environment variables:
```env
FLASK_DEBUG=True
```

Check the application logs for WhatsApp-related messages:
- "WhatsApp客戶端已初始化" - Client initialized successfully
- "WhatsApp通知已發送" - Message sent successfully
- "WhatsApp發送失敗" - Message sending failed

## Security Considerations

1. **API Keys**: Keep your API keys secure and don't commit them to version control
2. **Phone Numbers**: Ensure you have permission to send messages to the target number
3. **Rate Limiting**: Be aware of WhatsApp's rate limits to avoid being blocked
4. **Data Privacy**: Ensure compliance with data protection regulations when sending medical information

## Production Deployment

For production use:

1. Use a dedicated server for the WhatsApp automation
2. Implement proper error handling and retry mechanisms
3. Set up monitoring and logging
4. Consider using a message queue for reliability
5. Implement rate limiting to prevent spam
6. Use environment-specific configuration files

## Support

If you encounter issues:
1. Check the application logs
2. Verify your WhatsApp server is running and accessible
3. Test the connection manually using the socket client
4. Ensure all environment variables are correctly set
