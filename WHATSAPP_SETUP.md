# WhatsApp Integration Setup Guide

## Overview
This guide explains how to set up WhatsApp notifications for the AI Doctor system. When users click on doctor links, the system will automatically send diagnosis reports to a designated WhatsApp number.

## Prerequisites

### 1. Install wa-automate-socket-client
The system uses `wa-automate-socket-client-python` to send WhatsApp messages. This is already added to `requirements.txt`.

### 2. Set up WhatsApp Web Automation Server
You need to run a WhatsApp Web automation server that the Python client can connect to.

#### Option A: Using wa-automate-nodejs (Recommended)
```bash
# Install Node.js if not already installed
# Then install wa-automate
npm install -g @open-wa/wa-automate

# Create a simple server script (save as whatsapp-server.js)
const wa = require('@open-wa/wa-automate');

wa.create({
  sessionId: 'default',
  multiDevice: true,
  authTimeout: 60,
  blockCrashLogs: true,
  disableSpins: true,
  hostNotificationLang: 'PT_BR',
  logConsole: false,
  popup: true,
  qrTimeout: 0,
  restartOnCrash: true,
  sessionDataPath: './sessions',
  useChrome: true,
  killProcessOnBrowserClose: true,
  throwErrorOnTosBlock: false,
  chromiumArgs: [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage',
    '--disable-accelerated-2d-canvas',
    '--no-first-run',
    '--no-zygote',
    '--disable-gpu'
  ]
}).then(client => {
  console.log('WhatsApp client is ready!');
  
  // Start socket server on port 8085
  const io = require('socket.io')(8085, {
    cors: {
      origin: "*",
      methods: ["GET", "POST"]
    }
  });
  
  io.on('connection', (socket) => {
    console.log('Client connected');
    
    socket.on('sendText', async (data) => {
      try {
        const result = await client.sendText(data.to, data.content);
        socket.emit('sendText_result', { success: true, result });
      } catch (error) {
        socket.emit('sendText_result', { success: false, error: error.message });
      }
    });
  });
});

# Run the server
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
WHATSAPP_SOCKET_URL=http://localhost:8085
WHATSAPP_API_KEY=your_api_key_here
WHATSAPP_TARGET_NUMBER=852XXXXXXXX@c.us
WHATSAPP_SESSION_NAME=default
```

### 2. Configuration Details

- **WHATSAPP_ENABLED**: Set to `true` to enable WhatsApp notifications
- **WHATSAPP_SOCKET_URL**: URL of your WhatsApp automation server (default: http://localhost:8085)
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
