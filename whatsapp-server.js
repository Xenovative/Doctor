const wa = require('@open-wa/wa-automate');
const { Server } = require('socket.io');

console.log('🔄 Initializing WhatsApp Web Automation Server...');

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
  
  // Start socket server on port 8085
  const io = new Server(8085, {
    cors: {
      origin: "*",
      methods: ["GET", "POST"]
    }
  });
  
  console.log('🚀 Socket.IO server started on port 8085');
  
  io.on('connection', (socket) => {
    console.log('🔌 Client connected to WhatsApp server');
    
    socket.on('sendText', async (data) => {
      try {
        console.log(`📤 Sending message to ${data.to}`);
        const result = await client.sendText(data.to, data.content);
        socket.emit('sendText_result', { success: true, result });
        console.log('✅ Message sent successfully');
      } catch (error) {
        console.error('❌ Failed to send message:', error.message);
        socket.emit('sendText_result', { success: false, error: error.message });
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
