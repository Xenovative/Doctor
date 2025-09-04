import sys

# Check Python version compatibility
if sys.version_info >= (3, 12):
    print("Error: This application requires Python 3.11 or lower.")
    print(f"Current Python version: {sys.version}")
    print("Please use Python 3.8 - 3.11 to run this service.")
    sys.exit(1)

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import pandas as pd
import requests
import json
import os
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from typing import List, Dict, Any
import hashlib
import secrets
import asyncio
import threading
import logging
from dotenv import load_dotenv, set_key
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Conditional import for WhatsApp client
try:
    import socketio
    WHATSAPP_AVAILABLE = True
except ImportError:
    socketio = None
    WHATSAPP_AVAILABLE = False
    print("Warning: python-socketio not installed. WhatsApp functionality will be disabled.")

def update_env_file(key: str, value: str) -> None:
    """Update or add a key-value pair in the .env file."""
    env_path = Path('.env')
    
    # If .env doesn't exist, create it
    if not env_path.exists():
        env_path.touch()
    
    # Read current content
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"Error reading .env file: {e}")
        return
    
    # Update or add the key
    key_exists = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f'{key}='):
            lines[i] = f"{key}={value}\n"
            key_exists = True
            break
    
    if not key_exists:
        lines.append(f"{key}={value}\n")
    
    # Write back to file
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        logger.info(f"Updated {key} in .env file")
    except Exception as e:
        logger.error(f"Error writing to .env file: {e}")

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Add route to serve assets folder
from flask import send_from_directory

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)

# WhatsApp配置
WHATSAPP_CONFIG = {
    'enabled': os.getenv('WHATSAPP_ENABLED', 'false').lower() == 'true',
    'socket_url': os.getenv('WHATSAPP_SOCKET_URL', 'http://localhost:8086'),
    'api_key': os.getenv('WHATSAPP_API_KEY', ''),
    'target_number': os.getenv('WHATSAPP_TARGET_NUMBER', ''),  # Format: 852XXXXXXXX@c.us
    'session_name': os.getenv('WHATSAPP_SESSION_NAME', 'default')
}

# AI服務配置
AI_CONFIG = {
    'provider': os.getenv('AI_PROVIDER', 'ollama'),  # 'ollama', 'openrouter', or 'openai'
    'openrouter': {
        'api_key': os.getenv('OPENROUTER_API_KEY', ''),
        'base_url': 'https://openrouter.ai/api/v1/chat/completions',
        'model': os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3.5-sonnet'),
        'max_tokens': int(os.getenv('OPENROUTER_MAX_TOKENS', '4000'))
    },
    'openai': {
        'api_key': os.getenv('OPENAI_API_KEY', ''),
        'base_url': 'https://api.openai.com/v1/chat/completions',
        'model': os.getenv('OPENAI_MODEL', 'gpt-4'),
        'max_tokens': int(os.getenv('OPENAI_MAX_TOKENS', '4000'))
    },
    'ollama': {
        'base_url': 'http://localhost:11434/api/generate',
        'model': os.getenv('OLLAMA_MODEL', 'llama3.1:8b')
    }
}

# 載入醫生資料
def load_doctors_data():
    """載入醫生資料"""
    csv_path = os.path.join('assets', 'finddoc_doctors_detailed 2.csv')
    try:
        df = pd.read_csv(csv_path)
        return df.to_dict('records')
    except Exception as e:
        print(f"載入醫生資料時發生錯誤: {e}")
        return []

# 全局變數存儲醫生資料
DOCTORS_DATA = load_doctors_data()

# Admin credentials (in production, use proper user management)
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = hashlib.sha256(os.getenv('ADMIN_PASSWORD', 'admin123').encode()).hexdigest()

def load_ai_config_from_db():
    """Load AI configuration from database"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Load AI config
        cursor.execute('SELECT value FROM system_config WHERE config_key = ?', ('ai_config',))
        result = cursor.fetchone()
        
        if result:
            saved_config = json.loads(result[0])
            AI_CONFIG.update(saved_config)
            print("Loaded AI config from database")
        
        conn.close()
    except Exception as e:
        print(f"Error loading AI config from database: {e}")

def load_whatsapp_config_from_db():
    """Load WhatsApp configuration from database"""
    global WHATSAPP_CONFIG
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Load WhatsApp config
        cursor.execute('SELECT value FROM admin_config WHERE key = ?', ('whatsapp_config',))
        result = cursor.fetchone()
        
        if result:
            saved_config = json.loads(result[0])
            WHATSAPP_CONFIG.update(saved_config)
            print("Loaded WhatsApp config from database")
        
        conn.close()
    except Exception as e:
        print(f"Error loading WhatsApp config from database: {e}")

# Initialize database
def init_db():
    """Initialize SQLite database for analytics and user data"""
    conn = sqlite3.connect('admin_data.db')
    cursor = conn.cursor()
    
    # Analytics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL,
            user_ip TEXT,
            user_agent TEXT,
            data TEXT,
            session_id TEXT
        )
    ''')
    
    # User queries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            age INTEGER,
            symptoms TEXT,
            chronic_conditions TEXT,
            language TEXT,
            location TEXT,
            detailed_health_info TEXT,
            ai_diagnosis TEXT,
            recommended_specialty TEXT,
            matched_doctors_count INTEGER,
            user_ip TEXT,
            session_id TEXT
        )
    ''')
    
    # Doctor clicks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctor_clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            doctor_name TEXT,
            doctor_specialty TEXT,
            user_ip TEXT,
            session_id TEXT,
            query_id INTEGER,
            FOREIGN KEY (query_id) REFERENCES user_queries (id)
        )
    ''')
    
    # System config table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key TEXT UNIQUE,
            config_value TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Admin users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            permissions TEXT DEFAULT '{}',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,
            is_active BOOLEAN DEFAULT 1,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES admin_users (id)
        )
    ''')
    
    # Admin config table for storing configuration settings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create default admin user if not exists
    cursor.execute('SELECT COUNT(*) FROM admin_users WHERE username = ?', (ADMIN_USERNAME,))
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO admin_users (username, password_hash, role, permissions)
            VALUES (?, ?, 'super_admin', '{"all": true}')
        ''', (ADMIN_USERNAME, ADMIN_PASSWORD_HASH))
        print(f"Created default admin user: {ADMIN_USERNAME}")
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Load configurations from database
load_ai_config_from_db()
load_whatsapp_config_from_db()

# WhatsApp客戶端實例
whatsapp_client = None

def init_whatsapp_client():
    """初始化WhatsApp客戶端"""
    global whatsapp_client
    
    if not WHATSAPP_CONFIG['enabled'] or not WHATSAPP_AVAILABLE:
        whatsapp_client = None
        if not WHATSAPP_AVAILABLE:
            print("WhatsApp客戶端不可用：python-socketio未安裝")
        return
    
    try:
        whatsapp_client = socketio.SimpleClient()
        print(f"WhatsApp Socket.IO客戶端已初始化")
    except Exception as e:
        print(f"WhatsApp客戶端初始化失敗: {e}")
        whatsapp_client = None

# Initialize WhatsApp client on startup
init_whatsapp_client()

def send_whatsapp_notification(message: str):
    """發送WhatsApp通知"""
    print(f"DEBUG: WhatsApp enabled: {WHATSAPP_CONFIG['enabled']}")
    print(f"DEBUG: WhatsApp client initialized: {whatsapp_client is not None}")
    print(f"DEBUG: Target number: {WHATSAPP_CONFIG['target_number']}")
    print(f"DEBUG: Socket URL: {WHATSAPP_CONFIG['socket_url']}")
    
    if not WHATSAPP_CONFIG['enabled']:
        print("WhatsApp通知已跳過（未啟用）")
        return False
        
    if not whatsapp_client:
        print("WhatsApp通知已跳過（客戶端未初始化）")
        return False
    
    def send_async():
        connected = False
        try:
            # Check if already connected
            if not whatsapp_client.connected:
                print(f"DEBUG: Connecting to {WHATSAPP_CONFIG['socket_url']}")
                whatsapp_client.connect(WHATSAPP_CONFIG['socket_url'])
                connected = True
            else:
                print("DEBUG: Using existing connection")
            
            print(f"DEBUG: Sending message to {WHATSAPP_CONFIG['target_number']}")
            # Generate a unique message ID for deduplication
            import hashlib
            import time
            message_id = hashlib.md5(f"{WHATSAPP_CONFIG['target_number']}:{message}:{time.time()}".encode()).hexdigest()
            
            # Send message via Socket.IO and wait for response
            response = whatsapp_client.call('sendText', {
                'to': WHATSAPP_CONFIG['target_number'],
                'content': message,
                'messageId': message_id  # Include message ID for deduplication
            }, timeout=10)
            
            if response and response.get('success'):
                print(f"✅ WhatsApp message sent successfully to {WHATSAPP_CONFIG['target_number']}")
                return True
            else:
                error_msg = response.get('error', 'Unknown error') if response else 'No response from server'
                print(f"❌ WhatsApp send failed: {error_msg}")
                return False
                
        except Exception as e:
            print(f"❌ WhatsApp send error: {str(e)}")
            # If there was an error, try to disconnect to clean up the connection
            try:
                if connected and whatsapp_client.connected:
                    whatsapp_client.disconnect()
            except:
                pass
            return False
    
    try:
        # Run in a new thread
        thread = threading.Thread(target=send_async)
        thread.daemon = True
        thread.start()
        return True
    except Exception as e:
        print(f"WhatsApp通知錯誤: {e}")
        return False

def format_diagnosis_report(user_query_data: dict, doctor_data: dict) -> str:
    """格式化診斷報告為WhatsApp消息"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    message = f"""🏥 *AI醫療診斷報告*
📅 時間: {timestamp}

👤 *患者信息*
年齡: {user_query_data.get('age', 'N/A')}歲
症狀: {user_query_data.get('symptoms', 'N/A')}
語言: {user_query_data.get('language', 'N/A')}
地區: {user_query_data.get('location', 'N/A')}

🔍 *AI診斷結果*
推薦專科: {user_query_data.get('recommended_specialty', 'N/A')}

👨‍⚕️ *選擇的醫生*
醫生姓名: {doctor_data.get('doctor_name', 'N/A')}
專科: {doctor_data.get('doctor_specialty', 'N/A')}

📊 *完整診斷*
{user_query_data.get('ai_diagnosis', 'N/A')[:500]}{'...' if len(user_query_data.get('ai_diagnosis', '')) > 500 else ''}

---
AI香港醫療配對系統"""
    
    return message

def get_real_ip():
    """Get the real client IP address, considering proxies and load balancers"""
    # Check for forwarded headers in order of preference
    if request.headers.get('X-Forwarded-For'):
        # X-Forwarded-For can contain multiple IPs, get the first one (original client)
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    elif request.headers.get('CF-Connecting-IP'):  # Cloudflare
        return request.headers.get('CF-Connecting-IP')
    elif request.headers.get('X-Client-IP'):
        return request.headers.get('X-Client-IP')
    else:
        # Fallback to remote_addr
        return request.remote_addr

def log_analytics(event_type, data=None, user_ip=None, user_agent=None, session_id=None):
    """Log analytics event"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO analytics (event_type, user_ip, user_agent, data, session_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (event_type, user_ip, user_agent, json.dumps(data) if data else None, session_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Analytics logging error: {e}")

def get_admin_user(username):
    """Get admin user from database"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, password_hash, role, permissions, is_active
            FROM admin_users 
            WHERE username = ? AND is_active = 1
        ''', (username,))
        user = cursor.fetchone()
        conn.close()
        return user
    except Exception as e:
        print(f"Error getting admin user: {e}")
        return None

def check_permission(permission):
    """Check if current admin user has specific permission"""
    if not session.get('admin_logged_in'):
        return False
    
    user_role = session.get('admin_role', '')
    user_permissions = session.get('admin_permissions', {})
    
    # Super admin has all permissions
    if user_role == 'super_admin' or user_permissions.get('all'):
        return True
    
    return user_permissions.get(permission, False)

def require_admin(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    """Decorator to require admin authentication (alias for require_admin)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def require_permission(permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('admin_logged_in'):
                return redirect(url_for('admin_login'))
            if not check_permission(permission):
                flash('您沒有權限執行此操作', 'error')
                return redirect(url_for('admin_dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def generate_user_summary(age: int, symptoms: str, chronic_conditions: str, detailed_health_info: Dict) -> str:
    """生成用戶輸入數據摘要"""
    summary_parts = []
    
    # 基本信息
    summary_parts.append(f"年齡：{age}歲")
    summary_parts.append(f"主要症狀：{symptoms}")
    
    # 長期病史
    if chronic_conditions:
        summary_parts.append(f"長期病史：{chronic_conditions}")
    
    # 身體指標
    if detailed_health_info.get('height') or detailed_health_info.get('weight'):
        height = detailed_health_info.get('height', '')
        weight = detailed_health_info.get('weight', '')
        if height and weight:
            bmi = round(float(weight) / ((float(height) / 100) ** 2), 1) if height and weight else None
            summary_parts.append(f"身高體重：{height}cm / {weight}kg" + (f" (BMI: {bmi})" if bmi else ""))
        elif height:
            summary_parts.append(f"身高：{height}cm")
        elif weight:
            summary_parts.append(f"體重：{weight}kg")
    
    # 藥物信息
    if detailed_health_info.get('medications'):
        summary_parts.append(f"長期藥物：{detailed_health_info['medications']}")
    
    # 敏感史
    if detailed_health_info.get('allergies'):
        summary_parts.append(f"敏感史：{detailed_health_info['allergies']}")
    
    # 手術史
    if detailed_health_info.get('surgeries'):
        summary_parts.append(f"手術史：{detailed_health_info['surgeries']}")
    
    # 特殊情況
    special_conditions = []
    if detailed_health_info.get('bloodThinner'):
        special_conditions.append("有服薄血藥")
    if detailed_health_info.get('recentVisit'):
        special_conditions.append("三個月內曾就診")
    if detailed_health_info.get('cpapMachine'):
        special_conditions.append("使用呼吸機")
    if detailed_health_info.get('looseTeeth'):
        special_conditions.append("有鬆牙問題")
    
    if special_conditions:
        summary_parts.append(f"特殊情況：{'、'.join(special_conditions)}")
    
    return '\n'.join(summary_parts)

def call_openrouter_api(prompt: str) -> str:
    """調用OpenRouter API進行AI分析"""
    try:
        if not AI_CONFIG['openrouter']['api_key']:
            return "AI服務配置不完整，請聯繫系統管理員"
            
        headers = {
            "Authorization": f"Bearer {AI_CONFIG['openrouter']['api_key']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "AI Doctor Matching System"
        }
        
        data = {
            "model": AI_CONFIG['openrouter']['model'],
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": AI_CONFIG['openrouter']['max_tokens'],
            "temperature": 0.7
        }
        
        response = requests.post(
            AI_CONFIG['openrouter']['base_url'], 
            headers=headers, 
            json=data, 
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return "AI分析服務暫時不可用，請稍後再試"
            
    except Exception as e:
        return "AI分析服務暫時不可用，請稍後再試"

def call_openai_api(prompt: str) -> str:
    """調用OpenAI API進行AI分析"""
    try:
        if not AI_CONFIG['openai']['api_key']:
            return "AI服務配置不完整，請聯繫系統管理員"
            
        headers = {
            "Authorization": f"Bearer {AI_CONFIG['openai']['api_key']}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": AI_CONFIG['openai']['model'],
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": AI_CONFIG['openai']['max_tokens'],
            "temperature": 0.7
        }
        
        response = requests.post(
            AI_CONFIG['openai']['base_url'], 
            headers=headers, 
            json=data, 
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return "AI分析服務暫時不可用，請稍後再試"
            
    except Exception as e:
        return "AI分析服務暫時不可用，請稍後再試"

def call_ollama_api(prompt: str) -> str:
    """調用Ollama API進行AI分析"""
    try:
        data = {
            "model": AI_CONFIG['ollama']['model'],
            "prompt": prompt,
            "stream": False
        }
        
        response = requests.post(AI_CONFIG['ollama']['base_url'], json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get('response', 'AI分析服務暫時不可用，請稍後再試')
        else:
            return "AI分析服務暫時不可用，請稍後再試"
    except requests.exceptions.ConnectionError:
        return "AI分析服務暫時不可用，請稍後再試"
    except Exception as e:
        return "AI分析服務暫時不可用，請稍後再試"

def get_openai_models(api_key: str = None) -> List[str]:
    """獲取OpenAI可用模型列表"""
    try:
        # Use provided API key or fall back to config
        key_to_use = api_key or AI_CONFIG['openai']['api_key']
        
        if not key_to_use:
            return ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo']  # fallback
            
        headers = {
            "Authorization": f"Bearer {key_to_use}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            'https://api.openai.com/v1/models',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            models_data = response.json()
            # Filter for chat models only
            chat_models = []
            for model in models_data.get('data', []):
                model_id = model.get('id', '')
                if any(prefix in model_id for prefix in ['gpt-4', 'gpt-3.5']):
                    chat_models.append(model_id)
            
            # Sort models with GPT-4 first
            chat_models.sort(key=lambda x: (not x.startswith('gpt-4'), x))
            return chat_models if chat_models else ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo']
        else:
            return ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo']  # fallback
            
    except Exception as e:
        print(f"Error fetching OpenAI models: {e}")
        return ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo']  # fallback

def call_ai_api(prompt: str) -> str:
    """根據配置調用相應的AI API"""
    provider = AI_CONFIG['provider'].lower()
    
    if provider == 'openrouter':
        return call_openrouter_api(prompt)
    elif provider == 'openai':
        return call_openai_api(prompt)
    elif provider == 'ollama':
        return call_ollama_api(prompt)
    else:
        return f"不支援的AI提供商: {provider}"

def diagnose_symptoms(age: int, symptoms: str, chronic_conditions: str = '', detailed_health_info: Dict = None) -> Dict[str, str]:
    """使用AI診斷症狀"""
    
    if detailed_health_info is None:
        detailed_health_info = {}
    
    # 構建詳細健康信息
    health_details = []
    if chronic_conditions.strip():
        health_details.append(f"長期病史：{chronic_conditions}")
    
    if detailed_health_info.get('height') or detailed_health_info.get('weight'):
        height = detailed_health_info.get('height', '')
        weight = detailed_health_info.get('weight', '')
        if height and weight:
            try:
                bmi = round(float(weight) / ((float(height) / 100) ** 2), 1)
                health_details.append(f"身高體重：{height}cm / {weight}kg (BMI: {bmi})")
            except:
                health_details.append(f"身高體重：{height}cm / {weight}kg")
        elif height:
            health_details.append(f"身高：{height}cm")
        elif weight:
            health_details.append(f"體重：{weight}kg")
    
    if detailed_health_info.get('medications'):
        health_details.append(f"長期藥物：{detailed_health_info['medications']}")
    
    if detailed_health_info.get('allergies'):
        health_details.append(f"敏感史：{detailed_health_info['allergies']}")
    
    if detailed_health_info.get('surgeries'):
        health_details.append(f"手術史：{detailed_health_info['surgeries']}")
    
    special_conditions = []
    if detailed_health_info.get('bloodThinner'):
        special_conditions.append("有服薄血藥")
    if detailed_health_info.get('recentVisit'):
        special_conditions.append("三個月內曾就診")
    if detailed_health_info.get('cpapMachine'):
        special_conditions.append("使用呼吸機")
    if detailed_health_info.get('looseTeeth'):
        special_conditions.append("有鬆牙問題")
    
    if special_conditions:
        health_details.append(f"特殊情況：{'、'.join(special_conditions)}")
    
    # 構建AI診斷提示
    health_info = "\n    - ".join(health_details) if health_details else "無特殊健康信息"
    
    diagnosis_prompt = f"""
    作為一名經驗豐富的醫療專家，請根據以下病人資料進行初步診斷分析：

    病人資料：
    - 年齡：{age}歲
    - 主要症狀：{symptoms}
    - {health_info}

    請提供：
    1. 可能的病症診斷（最多3個可能性，按可能性排序）
    2. 建議就診的專科
    3. 症狀嚴重程度評估（輕微/中等/嚴重）
    4. 是否需要緊急就醫
    5. 一般建議和注意事項

    **重要指引：**
    - 如涉及精神健康問題（如精神崩潰、妄想、幻覺、自殺念頭、嚴重抑鬱/焦慮等），必須推薦精神科
    - 如涉及心理創傷、PTSD、情緒失控等，應推薦精神科而非內科
    - 如症狀涉及急性或危及生命情況，應推薦急診科
    - 根據症狀的主要系統選擇最適合的專科，避免一律推薦內科

    請用繁體中文回答，格式如下：
    
    可能診斷：
    1. [最可能的病症] - [可能性百分比]
    2. [第二可能的病症] - [可能性百分比]
    3. [第三可能的病症] - [可能性百分比]
    
    建議專科：[專科名稱]
    嚴重程度：[輕微/中等/嚴重]
    緊急程度：[是/否]
    
    建議：
    [詳細建議和注意事項]
    
    免責聲明：此分析僅供參考，不能替代專業醫療診斷，請務必諮詢合格醫生。
    """
    
    # 獲取AI診斷
    diagnosis_response = call_ai_api(diagnosis_prompt)
    
    # 解析診斷結果
    recommended_specialty = extract_specialty_from_diagnosis(diagnosis_response)
    
    return {
        'diagnosis': diagnosis_response,
        'recommended_specialty': recommended_specialty
    }

def analyze_symptoms_and_match(age: int, symptoms: str, chronic_conditions: str, language: str, location: str, detailed_health_info: Dict = None, location_details: Dict = None) -> Dict[str, Any]:
    """使用AI分析症狀並配對醫生"""
    
    if detailed_health_info is None:
        detailed_health_info = {}
    
    # 生成用戶數據摘要
    user_summary = generate_user_summary(age, symptoms, chronic_conditions, detailed_health_info)
    
    # 第一步：AI診斷
    diagnosis_result = diagnose_symptoms(age, symptoms, chronic_conditions, detailed_health_info)
    
    # 第二步：根據診斷結果推薦醫生
    matched_doctors = filter_doctors(
        diagnosis_result['recommended_specialty'], 
        language, 
        location, 
        symptoms, 
        diagnosis_result['diagnosis'],
        location_details
    )
    
    # 第三步：如果是12歲以下，添加兒科醫生
    if age <= 12:
        pediatric_doctors = filter_doctors('兒科', language, location, symptoms, diagnosis_result['diagnosis'], location_details)
        # 合併醫生清單，去除重複
        all_doctors = matched_doctors + pediatric_doctors
        seen_names = set()
        unique_doctors = []
        for doctor in all_doctors:
            if doctor['name'] not in seen_names:
                seen_names.add(doctor['name'])
                unique_doctors.append(doctor)
        matched_doctors = unique_doctors[:10]  # 限制最多10位醫生
    
    return {
        'user_summary': user_summary,
        'diagnosis': diagnosis_result['diagnosis'],
        'recommended_specialty': diagnosis_result['recommended_specialty'],
        'doctors': matched_doctors
    }

def extract_specialty_from_diagnosis(diagnosis_response: str) -> str:
    """從診斷結果中提取推薦的專科"""
    import re
    
    # 直接從AI回應中解析建議專科
    # 尋找「建議專科：」後面的內容
    specialty_pattern = r'建議專科：\s*([^一-鿿\n]*[一-鿿]+[^一-鿿\n]*?)(?=\n|嚴重程度|緊急程度|$)'
    match = re.search(specialty_pattern, diagnosis_response)
    
    if match:
        recommended_specialty = match.group(1).strip()
        
        # 清理提取的專科名稱，移除不必要的標點符號和空格
        recommended_specialty = re.sub(r'[\[\]\(\)【】《》「」『』]', '', recommended_specialty)
        recommended_specialty = recommended_specialty.strip()
        
        # 專科名稱正規化映射
        specialty_mapping = {
            '精神科': ['精神科', '心理科', '精神健康科', '精神醫學科'],
            '神經科': ['神經科', '腦神經科', '神經內科'],
            '心臟科': ['心臟科', '心臟內科', '心血管科'],
            '急診科': ['急診科', '急症科'],
            '外科': ['外科', '一般外科', '普通外科'],
            '皮膚科': ['皮膚科', '皮膚及性病科'],
            '眼科': ['眼科'],
            '耳鼻喉科': ['耳鼻喉科', 'ENT'],
            '婦產科': ['婦產科', '婦科', '產科'],
            '兒科': ['兒科', '小兒科'],
            '骨科': ['骨科', '骨外科'],
            '泌尿科': ['泌尿科', '泌尿外科'],
            '腸胃科': ['腸胃科', '消化內科', '胃腸科'],
            '內分泌科': ['內分泌科', '糖尿病科'],
            '內科': ['內科', '普通科', '家庭醫學科', '全科']
        }
        
        # 尋找匹配的標準專科名稱
        for standard_specialty, variations in specialty_mapping.items():
            for variation in variations:
                if variation in recommended_specialty:
                    return standard_specialty
        
        # 如果找不到匹配，但有提取到專科名稱，直接返回
        if recommended_specialty and len(recommended_specialty) > 0:
            return recommended_specialty
    
    # 如果沒有找到明確的專科推薦，返回內科作為默認
    return '內科'

def extract_specialty_from_ai_response(ai_response: str) -> str:
    """從AI回應中提取推薦的專科（保留兼容性）"""
    return extract_specialty_from_diagnosis(ai_response)

def safe_str_check(value, search_term):
    """安全的字符串檢查，處理NaN值"""
    if pd.isna(value) or value is None:
        return False
    return search_term in str(value)

def filter_doctors(recommended_specialty: str, language: str, location: str, symptoms: str, ai_analysis: str, location_details: Dict = None) -> List[Dict[str, Any]]:
    """根據條件篩選醫生"""
    matched_doctors = []
    
    for doctor in DOCTORS_DATA:
        score = 0
        match_reasons = []
        
        # 專科匹配
        doctor_specialty = doctor.get('specialty', '')
        if doctor_specialty and not pd.isna(doctor_specialty):
            doctor_specialty = str(doctor_specialty)
            if safe_str_check(doctor_specialty, recommended_specialty):
                score += 50
                match_reasons.append(f"專科匹配：{doctor_specialty}")
            elif safe_str_check(doctor_specialty, '普通科') or safe_str_check(doctor_specialty, '內科'):
                score += 30
                match_reasons.append("可處理一般症狀")
        
        # 語言匹配
        doctor_languages = doctor.get('languages', '')
        if doctor_languages and not pd.isna(doctor_languages):
            doctor_languages = str(doctor_languages)
            if safe_str_check(doctor_languages, language):
                score += 30
                match_reasons.append(f"語言匹配：{language}")
        
        # 3層地區匹配系統
        doctor_address = doctor.get('clinic_addresses', '')
        if doctor_address and not pd.isna(doctor_address):
            doctor_address = str(doctor_address)
            
            # 獲取3層位置信息
            if location_details is None:
                location_details = {}
            
            user_region = location_details.get('region', '')
            user_district = location_details.get('district', '')
            user_area = location_details.get('area', '')
            
            # 定義各區的關鍵詞匹配
            district_keywords = {
                # 香港島
                '中西區': ['中環', '上環', '西環', '金鐘', '堅尼地城', '石塘咀', '西營盤'],
                '東區': ['銅鑼灣', '天后', '炮台山', '北角', '鰂魚涌', '西灣河', '筲箕灣', '柴灣', '小西灣'],
                '南區': ['香港仔', '鴨脷洲', '黃竹坑', '深水灣', '淺水灣', '赤柱', '石澳'],
                '灣仔區': ['灣仔', '跑馬地', '大坑', '渣甸山', '寶馬山'],
                
                # 九龍
                '九龍城區': ['九龍城', '土瓜灣', '馬頭角', '馬頭圍', '啟德', '紅磡', '何文田'],
                '觀塘區': ['觀塘', '牛頭角', '九龍灣', '彩虹', '坪石', '秀茂坪', '藍田', '油塘'],
                '深水埗區': ['深水埗', '長沙灣', '荔枝角', '美孚', '石硤尾', '又一村'],
                '黃大仙區': ['黃大仙', '新蒲崗', '樂富', '橫頭磡', '東頭', '竹園', '慈雲山', '鑽石山'],
                '油尖旺區': ['油麻地', '尖沙咀', '旺角', '大角咀', '太子', '佐敦'],
                
                # 新界
                '離島區': ['長洲', '南丫島', '坪洲', '大嶼山', '東涌', '愉景灣'],
                '葵青區': ['葵涌', '青衣', '葵芳', '荔景'],
                '北區': ['上水', '粉嶺', '打鼓嶺', '沙頭角', '鹿頸'],
                '西貢區': ['西貢', '將軍澳', '坑口', '調景嶺', '寶林', '康盛花園'],
                '沙田區': ['沙田', '大圍', '火炭', '馬鞍山', '烏溪沙'],
                '大埔區': ['大埔', '太和', '大埔墟', '林村', '汀角'],
                '荃灣區': ['荃灣', '梨木樹', '象山', '城門'],
                '屯門區': ['屯門', '友愛', '安定', '山景', '大興', '良景', '建生'],
                '元朗區': ['元朗', '天水圍', '洪水橋', '流浮山', '錦田', '八鄉']
            }
            
            location_matched = False
            
            # 第1層：精確地區匹配 (最高分)
            if user_area and safe_str_check(doctor_address, user_area):
                score += 35
                match_reasons.append(f"精確位置匹配：{user_area}")
                location_matched = True
            
            # 第2層：地區匹配
            elif user_district and user_district in district_keywords:
                keywords = district_keywords[user_district]
                for keyword in keywords:
                    if safe_str_check(doctor_address, keyword):
                        score += 25
                        match_reasons.append(f"地區匹配：{user_district}")
                        location_matched = True
                        break
            
            # 第3層：大區匹配 (最低分)
            if not location_matched and user_region:
                # 香港島大區
                if user_region == '香港島' and (safe_str_check(doctor_address, '香港') or safe_str_check(doctor_address, '中環')):
                    score += 15
                    match_reasons.append("大區匹配：香港島")
                
                # 九龍大區
                elif user_region == '九龍' and safe_str_check(doctor_address, '九龍'):
                    score += 15
                    match_reasons.append("大區匹配：九龍")
                
                # 新界大區
                elif user_region == '新界' and safe_str_check(doctor_address, '新界'):
                    score += 15
                    match_reasons.append("大區匹配：新界")
            
            # 向後兼容：如果沒有location_details，使用舊的location匹配
            if not location_matched and not user_region and location:
                if location in district_keywords:
                    keywords = district_keywords[location]
                    for keyword in keywords:
                        if safe_str_check(doctor_address, keyword):
                            score += 25
                            match_reasons.append(f"地區匹配：{location}")
                            break
        
        # 只保留有一定匹配度的醫生
        if score >= 30:
            # 清理醫生數據，確保所有字段都是字符串
            doctor_copy = {}
            for key, value in doctor.items():
                if pd.isna(value) or value is None:
                    doctor_copy[key] = ''
                else:
                    doctor_copy[key] = str(value)
            
            doctor_copy['match_score'] = score
            doctor_copy['match_reasons'] = match_reasons
            doctor_copy['ai_analysis'] = ai_analysis
            matched_doctors.append(doctor_copy)
    
    # 按匹配分數排序
    matched_doctors.sort(key=lambda x: x['match_score'], reverse=True)
    
    # 返回前20名供分頁使用
    return matched_doctors[:20]

@app.route('/')
def index():
    """主頁"""
    # Log page visit
    log_analytics('page_visit', {'page': 'index'}, 
                 get_real_ip(), request.user_agent.string, session.get('session_id'))
    return render_template('index.html')

@app.route('/find_doctor', methods=['POST'])
def find_doctor():
    """處理醫生搜索請求"""
    try:
        data = request.get_json()
        age = int(data.get('age', 0))
        symptoms = data.get('symptoms', '')
        chronic_conditions = data.get('chronicConditions', '')
        language = data.get('language', '')
        location = data.get('location', '')
        location_details = data.get('locationDetails', {})
        detailed_health_info = data.get('detailedHealthInfo', {})
        
        # 驗證輸入
        if not all([age, symptoms, language, location]):
            return jsonify({'error': '請填寫所有必要資料'}), 400
        
        # 使用AI分析症狀並配對醫生 (傳遞location_details)
        result = analyze_symptoms_and_match(age, symptoms, chronic_conditions, language, location, detailed_health_info, location_details)
        
        # Log user query to database
        session_id = session.get('session_id', secrets.token_hex(16))
        session['session_id'] = session_id
        
        try:
            conn = sqlite3.connect('admin_data.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_queries 
                (age, symptoms, chronic_conditions, language, location, detailed_health_info, 
                 ai_diagnosis, recommended_specialty, matched_doctors_count, user_ip, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (age, symptoms, chronic_conditions, language, location, 
                  json.dumps(detailed_health_info), result['diagnosis'], 
                  result['recommended_specialty'], len(result['doctors']), 
                  get_real_ip(), session_id))
            query_id = cursor.lastrowid
            session['last_query_id'] = query_id
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Database logging error: {e}")
        
        # Log analytics
        log_analytics('doctor_search', {
            'age': age, 'symptoms': symptoms, 'language': language, 'location': location,
            'doctors_found': len(result['doctors']), 'specialty': result['recommended_specialty']
        }, get_real_ip(), request.user_agent.string, session_id)
        
        return jsonify({
            'success': True,
            'user_summary': result['user_summary'],
            'diagnosis': result['diagnosis'],
            'recommended_specialty': result['recommended_specialty'],
            'doctors': result['doctors'],
            'total': len(result['doctors'])
        })
        
    except Exception as e:
        print(f"處理請求時發生錯誤: {e}")
        return jsonify({'error': '服務器內部錯誤'}), 500

@app.route('/health')
def health_check():
    """健康檢查"""
    provider = AI_CONFIG['provider']
    ai_status = 'unknown'
    
    # 測試AI服務狀態
    try:
        test_response = call_ai_api("Hello")
        if "錯誤" not in test_response and "不可用" not in test_response:
            ai_status = 'healthy'
        else:
            ai_status = 'error'
    except:
        ai_status = 'error'
    
    return jsonify({
        'status': 'healthy',
        'doctors_loaded': len(DOCTORS_DATA),
        'ai_provider': provider,
        'ai_status': ai_status,
        'ai_config': {
            'provider': provider,
            'model': AI_CONFIG[provider]['model'] if provider in AI_CONFIG else 'unknown'
        }
    })

@app.route('/ai-config')
def get_ai_config():
    """獲取AI配置信息"""
    provider = AI_CONFIG['provider']
    config_info = {
        'current_provider': provider,
        'available_providers': ['ollama', 'openrouter'],
        'current_model': AI_CONFIG[provider]['model'] if provider in AI_CONFIG else 'unknown'
    }
    
    if provider == 'openrouter':
        config_info['api_key_set'] = bool(AI_CONFIG['openrouter']['api_key'])
        config_info['max_tokens'] = AI_CONFIG['openrouter']['max_tokens']
    
    return jsonify(config_info)

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check database first, then fallback to environment variables
        user = get_admin_user(username)
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if user and user[2] == password_hash:
            # Database user login
            session['admin_logged_in'] = True
            session['admin_username'] = username
            session['admin_user_id'] = user[0]
            session['admin_role'] = user[3]
            session['admin_permissions'] = json.loads(user[4]) if user[4] else {}
            
            # Update last login
            try:
                conn = sqlite3.connect('admin_data.db')
                cursor = conn.cursor()
                cursor.execute('UPDATE admin_users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user[0],))
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Error updating last login: {e}")
            
            log_analytics('admin_login', {'username': username, 'role': user[3]}, 
                         get_real_ip(), request.user_agent.string)
            flash('登入成功', 'success')
            return redirect(url_for('admin_dashboard'))
        elif (username == ADMIN_USERNAME and password_hash == ADMIN_PASSWORD_HASH):
            # Fallback to environment variables
            session['admin_logged_in'] = True
            session['admin_username'] = username
            session['admin_role'] = 'super_admin'
            session['admin_permissions'] = {'all': True}
            log_analytics('admin_login', {'username': username, 'role': 'super_admin'}, 
                         get_real_ip(), request.user_agent.string)
            flash('登入成功', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            log_analytics('admin_login_failed', {'username': username}, 
                         get_real_ip(), request.user_agent.string)
            flash('用戶名或密碼錯誤', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
@require_admin
def admin_logout():
    """Admin logout"""
    log_analytics('admin_logout', {'username': session.get('admin_username')}, 
                 get_real_ip(), request.user_agent.string)
    session.clear()
    flash('已成功登出', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@app.route('/admin/dashboard')
@require_admin
def admin_dashboard():
    """Admin dashboard"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Get basic stats
        cursor.execute('SELECT COUNT(*) FROM user_queries')
        total_queries = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM doctor_clicks')
        total_clicks = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT user_ip) FROM user_queries')
        unique_users = cursor.fetchone()[0]
        
        # Get recent queries
        cursor.execute('''
            SELECT timestamp, age, symptoms, language, location, recommended_specialty
            FROM user_queries 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        recent_queries = cursor.fetchall()
        
        # Get popular specialties
        cursor.execute('''
            SELECT recommended_specialty, COUNT(*) as count
            FROM user_queries 
            WHERE recommended_specialty IS NOT NULL
            GROUP BY recommended_specialty 
            ORDER BY count DESC 
            LIMIT 5
        ''')
        popular_specialties = cursor.fetchall()
        
        # Get daily stats for the last 7 days
        cursor.execute('''
            SELECT DATE(timestamp) as date, COUNT(*) as queries
            FROM user_queries 
            WHERE timestamp >= date('now', '-7 days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        ''')
        daily_stats = cursor.fetchall()
        
        conn.close()
        
        return render_template('admin/dashboard.html', 
                             total_queries=total_queries,
                             total_clicks=total_clicks,
                             unique_users=unique_users,
                             recent_queries=recent_queries,
                             popular_specialties=popular_specialties,
                             daily_stats=daily_stats)
    except Exception as e:
        print(f"Dashboard error: {e}")
        flash('載入儀表板時發生錯誤', 'error')
        return render_template('admin/dashboard.html')

def get_event_display_info(event_type: str) -> dict:
    """Convert event type to display-friendly name and color"""
    event_mapping = {
        'page_visit': {'name': '頁面訪問', 'color': 'primary'},
        'doctor_search': {'name': '醫生搜索', 'color': 'success'},
        'doctor_click': {'name': '醫生點擊', 'color': 'info'},
        'admin_login': {'name': '管理員登入', 'color': 'warning'},
        'admin_login_failed': {'name': '管理員登入失敗', 'color': 'danger'},
        'admin_logout': {'name': '管理員登出', 'color': 'secondary'},
        'config_update': {'name': '配置更新', 'color': 'dark'},
        'ai_analysis': {'name': 'AI分析', 'color': 'success'},
        'error': {'name': '錯誤事件', 'color': 'danger'},
        'health_check': {'name': '健康檢查', 'color': 'light'}
    }
    return event_mapping.get(event_type, {'name': event_type, 'color': 'secondary'})

@app.route('/admin/analytics')
@require_admin
def admin_analytics():
    """Analytics page"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Get analytics data
        cursor.execute('''
            SELECT event_type, COUNT(*) as count
            FROM analytics 
            GROUP BY event_type 
            ORDER BY count DESC
        ''')
        raw_event_stats = cursor.fetchall()
        
        # Convert to display-friendly format with color info
        event_stats = [(get_event_display_info(event_type), count) 
                      for event_type, count in raw_event_stats]
        
        # Get user queries with details
        cursor.execute('''
            SELECT id, timestamp, age, symptoms, language, location, 
                   recommended_specialty, matched_doctors_count, user_ip
            FROM user_queries 
            ORDER BY timestamp DESC 
            LIMIT 50
        ''')
        user_queries = cursor.fetchall()
        
        # Get doctor clicks
        cursor.execute('''
            SELECT dc.timestamp, dc.doctor_name, dc.doctor_specialty, 
                   uq.symptoms, dc.user_ip
            FROM doctor_clicks dc
            LEFT JOIN user_queries uq ON dc.query_id = uq.id
            ORDER BY dc.timestamp DESC 
            LIMIT 50
        ''')
        doctor_clicks = cursor.fetchall()
        
        conn.close()
        
        return render_template('admin/analytics.html',
                             event_stats=event_stats,
                             user_queries=user_queries,
                             doctor_clicks=doctor_clicks)
    except Exception as e:
        print(f"Analytics error: {e}")
        flash('載入分析數據時發生錯誤', 'error')
        return render_template('admin/analytics.html')

@app.route('/admin/config')
@login_required
def admin_config():
    """Admin configuration page"""
    return render_template('admin/config.html', whatsapp_config=WHATSAPP_CONFIG, ai_config=AI_CONFIG)

@app.route('/admin/api/openai-models')
@require_admin
def get_openai_models_api():
    """API endpoint to fetch OpenAI models"""
    # Get API key from query parameter or use current config
    api_key = request.args.get('api_key')
    models = get_openai_models(api_key)
    return jsonify({'models': models})

def update_env_file(key: str, value: str) -> None:
    """Update or add a key-value pair in the .env file."""
    env_path = Path('.env')
    
    # If .env doesn't exist, create it
    if not env_path.exists():
        env_path.touch()
    
    # Read current content
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"Error reading .env file: {e}")
        return
    
    # Update or add the key
    key_exists = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f'{key}='):
            lines[i] = f"{key}={value}\n"
            key_exists = True
            break
    
    if not key_exists:
        lines.append(f"{key}={value}\n")
    
    # Write back to file
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        logger.info(f"Updated {key} in .env file")
    except Exception as e:
        logger.error(f"Error writing to .env file: {e}")

@app.route('/admin/update_ai_config', methods=['POST'])
@require_admin
def update_ai_config():
    try:
        # Update AI_CONFIG based on form data
        provider = request.form.get('provider', 'ollama')
        AI_CONFIG['provider'] = provider
        
        # Update provider-specific config
        if provider == 'openrouter':
            AI_CONFIG['openrouter'].update({
                'api_key': request.form.get('openrouter_api_key', ''),
                'model': request.form.get('openrouter_model', 'anthropic/claude-3.5-sonnet'),
                'max_tokens': int(request.form.get('openrouter_max_tokens', '4000'))
            })
            # Update .env file
            update_env_file('AI_PROVIDER', 'openrouter')
            update_env_file('OPENROUTER_API_KEY', AI_CONFIG['openrouter']['api_key'])
            update_env_file('OPENROUTER_MODEL', AI_CONFIG['openrouter']['model'])
            update_env_file('OPENROUTER_MAX_TOKENS', str(AI_CONFIG['openrouter']['max_tokens']))
            
        elif provider == 'openai':
            AI_CONFIG['openai'].update({
                'api_key': request.form.get('openai_api_key', ''),
                'model': request.form.get('openai_model', 'gpt-4'),
                'max_tokens': int(request.form.get('openai_max_tokens', '4000'))
            })
            # Update .env file
            update_env_file('AI_PROVIDER', 'openai')
            update_env_file('OPENAI_API_KEY', AI_CONFIG['openai']['api_key'])
            
        elif provider == 'ollama':
            AI_CONFIG['ollama'].update({
                'model': request.form.get('ollama_model', 'llama3.1:8b'),
                'base_url': request.form.get('ollama_base_url', 'http://localhost:11434/api/generate')
            })
            # Update .env file
            update_env_file('AI_PROVIDER', 'ollama')
            update_env_file('OLLAMA_MODEL', AI_CONFIG['ollama']['model'])
            update_env_file('OLLAMA_BASE_URL', AI_CONFIG['ollama']['base_url'])
        
        # Save to database
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO system_config (config_key, config_value)
            VALUES ('ai_config', ?)
        ''', (json.dumps(AI_CONFIG),))
        conn.commit()
        conn.close()
        
        # Reload environment variables
        load_dotenv(override=True)
        
        log_analytics('config_update', {'type': 'ai_config', 'provider': provider}, 
                     get_real_ip(), request.user_agent.string)
        
        flash('AI配置已更新', 'success')
    except Exception as e:
        logger.error(f"AI config update error: {e}")
        flash(f'更新AI配置時發生錯誤: {str(e)}', 'error')
    
    return redirect(url_for('admin_config'))

@app.route('/admin/config/password', methods=['POST'])
@require_admin
def change_admin_password():
    """Change admin password"""
    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([current_password, new_password, confirm_password]):
            flash('請填寫所有密碼欄位', 'error')
            return redirect(url_for('admin_config'))
        
        if new_password != confirm_password:
            flash('新密碼與確認密碼不符', 'error')
            return redirect(url_for('admin_config'))
        
        if len(new_password) < 6:
            flash('新密碼長度至少6個字符', 'error')
            return redirect(url_for('admin_config'))
        
        # Verify current password
        current_hash = hashlib.sha256(current_password.encode()).hexdigest()
        user_id = session.get('admin_user_id')
        username = session.get('admin_username')
        
        if user_id:
            # Database user
            conn = sqlite3.connect('admin_data.db')
            cursor = conn.cursor()
            cursor.execute('SELECT password_hash FROM admin_users WHERE id = ?', (user_id,))
            stored_hash = cursor.fetchone()
            
            if not stored_hash or stored_hash[0] != current_hash:
                flash('當前密碼錯誤', 'error')
                conn.close()
                return redirect(url_for('admin_config'))
            
            # Update password
            new_hash = hashlib.sha256(new_password.encode()).hexdigest()
            cursor.execute('UPDATE admin_users SET password_hash = ? WHERE id = ?', (new_hash, user_id))
            conn.commit()
            conn.close()
        else:
            # Environment user - can't change password
            flash('環境變數用戶無法更改密碼', 'error')
            return redirect(url_for('admin_config'))
        
        log_analytics('password_change', {'username': username}, 
                     get_real_ip(), request.user_agent.string)
        flash('密碼更新成功', 'success')
        
    except Exception as e:
        print(f"Password change error: {e}")
        flash('更改密碼時發生錯誤', 'error')
    
    return redirect(url_for('admin_config'))

@app.route('/admin/config/users', methods=['POST'])
@require_permission('user_management')
def create_admin_user():
    """Create new admin user"""
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'admin')
        permissions = request.form.getlist('permissions')
        
        if not all([username, password]):
            flash('請填寫用戶名和密碼', 'error')
            return redirect(url_for('admin_config'))
        
        if len(password) < 6:
            flash('密碼長度至少6個字符', 'error')
            return redirect(url_for('admin_config'))
        
        # Build permissions object
        perm_obj = {}
        for perm in permissions:
            perm_obj[perm] = True
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        created_by = session.get('admin_user_id')
        
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO admin_users (username, password_hash, role, permissions, created_by)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, role, json.dumps(perm_obj), created_by))
            conn.commit()
            
            log_analytics('admin_user_created', {
                'username': username, 'role': role, 'created_by': session.get('admin_username')
            }, get_real_ip(), request.user_agent.string)
            
            flash(f'管理員用戶 {username} 創建成功', 'success')
        except sqlite3.IntegrityError:
            flash('用戶名已存在', 'error')
        
        conn.close()
        
    except Exception as e:
        print(f"User creation error: {e}")
        flash('創建用戶時發生錯誤', 'error')
    
    return redirect(url_for('admin_config'))

@app.route('/admin/api/admin-users')
@require_permission('user_management')
def get_admin_users():
    """Get list of admin users"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, role, created_at, last_login, is_active
            FROM admin_users 
            ORDER BY created_at DESC
        ''')
        users = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'users': [{
                'id': user[0],
                'username': user[1],
                'role': user[2],
                'created_at': user[3],
                'last_login': user[4],
                'is_active': bool(user[5])
            } for user in users]
        })
    except Exception as e:
        print(f"Error fetching admin users: {e}")
        return jsonify({'error': 'Failed to fetch users'}), 500

@app.route('/admin/config/users/<int:user_id>/toggle', methods=['POST'])
@require_permission('user_management')
def toggle_admin_user(user_id):
    """Toggle admin user active status"""
    try:
        if user_id == session.get('admin_user_id'):
            flash('不能停用自己的帳戶', 'error')
            return redirect(url_for('admin_config'))
        
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE admin_users SET is_active = NOT is_active WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        flash('用戶狀態已更新', 'success')
    except Exception as e:
        print(f"Error toggling user: {e}")
        flash('更新用戶狀態時發生錯誤', 'error')
    
    return redirect(url_for('admin_config'))

@app.route('/admin/database/export-doctors')
@require_permission('config')
def export_doctors_database():
    """Export doctors database as CSV"""
    try:
        import io
        from flask import make_response
        
        # Create CSV content
        output = io.StringIO()
        if DOCTORS_DATA:
            # Get all column names from the first doctor record
            fieldnames = list(DOCTORS_DATA[0].keys())
            
            # Write header
            output.write(','.join(f'"{field}"' for field in fieldnames) + '\n')
            
            # Write data rows
            for doctor in DOCTORS_DATA:
                row = []
                for field in fieldnames:
                    value = doctor.get(field, '')
                    # Escape quotes and handle None values
                    if value is None:
                        value = ''
                    value = str(value).replace('"', '""')
                    row.append(f'"{value}"')
                output.write(','.join(row) + '\n')
        
        # Create response with UTF-8 BOM for better Excel compatibility
        csv_content = '\ufeff' + output.getvalue()  # Add UTF-8 BOM
        response = make_response(csv_content.encode('utf-8'))
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=doctors_database_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        log_analytics('database_export', {'type': 'doctors', 'count': len(DOCTORS_DATA)}, 
                     get_real_ip(), request.user_agent.string)
        
        return response
        
    except Exception as e:
        print(f"Export error: {e}")
        flash('導出醫生數據庫時發生錯誤', 'error')
        return redirect(url_for('admin_config'))

@app.route('/admin/database/import-doctors', methods=['POST'])
@require_permission('config')
def import_doctors_database():
    """Import doctors database from CSV"""
    try:
        if 'doctors_file' not in request.files:
            flash('請選擇要上傳的CSV文件', 'error')
            return redirect(url_for('admin_config'))
        
        file = request.files['doctors_file']
        if file.filename == '':
            flash('請選擇要上傳的CSV文件', 'error')
            return redirect(url_for('admin_config'))
        
        if not file.filename.lower().endswith('.csv'):
            flash('請上傳CSV格式的文件', 'error')
            return redirect(url_for('admin_config'))
        
        # Read and parse CSV
        import io
        import csv
        
        # Read file content
        file_content = file.read().decode('utf-8-sig')  # Handle BOM
        csv_reader = csv.DictReader(io.StringIO(file_content))
        
        new_doctors_data = []
        row_count = 0
        error_rows = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start from 2 (after header)
            row_count += 1
            try:
                # Clean and validate row data
                cleaned_row = {}
                for key, value in row.items():
                    if key:  # Skip empty column names
                        cleaned_row[key.strip()] = value.strip() if value else ''
                
                # Basic validation - ensure we have essential fields
                if not cleaned_row.get('name', '').strip():
                    error_rows.append(f"第{row_num}行: 缺少醫生姓名")
                    continue
                
                new_doctors_data.append(cleaned_row)
                
            except Exception as e:
                error_rows.append(f"第{row_num}行: 數據格式錯誤 - {str(e)}")
        
        if error_rows:
            error_msg = "導入過程中發現錯誤:\n" + "\n".join(error_rows[:10])  # Show first 10 errors
            if len(error_rows) > 10:
                error_msg += f"\n... 還有 {len(error_rows) - 10} 個錯誤"
            flash(error_msg, 'error')
            return redirect(url_for('admin_config'))
        
        if not new_doctors_data:
            flash('CSV文件中沒有有效的醫生數據', 'error')
            return redirect(url_for('admin_config'))
        
        # Backup current data
        backup_action = request.form.get('backup_action', 'replace')
        
        if backup_action == 'replace':
            # Replace all data
            global DOCTORS_DATA
            DOCTORS_DATA = new_doctors_data
            flash(f'成功導入 {len(new_doctors_data)} 位醫生數據（已替換原有數據）', 'success')
        elif backup_action == 'append':
            # Append to existing data
            DOCTORS_DATA.extend(new_doctors_data)
            flash(f'成功追加 {len(new_doctors_data)} 位醫生數據（總計 {len(DOCTORS_DATA)} 位）', 'success')
        
        # Save to file (optional - update the CSV file)
        try:
            csv_path = os.path.join('assets', 'finddoc_doctors_detailed 2.csv')
            with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                if DOCTORS_DATA:
                    fieldnames = list(DOCTORS_DATA[0].keys())
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(DOCTORS_DATA)
        except Exception as e:
            print(f"Warning: Could not save to CSV file: {e}")
        
        log_analytics('database_import', {
            'type': 'doctors', 
            'imported_count': len(new_doctors_data),
            'total_count': len(DOCTORS_DATA),
            'action': backup_action
        }, get_real_ip(), request.user_agent.string)
        
    except Exception as e:
        print(f"Import error: {e}")
        flash(f'導入醫生數據庫時發生錯誤: {str(e)}', 'error')
    
    return redirect(url_for('admin_config'))

@app.route('/admin/database/stats')
@require_admin
def get_database_stats():
    """Get database statistics"""
    try:
        stats = {
            'doctors_count': len(DOCTORS_DATA),
            'doctors_fields': list(DOCTORS_DATA[0].keys()) if DOCTORS_DATA else [],
            'sample_doctor': DOCTORS_DATA[0] if DOCTORS_DATA else None
        }
        
        # Get analytics data count
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM user_queries')
        stats['user_queries_count'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM doctor_clicks')
        stats['doctor_clicks_count'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM analytics')
        stats['analytics_events_count'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM admin_users')
        stats['admin_users_count'] = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify(stats)
        
    except Exception as e:
        print(f"Database stats error: {e}")
        return jsonify({'error': 'Failed to get database stats'}), 500

@app.route('/admin/database/export-analytics', methods=['GET', 'POST'])
@require_permission('analytics')
def export_analytics_database():
    """Export analytics data as CSV with selective options"""
    try:
        import io
        from flask import make_response
        
        # Get form data for selective export
        export_types = request.form.getlist('export_types') if request.method == 'POST' else ['analytics', 'queries', 'clicks']
        date_range = request.form.get('date_range', 'all') if request.method == 'POST' else 'all'
        start_date = request.form.get('start_date') if request.method == 'POST' else None
        end_date = request.form.get('end_date') if request.method == 'POST' else None
        
        # Build date filter condition
        date_filter = ""
        date_params = []
        
        if date_range == 'today':
            date_filter = "WHERE DATE(timestamp) = DATE('now')"
        elif date_range == 'week':
            date_filter = "WHERE timestamp >= datetime('now', '-7 days')"
        elif date_range == 'month':
            date_filter = "WHERE timestamp >= datetime('now', '-30 days')"
        elif date_range == 'custom' and start_date and end_date:
            date_filter = "WHERE DATE(timestamp) BETWEEN ? AND ?"
            date_params = [start_date, end_date]
        
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Initialize data containers
        analytics_data = []
        user_queries_data = []
        doctor_clicks_data = []
        
        # Get analytics data if requested
        if 'analytics' in export_types:
            query = f'''
                SELECT 
                    a.timestamp,
                    a.event_type,
                    a.user_ip,
                    a.user_agent,
                    a.data,
                    a.session_id
                FROM analytics a
                {date_filter}
                ORDER BY a.timestamp DESC
            '''
            cursor.execute(query, date_params)
            analytics_data = cursor.fetchall()
        
        # Get user queries data if requested
        if 'queries' in export_types:
            query = f'''
                SELECT 
                    uq.timestamp,
                    uq.age,
                    uq.symptoms,
                    uq.chronic_conditions,
                    uq.language,
                    uq.location,
                    uq.detailed_health_info,
                    uq.ai_diagnosis,
                    uq.recommended_specialty,
                    uq.matched_doctors_count,
                    uq.user_ip,
                    uq.session_id
                FROM user_queries uq
                {date_filter}
                ORDER BY uq.timestamp DESC
            '''
            cursor.execute(query, date_params)
            user_queries_data = cursor.fetchall()
        
        # Get doctor clicks data if requested
        if 'clicks' in export_types:
            query = f'''
                SELECT 
                    dc.timestamp,
                    dc.doctor_name,
                    dc.doctor_specialty,
                    dc.user_ip,
                    dc.session_id,
                    dc.query_id
                FROM doctor_clicks dc
                {date_filter}
                ORDER BY dc.timestamp DESC
            '''
            cursor.execute(query, date_params)
            doctor_clicks_data = cursor.fetchall()
        
        conn.close()
        
        # Create CSV content
        output = io.StringIO()
        
        # Export analytics events if requested
        if 'analytics' in export_types and analytics_data:
            output.write("=== ANALYTICS EVENTS ===\n")
            output.write("Timestamp,Event Type,User IP,User Agent,Data,Session ID\n")
            for row in analytics_data:
                escaped_row = []
                for field in row:
                    if field is None:
                        field = ''
                    field_str = str(field).replace('"', '""')
                    escaped_row.append(f'"{field_str}"')
                output.write(','.join(escaped_row) + '\n')
            output.write("\n")
        
        # Export user queries if requested
        if 'queries' in export_types and user_queries_data:
            output.write("=== USER QUERIES ===\n")
            output.write("Timestamp,Age,Symptoms,Chronic Conditions,Language,Location,Detailed Health Info,AI Diagnosis,Recommended Specialty,Matched Doctors Count,User IP,Session ID\n")
            for row in user_queries_data:
                escaped_row = []
                for field in row:
                    if field is None:
                        field = ''
                    field_str = str(field).replace('"', '""')
                    escaped_row.append(f'"{field_str}"')
                output.write(','.join(escaped_row) + '\n')
            output.write("\n")
        
        # Export doctor clicks if requested
        if 'clicks' in export_types and doctor_clicks_data:
            output.write("=== DOCTOR CLICKS ===\n")
            output.write("Timestamp,Doctor Name,Doctor Specialty,User IP,Session ID,Query ID\n")
            for row in doctor_clicks_data:
                escaped_row = []
                for field in row:
                    if field is None:
                        field = ''
                    field_str = str(field).replace('"', '""')
                    escaped_row.append(f'"{field_str}"')
                output.write(','.join(escaped_row) + '\n')
        
        # Check if any data was exported
        if not output.getvalue().strip():
            flash('沒有找到符合條件的數據', 'warning')
            return redirect(url_for('admin_analytics'))
        
        # Create filename with export details
        filename_parts = []
        if 'analytics' in export_types:
            filename_parts.append('events')
        if 'queries' in export_types:
            filename_parts.append('queries')
        if 'clicks' in export_types:
            filename_parts.append('clicks')
        
        filename = f"analytics_{'_'.join(filename_parts)}_{date_range}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Create response with UTF-8 BOM for better Excel compatibility
        csv_content = '\ufeff' + output.getvalue()  # Add UTF-8 BOM
        response = make_response(csv_content.encode('utf-8'))
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        log_analytics('analytics_export', {
            'export_types': export_types,
            'date_range': date_range,
            'analytics_count': len(analytics_data),
            'queries_count': len(user_queries_data),
            'clicks_count': len(doctor_clicks_data)
        }, get_real_ip(), request.user_agent.string)
        
        return response
        
    except Exception as e:
        print(f"Analytics export error: {e}")
        flash('導出分析數據時發生錯誤', 'error')
        return redirect(url_for('admin_analytics'))

@app.route('/admin/users')
@require_admin
def admin_users():
    """User management page"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Get user statistics
        cursor.execute('''
            SELECT user_ip, COUNT(*) as query_count, 
                   MIN(timestamp) as first_visit,
                   MAX(timestamp) as last_visit
            FROM user_queries 
            GROUP BY user_ip 
            ORDER BY query_count DESC
        ''')
        user_stats = cursor.fetchall()
        
        conn.close()
        
        return render_template('admin/users.html', user_stats=user_stats)
    except Exception as e:
        print(f"Users page error: {e}")
        flash('載入用戶數據時發生錯誤', 'error')
        return render_template('admin/users.html')

@app.route('/admin/api/user-details/<user_ip>')
@require_admin
def get_user_details(user_ip):
    """API endpoint to get detailed user information"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Get user query statistics
        cursor.execute('''
            SELECT COUNT(*) as total_queries,
                   COUNT(DISTINCT DATE(timestamp)) as active_days,
                   GROUP_CONCAT(DISTINCT recommended_specialty) as specialties
            FROM user_queries 
            WHERE user_ip = ?
        ''', (user_ip,))
        stats = cursor.fetchone()
        
        # Get most common specialty
        cursor.execute('''
            SELECT recommended_specialty, COUNT(*) as count
            FROM user_queries 
            WHERE user_ip = ? AND recommended_specialty IS NOT NULL
            GROUP BY recommended_specialty 
            ORDER BY count DESC 
            LIMIT 1
        ''', (user_ip,))
        top_specialty = cursor.fetchone()
        
        # Get recent queries
        cursor.execute('''
            SELECT timestamp, symptoms, recommended_specialty
            FROM user_queries 
            WHERE user_ip = ?
            ORDER BY timestamp DESC 
            LIMIT 5
        ''', (user_ip,))
        recent_queries = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'total_queries': stats[0] if stats else 0,
            'active_days': stats[1] if stats else 0,
            'top_specialty': top_specialty[0] if top_specialty else '無',
            'recent_queries': [
                {
                    'timestamp': query[0],
                    'symptoms': query[1][:50] + '...' if len(query[1]) > 50 else query[1],
                    'specialty': query[2]
                } for query in recent_queries
            ]
        })
    except Exception as e:
        print(f"User details error: {e}")
        return jsonify({'error': 'Failed to fetch user details'}), 500

@app.route('/track_click', methods=['POST'])
def track_click():
    """Track doctor link clicks and send WhatsApp notification"""
    try:
        data = request.get_json()
        doctor_name = data.get('doctor_name', '')
        doctor_specialty = data.get('doctor_specialty', '')
        query_id = session.get('last_query_id')
        session_id = session.get('session_id')
        
        # Log to database
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO doctor_clicks (doctor_name, doctor_specialty, user_ip, session_id, query_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (doctor_name, doctor_specialty, get_real_ip(), session_id, query_id))
        conn.commit()
        
        # Get user query data for WhatsApp notification
        if query_id:
            cursor.execute('''
                SELECT age, symptoms, chronic_conditions, language, location, 
                       detailed_health_info, ai_diagnosis, recommended_specialty
                FROM user_queries WHERE id = ?
            ''', (query_id,))
            user_query_row = cursor.fetchone()
            
            if user_query_row:
                user_query_data = {
                    'age': user_query_row[0],
                    'symptoms': user_query_row[1],
                    'chronic_conditions': user_query_row[2],
                    'language': user_query_row[3],
                    'location': user_query_row[4],
                    'detailed_health_info': user_query_row[5],
                    'ai_diagnosis': user_query_row[6],
                    'recommended_specialty': user_query_row[7]
                }
                
                doctor_data = {
                    'doctor_name': doctor_name,
                    'doctor_specialty': doctor_specialty
                }
                
                # Send WhatsApp notification
                message = format_diagnosis_report(user_query_data, doctor_data)
                send_whatsapp_notification(message)
        
        conn.close()
        
        # Log analytics
        log_analytics('doctor_click', {
            'doctor_name': doctor_name, 'doctor_specialty': doctor_specialty
        }, get_real_ip(), request.user_agent.string, session_id)
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Click tracking error: {e}")
        return jsonify({'error': 'Failed to track click'}), 500

@app.route('/admin/api/whatsapp-status')
@login_required
def get_whatsapp_status():
    """Get WhatsApp service status"""
    try:
        enabled = WHATSAPP_CONFIG['enabled']
        connected = False
        
        if enabled and whatsapp_client:
            try:
                # Test connection by checking if client is ready
                connected = True  # Assume connected if client exists
            except:
                connected = False
        
        return jsonify({
            'enabled': enabled,
            'connected': connected,
            'target_number': WHATSAPP_CONFIG['target_number'] if enabled else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/whatsapp-test', methods=['POST'])
@login_required
def test_whatsapp_connection():
    """Test WhatsApp connection with provided config"""
    try:
        data = request.get_json()
        socket_url = data.get('socket_url', 'http://localhost:8086')
        target_number = data.get('target_number')
        api_key = data.get('api_key', '')
        session_name = data.get('session_name', 'default')
        
        if not target_number:
            return jsonify({'success': False, 'error': '目標號碼不能為空'})
        
        # Test message
        test_message = "🔧 WhatsApp連接測試\n\n這是一條測試消息，用於驗證WhatsApp通知配置。\n\n如果您收到此消息，表示配置正確！"
        
        # Try to send test message
        try:
            if not WHATSAPP_AVAILABLE:
                return jsonify({'success': False, 'error': 'WhatsApp客戶端不可用：python-socketio未安裝'})
            
            test_client = socketio.SimpleClient()
            test_client.connect(socket_url)
            test_client.emit('sendText', {
                'to': target_number,
                'content': test_message
            })
            test_client.disconnect()
            return jsonify({'success': True, 'message': '測試消息已發送'})
        except Exception as e:
            return jsonify({'success': False, 'error': f'連接失敗: {str(e)}'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/update_whatsapp_config', methods=['POST'])
@login_required
def update_whatsapp_config():
    """Update WhatsApp configuration"""
    try:
        global WHATSAPP_CONFIG, whatsapp_client
        
        # Get form data
        enabled = request.form.get('whatsapp_enabled') == 'true'
        target_number = request.form.get('target_number', '').strip()
        socket_url = request.form.get('socket_url', 'http://localhost:8086').strip()
        api_key = request.form.get('api_key', '').strip()
        session_name = request.form.get('session_name', 'default').strip()
        
        # Validate required fields if enabled
        if enabled and not target_number:
            flash('啟用WhatsApp通知時，目標號碼不能為空', 'error')
            return redirect(url_for('admin_config'))
        
        # Update configuration
        WHATSAPP_CONFIG.update({
            'enabled': enabled,
            'target_number': target_number,
            'socket_url': socket_url,
            'api_key': api_key,
            'session_name': session_name
        })
        
        # Update .env file
        update_env_file('WHATSAPP_ENABLED', 'true' if enabled else 'false')
        update_env_file('WHATSAPP_TARGET_NUMBER', target_number)
        update_env_file('WHATSAPP_SOCKET_URL', socket_url)
        update_env_file('WHATSAPP_API_KEY', api_key)
        update_env_file('WHATSAPP_SESSION_NAME', session_name)
        
        # Save to database
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Update or insert WhatsApp config
        cursor.execute('''
            INSERT OR REPLACE INTO admin_config (key, value) 
            VALUES (?, ?)
        ''', ('whatsapp_config', json.dumps(WHATSAPP_CONFIG)))
        
        conn.commit()
        conn.close()
        
        # Reload environment variables
        load_dotenv(override=True)
        
        # Reinitialize WhatsApp client if enabled
        if enabled:
            init_whatsapp_client()
            flash('WhatsApp配置已更新並重新初始化', 'success')
        else:
            whatsapp_client = None
            flash('WhatsApp通知已停用', 'success')
        
        return redirect(url_for('admin_config'))
        
    except Exception as e:
        logger.error(f"WhatsApp config update error: {e}")
        flash(f'更新WhatsApp配置失敗: {str(e)}', 'error')
        return redirect(url_for('admin_config'))

if __name__ == '__main__':
    # Initialize database and load saved config
    init_db()
    load_ai_config_from_db()
    load_whatsapp_config_from_db()
    
    # Initialize WhatsApp client
    init_whatsapp_client()
    
    print(f"已載入 {len(DOCTORS_DATA)} 位醫生資料")
    print("正在啟動AI香港醫療配對系統...")
    print(f"當前AI提供商: {AI_CONFIG['provider']}")
    
    if WHATSAPP_CONFIG['enabled']:
        print(f"WhatsApp通知已啟用，目標號碼: {WHATSAPP_CONFIG['target_number']}")
    else:
        print("WhatsApp通知未啟用")
    
    if AI_CONFIG['provider'] == 'openrouter':
        if AI_CONFIG['openrouter']['api_key']:
            print(f"OpenRouter模型: {AI_CONFIG['openrouter']['model']}")
            print("OpenRouter API密鑰已設置")
        else:
            print("警告: 未設置OPENROUTER_API_KEY環境變數")
    elif AI_CONFIG['provider'] == 'openai':
        if AI_CONFIG['openai']['api_key']:
            print(f"OpenAI模型: {AI_CONFIG['openai']['model']}")
            print("OpenAI API密鑰已設置")
        else:
            print("警告: 未設置OPENAI_API_KEY環境變數")
    else:
        print(f"Ollama模型: {AI_CONFIG['ollama']['model']}")
        print("請確保Ollama服務正在運行：ollama serve")
    
    # Get host and port from environment variables
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '8081'))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    app.run(debug=debug, host=host, port=port)
