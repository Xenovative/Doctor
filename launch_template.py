#!/usr/bin/env python3
"""
AI Doctor Matching System Launcher
This script loads environment variables and starts the Flask application
"""
import os
import sys

try:
    from dotenv import load_dotenv
except ImportError:
    print("python-dotenv not found. Installing...")
    os.system(f"{sys.executable} -m pip install python-dotenv")
    from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import the main app
from app import app, AI_CONFIG

def print_startup_info():
    """Print startup information"""
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8081))
    provider = AI_CONFIG['provider']
    
    print("=" * 50)
    print("🏥 AI Doctor Matching System")
    print("=" * 50)
    print(f"Server: http://{host}:{port}")
    print(f"AI Provider: {provider}")
    
    if provider == 'openrouter':
        model = AI_CONFIG['openrouter']['model']
        api_key_set = bool(AI_CONFIG['openrouter']['api_key'])
        print(f"Model: {model}")
        print(f"API Key: {'✓ Set' if api_key_set else '✗ Not Set'}")
    else:
        model = AI_CONFIG['ollama']['model']
        print(f"Model: {model}")
        print("Make sure Ollama is running: ollama serve")
    
    print("=" * 50)
    print(f"Health Check: http://{host}:{port}/health")
    print(f"AI Config: http://{host}:{port}/ai-config")
    print("=" * 50)

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8081))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    print_startup_info()
    
    try:
        app.run(debug=debug, host=host, port=port)
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)
