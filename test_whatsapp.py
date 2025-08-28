import os
import sys
import json
import socketio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# WhatsApp configuration
WHATSAPP_CONFIG = {
    'enabled': os.getenv('WHATSAPP_ENABLED', 'false').lower() == 'true',
    'target_number': os.getenv('WHATSAPP_TARGET_NUMBER', ''),
    'socket_url': os.getenv('WHATSAPP_SOCKET_URL', 'http://localhost:8086'),
    'api_key': os.getenv('WHATSAPP_API_KEY', ''),
    'session_name': os.getenv('WHATSAPP_SESSION_NAME', 'default')
}

print("Current WhatsApp Configuration:")
print(json.dumps(WHATSAPP_CONFIG, indent=2, ensure_ascii=False))

if not WHATSAPP_CONFIG['enabled']:
    print("\nWhatsApp is not enabled. Please check your .env file.")
    sys.exit(1)

try:
    print("\nInitializing WhatsApp client...")
    client = socketio.SimpleClient()
    print(f"Connecting to {WHATSAPP_CONFIG['socket_url']}...")
    client.connect(WHATSAPP_CONFIG['socket_url'])
    print("Connected successfully!")
    
    # Test message
    test_message = "This is a test message from the WhatsApp client."
    print(f"\nSending test message to {WHATSAPP_CONFIG['target_number']}...")
    
    response = client.call('sendText', {
        'to': WHATSAPP_CONFIG['target_number'],
        'content': test_message
    }, timeout=10)
    
    print("\nResponse from server:")
    print(json.dumps(response, indent=2))
    
    if response.get('success'):
        print("\n✅ Message sent successfully!")
    else:
        print(f"\n❌ Failed to send message: {response.get('error', 'Unknown error')}")
    
    client.disconnect()
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
