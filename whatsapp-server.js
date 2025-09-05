const wa = require('@open-wa/wa-automate');
const { Server } = require('socket.io');

console.log('🔄 Initializing WhatsApp Web Automation Server...');

// Message tracking for deduplication and rate limiting
const messageStore = new Map(); // Format: messageId -> { timestamp, to, content }
const sentMessages = new Set(); // Track already sent message IDs
const RATE_LIMIT_WINDOW = 60000; // 1 minute
const MAX_MESSAGES_PER_WINDOW = 5; // Max messages per minute per number

// Generate a unique message ID
function generateMessageId(to, content) {
  const timestamp = Date.now();
  const hash = require('crypto')
    .createHash('md5')
    .update(`${to}:${content}:${timestamp}`)
    .digest('hex');
  return `msg_${hash}`;
}

wa.create({
  sessionId: process.env.WHATSAPP_SESSION_NAME || 'default',
  multiDevice: true,
  authTimeout: 60,
  blockCrashLogs: true,
  disableSpins: true,
  hostNotificationLang: 'EN',
  logConsole: false,
  popup: true,
  qrTimeout: 0,
  restartOnCrash: true,
  sessionDataPath: './whatsapp-sessions',
  useChrome: true,
  killProcessOnBrowserClose: true,
  throwErrorOnTosBlock: false,
  executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome-stable',
  chromiumArgs: [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage',
    '--disable-accelerated-2d-canvas',
    '--no-first-run',
    '--no-zygote',
    '--disable-gpu',
    '--disable-web-security',
    '--disable-features=VizDisplayCompositor'
  ]
}).then(client => {
  console.log('✅ WhatsApp client is ready!');
  console.log('📱 Please scan the QR code with your WhatsApp mobile app');
  
  // Start socket server on configurable port (default 8086 to avoid Flask conflict)
  const whatsappPort = process.env.WHATSAPP_PORT || 8086;
  const io = new Server(whatsappPort, {
    cors: {
      origin: "*",
      methods: ["GET", "POST"]
    }
  });
  
  console.log(`🚀 Socket.IO server started on port ${whatsappPort}`);
  
  io.on('connection', (socket) => {
    console.log('🔌 Client connected to WhatsApp server');
    
    socket.on('sendText', async (data, callback) => {
      const now = Date.now();
      
      // Generate or use provided messageId
      const messageId = data.messageId || generateMessageId(data.to, data.content);
      const messageKey = `msg_${messageId}`;
      
      // Check if message was already sent
      if (sentMessages.has(messageId)) {
        console.log(`🔄 Message ${messageId} was already sent, skipping`);
        if (typeof callback === 'function') {
          return callback({ 
            success: true, 
            messageId,
            alreadySent: true,
            status: 'Message was already sent previously'
          });
        }
        return;
      }
      
      // Check for duplicate message
      if (messageStore.has(messageKey)) {
        const lastSent = messageStore.get(messageKey);
        if ((now - lastSent) < RATE_LIMIT_WINDOW) {
          console.log(`🔄 Duplicate message to ${data.to} detected, ignoring`);
          if (typeof callback === 'function') {
            return callback({ success: false, error: 'Duplicate message' });
          }
          return;
        }
      }
      
      // Check rate limit
      const messageCount = Array.from(messageStore.entries())
        .filter(([key, timestamp]) => 
          key.startsWith(`${data.to}:`) && 
          (now - timestamp) < RATE_LIMIT_WINDOW
        ).length;
        
      if (messageCount >= MAX_MESSAGES_PER_WINDOW) {
        console.log(`⚠️ Rate limit exceeded for ${data.to}`);
        if (typeof callback === 'function') {
          return callback({ 
            success: false, 
            error: 'Rate limit exceeded. Please try again later.' 
          });
        }
        return;
      }
      
      try {
        console.log(`📤 Sending message [${messageId}] to ${data.to}`);
        const result = await client.sendText(data.to, data.content);
        
        // Mark message as sent
        sentMessages.add(messageId);
        
        // Store message with timestamp for rate limiting
        messageStore.set(messageKey, {
          timestamp: now,
          to: data.to,
          content: data.content
        });
        
        // Clean up old entries
        for (const [key, entry] of messageStore.entries()) {
          if ((now - entry.timestamp) > RATE_LIMIT_WINDOW * 2) {
            messageStore.delete(key);
            // Keep sentMessages to prevent resending even after cleanup
          }
        }
        
        const response = { 
          success: true, 
          result, 
          messageId,
          alreadySent: false,
          timestamp: now
        };
        if (typeof callback === 'function') {
          callback(response);
        } else {
          socket.emit('sendText_result', response);
        }
        console.log('✅ Message sent successfully');
      } catch (error) {
        console.error('❌ Failed to send message:', error.message);
        const errorResponse = { 
          success: false, 
          error: error.message,
          code: error.code || 'SEND_MESSAGE_ERROR'
        };
        if (typeof callback === 'function') {
          callback(errorResponse);
        } else {
          socket.emit('sendText_result', errorResponse);
        }
      }
    });
    
    socket.on('disconnect', () => {
      console.log('🔌 Client disconnected from WhatsApp server');
    });
  });
  
  // Handle client events
  client.onMessage(async (message) => {
    console.log('📨 Received message:', message.body);
  });
  
  client.onStateChanged((state) => {
    console.log('📱 WhatsApp state changed:', state);
  });
  
}).catch(error => {
  console.error('❌ Failed to initialize WhatsApp client:', error);
  process.exit(1);
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('🛑 Shutting down WhatsApp server...');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('🛑 Shutting down WhatsApp server...');
  process.exit(0);
});
