#!/usr/bin/env python3
"""
WSGI configuration for AI Doctor Matching System
For production deployment with Gunicorn, uWSGI, or other WSGI servers
"""

import os
import sys
from pathlib import Path

# Add the application directory to Python path
app_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(app_dir))

# Load environment variables from .env file if it exists
env_file = app_dir / '.env'
if env_file.exists():
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

# Import the Flask application
from app import app as application

if __name__ == "__main__":
    # For development/testing
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '8081'))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    application.run(debug=debug, host=host, port=port)
