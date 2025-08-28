module.exports = {
  apps: [
    {
      name: 'whatsapp-server',
      script: 'whatsapp-server.js',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        WHATSAPP_PORT: 8086
      },
      env_development: {
        NODE_ENV: 'development',
        WHATSAPP_PORT: 8086
      },
      error_file: './logs/whatsapp-err.log',
      out_file: './logs/whatsapp-out.log',
      log_file: './logs/whatsapp-combined.log',
      time: true,
      merge_logs: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    }
  ]
};
