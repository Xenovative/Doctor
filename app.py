import sys

# Check Python version compatibility
if sys.version_info >= (3, 12):
    print("Error: This application requires Python 3.11 or lower.")
    print(f"Current Python version: {sys.version}")
    print("Please use Python 3.8 - 3.11 to run this service.")
    sys.exit(1)

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from translations import get_translation, get_available_languages, TRANSLATIONS
import pandas as pd
import requests
import json
import os
import re
import sqlite3
from datetime import datetime, timedelta
import pytz
from functools import wraps
from typing import List, Dict, Any
import hashlib
import secrets
import asyncio
import threading
import logging
from dotenv import load_dotenv, set_key
from pathlib import Path
import schedule
import time

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

# Language switching route
@app.route('/set_language/<lang>')
def set_language(lang):
    """Set user's preferred language"""
    if lang in ['zh-TW', 'zh-CN', 'en']:
        session['language'] = lang
        return jsonify({'success': True, 'language': lang})
    return jsonify({'success': False, 'error': 'Invalid language'}), 400

# API endpoint to get translations
@app.route('/api/translations/<lang>')
def get_translations_api(lang):
    """Get translations for a specific language"""
    if lang in TRANSLATIONS:
        return jsonify(TRANSLATIONS[lang])
    return jsonify(TRANSLATIONS['zh-TW'])  # Default fallback

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
    'target_number': os.getenv('WHATSAPP_TARGET_NUMBER', ''),  # Format: 852XXXXXXXX (for wa.me links)
    'session_name': os.getenv('WHATSAPP_SESSION_NAME', 'default')
}

# 時區配置
TIMEZONE_CONFIG = {
    'timezone': os.getenv('APP_TIMEZONE', 'Asia/Hong_Kong')
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
    """載入醫生資料 - 從SQLite數據庫"""
    try:
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        # 查詢所有醫生資料，優先使用中文資料，英文作為備用，按優先級和名稱排序
        cursor.execute('''
            SELECT 
                id,
                COALESCE(name_zh, name_en, name) as name,
                COALESCE(specialty_zh, specialty_en, specialty) as specialty,
                COALESCE(qualifications_zh, qualifications_en, qualifications) as qualifications,
                COALESCE(languages_zh, languages_en, languages) as languages,
                contact_numbers as phone,
                clinic_addresses as address,
                email,
                consultation_fee,
                consultation_hours,
                profile_url,
                registration_number,
                languages_available,
                name_zh,
                name_en,
                specialty_zh,
                specialty_en,
                qualifications_zh,
                qualifications_en,
                languages_zh,
                languages_en,
                COALESCE(priority_flag, 0) as priority_flag
            FROM doctors 
            ORDER BY COALESCE(priority_flag, 0) DESC, name
        ''')
        
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        doctors_data = []
        for row in rows:
            doctor_dict = dict(zip(columns, row))
            # 確保必要欄位不為空
            if not doctor_dict.get('name'):
                doctor_dict['name'] = doctor_dict.get('name_en', 'Unknown')
            if not doctor_dict.get('specialty'):
                doctor_dict['specialty'] = doctor_dict.get('specialty_en', 'General')
            doctors_data.append(doctor_dict)
        
        conn.close()
        print(f"✅ 從數據庫載入了 {len(doctors_data):,} 位醫生資料")
        return doctors_data
        
    except Exception as e:
        print(f"從數據庫載入醫生資料時發生錯誤: {e}")
        # 備用方案：嘗試從CSV載入
        return load_doctors_data_csv()

def load_doctors_data_csv():
    """備用方案：從CSV載入醫生資料"""
    csv_path = os.path.join('assets', 'finddoc_doctors_detailed 2.csv')
    try:
        df = pd.read_csv(csv_path)
        print(f"⚠️ 使用備用CSV載入了 {len(df)} 位醫生資料")
        return df.to_dict('records')
    except Exception as e:
        print(f"載入CSV醫生資料時發生錯誤: {e}")
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
        cursor.execute('SELECT config_value FROM system_config WHERE config_key = ?', ('ai_config',))
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
    try:
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
        print("=== DATABASE INITIALIZED SUCCESSFULLY ===")
        print(f"Created tables: analytics, user_queries, doctor_clicks, system_config, admin_users, admin_config")
        print(f"Default admin user: {ADMIN_USERNAME}")
        
    except Exception as e:
        print(f"=== DATABASE INITIALIZATION ERROR ===")
        print(f"Error: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        # Create a minimal fallback database
        try:
            conn = sqlite3.connect('admin_data.db')
            conn.close()
            print("=== CREATED MINIMAL DATABASE FILE ===")
        except Exception as fallback_error:
            print(f"=== FAILED TO CREATE DATABASE FILE ===")
            print(f"Fallback error: {fallback_error}")

# Initialize database on startup
print("=== STARTING DATABASE INITIALIZATION ===")
init_db()

# Load configurations from database
print("=== LOADING AI CONFIG FROM DATABASE ===")
load_ai_config_from_db()
print("=== LOADING WHATSAPP CONFIG FROM DATABASE ===")
load_whatsapp_config_from_db()
print("=== APP STARTUP COMPLETE ===")

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

def get_app_timezone():
    """Get configured timezone"""
    try:
        return pytz.timezone(TIMEZONE_CONFIG['timezone'])
    except:
        return pytz.timezone('Asia/Hong_Kong')

def get_current_time():
    """Get current time in Hong Kong timezone"""
    hk_tz = pytz.timezone('Asia/Hong_Kong')
    return datetime.now(hk_tz)

def format_timestamp(timestamp_str):
    """Format timestamp string to clean readable format"""
    try:
        # Parse the timestamp string
        if isinstance(timestamp_str, str):
            # Handle ISO format with timezone
            if '+' in timestamp_str or 'T' in timestamp_str:
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        else:
            dt = timestamp_str
        
        # Convert to Hong Kong timezone if needed
        if dt.tzinfo is None:
            hk_tz = pytz.timezone('Asia/Hong_Kong')
            dt = hk_tz.localize(dt)
        elif dt.tzinfo != pytz.timezone('Asia/Hong_Kong'):
            dt = dt.astimezone(pytz.timezone('Asia/Hong_Kong'))
        
        # Format as clean readable string
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger.error(f"Error formatting timestamp {timestamp_str}: {e}")
        return str(timestamp_str)

def format_diagnosis_report_full(user_query_data: dict, doctor_data: dict) -> str:
    """格式化完整診斷報告為HTML顯示"""
    timestamp = get_current_time().strftime('%Y-%m-%d %H:%M:%S')
    
    # Format gender display
    gender = user_query_data.get('gender', '')
    gender_display = f"生理性別: {gender}" if gender else "生理性別: 未提供"
    
    message = f"""🏥 AI醫療診斷報告
📅 時間: {timestamp}

👤 患者信息
年齡: {user_query_data.get('age', 'N/A')}歲
{gender_display}
症狀: {user_query_data.get('symptoms', 'N/A')}
語言: {user_query_data.get('language', 'N/A')}
地區: {user_query_data.get('location', 'N/A')}

🔍 AI診斷結果
推薦專科: {user_query_data.get('recommended_specialty', 'N/A')}

👨‍⚕️ 選擇的醫生
醫生姓名: {doctor_data.get('doctor_name', 'N/A')}
專科: {doctor_data.get('doctor_specialty', 'N/A')}

📊 完整診斷
{user_query_data.get('ai_diagnosis', 'N/A')}

免責聲明：此分析僅供參考，不能替代專業醫療診斷，請務必諮詢合格醫生。

---
Doctor-AI香港醫療配對系統"""
    
    return message

def format_whatsapp_message(doctor_data: dict, report_url: str) -> str:
    """格式化WhatsApp消息，包含診斷報告鏈接"""
    message = f"""AI醫療診斷報告

您好！我通過AI醫療配對系統選擇了您作為我的醫生。

醫生信息
姓名: {doctor_data.get('doctor_name', 'N/A')}
專科: {doctor_data.get('doctor_specialty', 'N/A')}

完整診斷報告請查看：
{report_url}

期待您的專業建議，謝謝！

---
Doctor-AI香港醫療配對系統"""
    
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

def log_analytics(event_type: str, data: Dict, user_ip: str, user_agent: str, session_id: str = None):
    """Log analytics data to database"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Check if analytics table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analytics'")
        if not cursor.fetchone():
            print("Analytics table not found, reinitializing database...")
            conn.close()
            init_db()
            conn = sqlite3.connect('admin_data.db')
            cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO analytics (event_type, user_ip, user_agent, data, session_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (event_type, user_ip, user_agent, json.dumps(data), session_id, get_current_time().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Analytics logging error: {e}")
        # Try to reinitialize database if it's corrupted
        try:
            init_db()
        except:
            pass

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

def generate_user_summary(age: int, gender: str, symptoms: str, chronic_conditions: str, detailed_health_info: Dict) -> str:
    """生成用戶輸入數據摘要"""
    summary_parts = []
    
    # 基本信息
    summary_parts.append(f"年齡：{age}歲")
    if gender:
        summary_parts.append(f"性別：{gender}")
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
            "temperature": 0.3,
            "top_p": 0.9
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
            "temperature": 0.3,
            "top_p": 0.9
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

def get_available_specialties() -> List[str]:
    """獲取資料庫中所有可用的專科"""
    try:
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        # Try different specialty columns with encoding handling
        cursor.execute("SELECT DISTINCT specialty FROM doctors WHERE specialty IS NOT NULL AND specialty != '' AND LENGTH(specialty) > 0")
        specialties = []
        for row in cursor.fetchall():
            try:
                if row[0] and isinstance(row[0], str) and len(row[0].strip()) > 0:
                    specialties.append(row[0].strip())
            except (UnicodeDecodeError, AttributeError):
                continue
        conn.close()
        
        # Remove duplicates and sort
        specialties = sorted(list(set(specialties)))
        
        if not specialties:
            # Fallback list
            specialties = ['內科', '外科', '小兒科', '婦產科', '骨科', '皮膚科', '眼科', '耳鼻喉科', '精神科', '神經科', '心臟科', '急診科']
        
        return specialties
    except Exception as e:
        print(f"Error fetching specialties: {e}")
        return ['內科', '外科', '小兒科', '婦產科', '骨科', '皮膚科', '眼科', '耳鼻喉科', '精神科', '神經科', '心臟科', '急診科']

def validate_symptoms_with_llm(symptoms: str, user_language: str = 'zh-TW') -> Dict[str, Any]:
    """使用LLM驗證症狀描述是否有效"""
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return {'valid': True, 'message': '症狀驗證服務不可用，將繼續處理'}
        
        # Get translations for the prompt
        t = lambda key: get_translation(key, user_language)
        
        prompt = f"""
你是一個醫療症狀驗證專家。請分析以下症狀描述，判斷是否為有效的醫療症狀。

症狀描述：{symptoms}

請評估：
1. 這些是否為真實的醫療症狀？
2. 描述是否合理和具體？
3. 是否包含不相關或無意義的內容？

無效症狀的例子：
- 測試、test、123、隨便寫的
- 非醫療相關的詞語（如：開心、工作、吃飯）
- 明顯的垃圾文字或無意義字符
- 過於簡單或不具體的描述（如：不舒服、有問題）

請以JSON格式回應：
{{
    "valid": true/false,
    "confidence": 0.0-1.0,
    "issues": ["問題列表"],
    "suggestions": ["改善建議"]
}}
"""
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {'role': 'system', 'content': '你是一個專業的醫療症狀驗證助手。請仔細分析症狀描述的有效性。'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 500,
            'temperature': 0.3
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            try:
                # Parse JSON response
                validation_result = json.loads(content)
                return {
                    'valid': validation_result.get('valid', True),
                    'confidence': validation_result.get('confidence', 0.5),
                    'issues': validation_result.get('issues', []),
                    'suggestions': validation_result.get('suggestions', []),
                    'message': '症狀驗證完成'
                }
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                is_valid = 'true' in content.lower() and 'valid' in content.lower()
                return {
                    'valid': is_valid,
                    'confidence': 0.7,
                    'issues': [],
                    'suggestions': [],
                    'message': '症狀驗證完成（簡化結果）'
                }
        else:
            logger.error(f"Symptom validation API error: {response.status_code}")
            return {'valid': True, 'message': '症狀驗證服務暫時不可用，將繼續處理'}
            
    except Exception as e:
        logger.error(f"Error validating symptoms: {e}")
        return {'valid': True, 'message': '症狀驗證過程中出現錯誤，將繼續處理'}

def diagnose_symptoms(age: int, gender: str, symptoms: str, chronic_conditions: str = '', detailed_health_info: Dict = None, user_language: str = 'zh-TW') -> Dict[str, str]:
    """使用AI診斷症狀"""
    
    if detailed_health_info is None:
        detailed_health_info = {}
    
    # 構建詳細健康信息
    health_details = []
    if gender:
        health_details.append(f"性別：{gender}")
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
    
    # Get translations for the user's language
    t = lambda key: get_translation(key, user_language)
    
    # Build health info with translated labels
    health_info = "\n    - ".join(health_details) if health_details else t('no_special_health_info')
    
    # Get available specialties from database
    available_specialties = get_available_specialties()
    specialty_list = "、".join(available_specialties)
    
    # Build AI diagnosis prompt in user's language with consistency instructions
    diagnosis_prompt = f"""
    {t('diagnosis_prompt_intro')}

    {t('patient_data')}
    - {t('age_label')}{age}{t('years_old')}
    - {t('main_symptoms')}{symptoms}
    - {health_info}

    {t('please_provide')}
    1. {t('possible_diagnosis')}
    2. {t('recommended_specialty')}
    3. {t('severity_assessment')}
    4. {t('emergency_needed')}
    5. {t('general_advice')}

    **{t('important_guidelines')}**
    - {t('mental_health_guideline')}
    - {t('trauma_guideline')}
    - {t('emergency_guideline')}
    - {t('specialty_guideline')}

    **一致性要求 (Consistency Requirements):**
    - 必須嚴格按照以下格式回答，不可偏離
    - 嚴重程度只能是：輕微、中等、嚴重 (三選一)
    - 緊急程度只能是：是、否 (二選一)
    - 專科名稱必須從以下可用專科中選擇：{specialty_list}
    - 不可推薦資料庫中不存在的專科
    - 回答必須簡潔明確，避免模糊用詞

    {t('response_language')}
    
    **嚴格格式要求 (Strict Format Requirements):**
    {t('diagnosis_format')}
    {t('specialty_format')}
    {t('severity_format')}
    {t('emergency_format')}
    {t('advice_format')}
    
    {t('disclaimer')}
    """
    
    # 獲取AI診斷
    diagnosis_response = call_ai_api(diagnosis_prompt)
    
    # 解析診斷結果
    recommended_specialties = extract_specialties_from_diagnosis(diagnosis_response)
    recommended_specialty = recommended_specialties[0] if recommended_specialties else '內科'
    severity_level = extract_severity_from_diagnosis(diagnosis_response)
    emergency_needed = check_emergency_needed(diagnosis_response)
    
    # Debug logging
    print(f"DEBUG - AI Response: {diagnosis_response[:200]}...")
    print(f"DEBUG - Extracted specialties: {recommended_specialties}")
    print(f"DEBUG - Primary specialty: {recommended_specialty}")
    print(f"DEBUG - Severity level: {severity_level}")
    print(f"DEBUG - Emergency needed: {emergency_needed}")
    
    return {
        'diagnosis': diagnosis_response,
        'recommended_specialty': recommended_specialty,
        'recommended_specialties': recommended_specialties,
        'severity_level': severity_level,
        'emergency_needed': emergency_needed
    }

def analyze_symptoms_and_match(age: int, gender: str, symptoms: str, chronic_conditions: str, language: str, location: str, detailed_health_info: Dict = None, location_details: Dict = None) -> Dict[str, Any]:
    """使用AI分析症狀並配對醫生"""
    
    if detailed_health_info is None:
        detailed_health_info = {}
    
    # 生成用戶數據摘要
    user_summary = generate_user_summary(age, gender, symptoms, chronic_conditions, detailed_health_info)
    
    # Get user's language from session or use the language parameter passed in
    user_language = session.get('language', language if language else 'zh-TW')
    
    # 第一步：驗證症狀有效性
    symptom_validation = validate_symptoms_with_llm(symptoms, user_language)
    
    if not symptom_validation.get('valid', True):
        return {
            'diagnosis': '症狀驗證失敗',
            'recommended_specialty': '無',
            'doctors': [],
            'user_summary': user_summary,
            'emergency_needed': False,
            'severity_level': 'low',
            'validation_error': True,
            'validation_issues': symptom_validation.get('issues', []),
            'validation_suggestions': symptom_validation.get('suggestions', []),
            'validation_message': '您輸入的內容不是有效的醫療症狀。請重新輸入真實的身體不適症狀，例如頭痛、發燒、咳嗽等。'
        }
    
    # 第二步：AI診斷 (pass user language)
    diagnosis_result = diagnose_symptoms(age, gender, symptoms, chronic_conditions, detailed_health_info, user_language)
    
    # 第二步：檢查是否需要緊急醫療處理
    print(f"DEBUG - Emergency check: emergency_needed={diagnosis_result.get('emergency_needed', False)}, severity_level={diagnosis_result.get('severity_level')}")
    
    if diagnosis_result.get('emergency_needed', False):
        print("DEBUG - Emergency case detected, routing to emergency doctors")
        # 緊急情況：優先推薦急診科和醫院
        emergency_doctors = filter_doctors('急診科', language, location, symptoms, diagnosis_result['diagnosis'], location_details)
        # 如果沒有急診科醫生，推薦內科醫生但標記為緊急
        if not emergency_doctors:
            emergency_doctors = filter_doctors('內科', language, location, symptoms, diagnosis_result['diagnosis'], location_details)
        
        # 為緊急醫生添加緊急標記
        for doctor in emergency_doctors:
            doctor['is_emergency'] = True
            doctor['emergency_message'] = get_translation('emergency_care_needed', user_language)
        
        matched_doctors = emergency_doctors
    else:
        print("DEBUG - Normal case, routing to specialty doctors")
        # 一般情況：根據診斷結果推薦多個相關專科的醫生
        all_matched_doctors = []
        recommended_specialties = diagnosis_result.get('recommended_specialties', [diagnosis_result['recommended_specialty']])
        print(f"DEBUG - Will search for specialties: {recommended_specialties}")
        
        for specialty in recommended_specialties:
            specialty_doctors = filter_doctors(
                specialty, 
                language, 
                location, 
                symptoms, 
                diagnosis_result['diagnosis'],
                location_details
            )
            
            print(f"DEBUG - Found {len(specialty_doctors)} doctors for specialty: {specialty}")
            
            # 為每個醫生添加專科標記，用於排序
            for doctor in specialty_doctors:
                doctor['matched_specialty'] = specialty
                doctor['is_primary_specialty'] = (specialty == diagnosis_result['recommended_specialty'])
            
            all_matched_doctors.extend(specialty_doctors)
        
        # 去除重複醫生並按優先級排序
        seen_names = set()
        unique_doctors = []
        
        # 首先添加主要專科的醫生
        for doctor in all_matched_doctors:
            if doctor.get('is_primary_specialty', False) and doctor['name'] not in seen_names:
                seen_names.add(doctor['name'])
                unique_doctors.append(doctor)
        
        # 然後添加其他專科的醫生
        for doctor in all_matched_doctors:
            if not doctor.get('is_primary_specialty', False) and doctor['name'] not in seen_names:
                seen_names.add(doctor['name'])
                unique_doctors.append(doctor)
        
        matched_doctors = unique_doctors[:15]  # 增加到15位醫生以包含多個專科
        
        # 確保非緊急情況下不設置緊急標記
        for doctor in matched_doctors:
            doctor['is_emergency'] = False
    
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
        matched_doctors = unique_doctors[:15]  # 限制最多15位醫生以包含多個專科
    
    return {
        'user_summary': user_summary,
        'diagnosis': diagnosis_result['diagnosis'],
        'recommended_specialty': diagnosis_result['recommended_specialty'],
        'severity_level': diagnosis_result.get('severity_level', 'mild'),
        'emergency_needed': diagnosis_result.get('emergency_needed', False),
        'doctors': matched_doctors
    }

def extract_specialties_from_diagnosis(diagnosis_text: str) -> List[str]:
    """從診斷文本中提取推薦的專科"""
    if not diagnosis_text:
        return ['內科']
    
    # Get available specialties from database
    available_specialties = get_available_specialties()
    
    # Create dynamic mapping based on database specialties
    specialty_mapping = {}
    for specialty in available_specialties:
        # Create variations for each specialty
        variations = [specialty]
        
        # Add common English translations and variations
        if '內科' in specialty:
            variations.extend(['internal medicine', 'general medicine', 'family medicine'])
        elif '外科' in specialty:
            variations.extend(['surgery', 'general surgery'])
        elif '小兒科' in specialty or '兒科' in specialty:
            variations.extend(['pediatrics', 'pediatric'])
        elif '婦產科' in specialty:
            variations.extend(['obstetrics', 'gynecology', 'ob/gyn', 'obgyn'])
        elif '骨科' in specialty:
            variations.extend(['orthopedics', 'orthopedic'])
        elif '皮膚科' in specialty:
            variations.extend(['dermatology', 'dermatologic'])
        elif '眼科' in specialty:
            variations.extend(['ophthalmology', 'eye'])
        elif '耳鼻喉' in specialty:
            variations.extend(['ent', 'otolaryngology'])
        elif '精神科' in specialty:
            variations.extend(['psychiatry', 'psychiatric', 'mental health'])
        elif '神經科' in specialty:
            variations.extend(['neurology', 'neurologic'])
        elif '心臟科' in specialty or '心血管' in specialty:
            variations.extend(['cardiology', 'cardiac'])
        elif '急診' in specialty:
            variations.extend(['emergency', 'emergency medicine', 'er'])
        elif '感染' in specialty:
            variations.extend(['infectious disease', 'infection'])
        elif '腎臟科' in specialty:
            variations.extend(['nephrology', 'kidney'])
        elif '胃腸科' in specialty or '消化科' in specialty:
            variations.extend(['gastroenterology', 'digestive'])
        elif '呼吸科' in specialty:
            variations.extend(['pulmonology', 'respiratory'])
        elif '血液科' in specialty:
            variations.extend(['hematology', 'blood'])
        elif '腫瘤科' in specialty:
            variations.extend(['oncology', 'cancer'])
        elif '風濕科' in specialty:
            variations.extend(['rheumatology', 'rheumatic'])
        elif '內分泌' in specialty:
            variations.extend(['endocrinology', 'hormone'])
        elif '泌尿科' in specialty:
            variations.extend(['urology', 'urologic'])
        elif '放射科' in specialty:
            variations.extend(['radiology', 'imaging'])
        elif '病理科' in specialty:
            variations.extend(['pathology'])
        elif '麻醉科' in specialty:
            variations.extend(['anesthesiology'])
        elif '復健科' in specialty:
            variations.extend(['rehabilitation', 'physical medicine'])
        elif '核醫科' in specialty:
            variations.extend(['nuclear medicine'])
        elif '整形外科' in specialty:
            variations.extend(['plastic surgery'])
        elif '神經外科' in specialty:
            variations.extend(['neurosurgery'])
        elif '胸腔外科' in specialty:
            variations.extend(['thoracic surgery'])
        elif '心臟外科' in specialty:
            variations.extend(['cardiac surgery'])
        elif '血管外科' in specialty:
            variations.extend(['vascular surgery'])
        elif '大腸直腸外科' in specialty:
            variations.extend(['colorectal surgery'])
        
        specialty_mapping[specialty] = {'variations': variations}
    
    # 使用正則表達式提取專科資訊 (支援中英文)
    specialty_patterns = [
        r'推薦專科[：:]\s*([^\n\r]+)',
        r'建議專科[：:]\s*([^\n\r]+)', 
        r'專科[：:]\s*([^\n\r]+)',
        r'科別[：:]\s*([^\n\r]+)',
        r'Recommended specialty[：:]?\s*([^\n\r]+)',
        r'Specialty[：:]?\s*([^\n\r]+)',
        r'([^。\n\r]*(?:科|Specialist|Medicine|Surgery|ology|ics))\s*(?:醫師|專科|doctor)?',
    ]
    
    found_specialties = set()
    
    # 首先嘗試從明確的專科推薦中提取
    for pattern in specialty_patterns:
        matches = re.findall(pattern, diagnosis_text, re.IGNORECASE)
        if matches:
            recommended_specialty = matches[0].strip()
            print(f"DEBUG - Specialty pattern matched: '{pattern}' -> '{recommended_specialty}'")
            
            # 清理提取的專科名稱
            recommended_specialty = re.sub(r'\s*(or|或)\s*.*$', '', recommended_specialty, flags=re.IGNORECASE).strip()
            
            # 尋找匹配的標準專科名稱
            for standard_specialty, specialty_info in specialty_mapping.items():
                for variation in specialty_info['variations']:
                    if variation.lower() in recommended_specialty.lower():
                        found_specialties.add(standard_specialty)
                        print(f"DEBUG - Primary specialty found: '{variation}' -> '{standard_specialty}'")
                        break
            break
    
    # 如果沒有找到明確的專科推薦，搜索關鍵字
    if not found_specialties:
        print("DEBUG - No specialty pattern matched, searching for keywords")
        text_lower = diagnosis_text.lower()
        for standard_specialty, specialty_info in specialty_mapping.items():
            for variation in specialty_info['variations']:
                if variation.lower() in text_lower:
                    found_specialties.add(standard_specialty)
                    print(f"DEBUG - Keyword match found: '{variation}' -> '{standard_specialty}'")
    
    # 如果找到了主要專科，添加相關專科
    if found_specialties:
        primary_specialty = list(found_specialties)[0]  # 取第一個作為主要專科
        related_specialties = specialty_mapping.get(primary_specialty, {}).get('related', [])
        
        print(f"DEBUG - Primary specialty: {primary_specialty}, Related: {related_specialties}")
        # 添加最多2個相關專科，避免推薦太多
        for related in related_specialties[:2]:
            if related in specialty_mapping:  # 確保相關專科存在
                found_specialties.add(related)
                print(f"DEBUG - Added related specialty: {related}")
            else:
                print(f"DEBUG - Skipped invalid related specialty: {related}")
        
        result = list(found_specialties)
        print(f"DEBUG - Final specialties: {result}")
        return result
    
    # 如果沒有找到任何專科，返回內科作為默認
    print("DEBUG - No specialty keywords found, defaulting to Internal Medicine")
    return ['內科']

def extract_specialty_from_diagnosis(diagnosis_text: str) -> str:
    """從診斷文本中提取推薦的專科（單一專科，保留兼容性）"""
    specialties = extract_specialties_from_diagnosis(diagnosis_text)
    return specialties[0] if specialties else '內科'

def extract_specialty_from_ai_response(ai_response: str) -> str:
    """從AI回應中提取推薦的專科（保留兼容性）"""
    return extract_specialty_from_diagnosis(ai_response)

def extract_severity_from_diagnosis(diagnosis_text: str) -> str:
    """從診斷文本中提取嚴重程度"""
    if not diagnosis_text:
        return 'mild'
    
    text_lower = diagnosis_text.lower()
    
    # First check for explicit severity statements
    explicit_severity_patterns = [
        ('嚴重程度：輕微', 'mild'),
        ('嚴重程度：中等', 'moderate'), 
        ('嚴重程度：嚴重', 'severe'),
        ('severity: mild', 'mild'),
        ('severity: moderate', 'moderate'),
        ('severity: severe', 'severe')
    ]
    
    for pattern, severity in explicit_severity_patterns:
        if pattern in text_lower:
            print(f"DEBUG - Explicit severity found: '{pattern}' -> {severity}")
            return severity
    
    # Check for non-emergency indicators that should override severity keywords
    non_emergency_patterns = [
        '不需要緊急就醫', '非緊急', '不緊急', 'not emergency', 'no emergency needed',
        '不需要急診', '無需緊急', 'non-urgent', 'not urgent'
    ]
    
    is_non_emergency = False
    for pattern in non_emergency_patterns:
        if pattern in text_lower:
            is_non_emergency = True
            print(f"DEBUG - Non-emergency pattern found in severity check: '{pattern}'")
            break
    
    emergency_keywords = [
        'emergency', '緊急', '急診', 'urgent', '嚴重', 'severe', 'critical', '危急',
        'life-threatening', '威脅生命', 'immediate', '立即', 'high risk', '高風險'
    ]
    
    moderate_keywords = [
        'moderate', '中等', '中度', 'medium', '適中', '一般嚴重'
    ]
    
    found_emergency = []
    for keyword in emergency_keywords:
        if keyword in text_lower:
            found_emergency.append(keyword)
    
    found_moderate = []
    for keyword in moderate_keywords:
        if keyword in text_lower:
            found_moderate.append(keyword)
    
    print(f"DEBUG - Severity check - Emergency keywords found: {found_emergency}")
    print(f"DEBUG - Severity check - Moderate keywords found: {found_moderate}")
    
    # If explicitly marked as non-emergency, don't return severe even if keywords found
    if is_non_emergency and found_emergency:
        print("DEBUG - Non-emergency override: downgrading from severe to moderate")
        return 'moderate'
    
    if found_emergency:
        return 'severe'
    
    if found_moderate:
        return 'moderate'
    
    return 'mild'

def check_emergency_needed(diagnosis_text: str) -> bool:
    """檢查是否需要緊急就醫"""
    if not diagnosis_text:
        return False
    
    text_lower = diagnosis_text.lower()
    
    # First check for explicit non-emergency statements
    non_emergency_patterns = [
        '不需要緊急就醫', '非緊急', '不緊急', 'not emergency', 'no emergency needed',
        '不需要急診', '無需緊急', 'non-urgent', 'not urgent',
        '緊急程度：否', '緊急程度: 否', 'emergency: no', 'emergency:no'
    ]
    
    for pattern in non_emergency_patterns:
        if pattern in text_lower:
            print(f"DEBUG - Non-emergency pattern found: '{pattern}' - overriding emergency detection")
            return False
    
    # Strong emergency indicators that should trigger emergency response
    strong_emergency_indicators = [
        'call emergency', '撥打急救', 'go to emergency', '前往急診',
        'emergency room', '急診室', 'hospital immediately', '立即住院',
        'life-threatening', '威脅生命', 'critical condition', '危急狀況',
        '999', '911', '112', 'ambulance', '救護車', '緊急護理'
    ]
    
    # Weaker indicators that need context checking
    contextual_indicators = [
        'seek immediate', 'urgent care'
    ]
    
    found_strong = []
    found_contextual = []
    
    for indicator in strong_emergency_indicators:
        if indicator in text_lower:
            found_strong.append(indicator)
    
    for indicator in contextual_indicators:
        if indicator in text_lower:
            found_contextual.append(indicator)
    
    # If we have strong indicators, it's definitely emergency
    if found_strong:
        print(f"DEBUG - Strong emergency indicators found: {found_strong}")
        return True
    
    # For contextual indicators, check if they appear in conditional statements
    if found_contextual:
        # Check if the contextual indicator appears in conditional context
        conditional_patterns = [
            '若.*惡化.*立即就醫', '如果.*嚴重.*立即就醫', 'if.*worse.*seek immediate',
            '症狀持續.*立即就醫', '持續或惡化.*立即就醫', '建議.*多休息.*並.*立即就醫',
            '保持.*水分.*立即就醫', '避免.*刺激.*立即就醫'
        ]
        
        is_conditional = False
        for pattern in conditional_patterns:
            if re.search(pattern, text_lower):
                is_conditional = True
                print(f"DEBUG - Contextual emergency indicator in conditional statement: '{pattern}'")
                break
        
        if is_conditional:
            print(f"DEBUG - Emergency indicator '{found_contextual}' is conditional, not immediate emergency")
            return False
        else:
            print(f"DEBUG - Direct emergency indicators found: {found_contextual}")
            return True
    
    print("DEBUG - No emergency indicators found")
    return False

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
        
        # Get UI language from session for doctor prioritization
        ui_language = session.get('language', 'zh-TW')

        # Language-based doctor prioritization
        doctor_languages = doctor.get('languages', '')
        if doctor_languages and not pd.isna(doctor_languages):
            doctor_languages = str(doctor_languages)

            if ui_language == 'en':
                # For English UI, prioritize doctors who speak English
                if safe_str_check(doctor_languages, 'English') or safe_str_check(doctor_languages, '英文'):
                    score += 20
                    match_reasons.append("English-speaking doctor (English preference)")
            else:
                # For Chinese UI, prioritize doctors who speak Chinese
                if safe_str_check(doctor_languages, '中文') or safe_str_check(doctor_languages, '國語') or safe_str_check(doctor_languages, '粵語'):
                    score += 10
                    match_reasons.append("Chinese-speaking doctor (Chinese preference)")
        
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
        
        # 加入優先級別到匹配分數
        priority_flag = doctor.get('priority_flag', 0)
        if priority_flag and not pd.isna(priority_flag):
            priority_bonus = int(priority_flag) * 10  # 每級優先級加10分
            score += priority_bonus
            if priority_bonus > 0:
                match_reasons.append(f"優先醫生 (級別 {priority_flag})")
        
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
    
    # 按匹配分數排序 (優先級已包含在分數中)
    matched_doctors.sort(key=lambda x: x['match_score'], reverse=True)
    
    # 返回前20名供分頁使用
    return matched_doctors[:20]

@app.route('/')
def index():
    """主頁"""
    # Get user's preferred language from session or default to zh-TW
    current_lang = session.get('language', 'zh-TW')
    
    # Log page visit
    log_analytics('page_visit', {'page': 'index', 'language': current_lang}, 
                 get_real_ip(), request.user_agent.string, session.get('session_id'))
    return render_template('index.html', current_lang=current_lang, translations=TRANSLATIONS.get(current_lang, TRANSLATIONS['zh-TW']))

@app.route('/find_doctor', methods=['POST'])
def find_doctor():
    """處理醫生搜索請求"""
    try:
        data = request.get_json()
        age = int(data.get('age', 0))
        gender = data.get('gender', '')
        symptoms = data.get('symptoms', '')
        chronic_conditions = data.get('chronicConditions', '')
        language = data.get('language', '')
        location = data.get('location', '')
        location_details = data.get('locationDetails', {})
        detailed_health_info = data.get('detailedHealthInfo', {})
        ui_language = data.get('uiLanguage', 'zh-TW')  # Get UI language for diagnosis
        
        # 驗證輸入 - gender is optional for backward compatibility
        if not all([age, symptoms, language, location]):
            return jsonify({'error': '請填寫所有必要資料'}), 400
        
        # Set session language for diagnosis
        session['language'] = ui_language
        
        # 使用AI分析症狀並配對醫生 (傳遞location_details)
        # Handle backward compatibility - pass empty string if gender is None
        gender_safe = gender or ''
        result = analyze_symptoms_and_match(age, gender_safe, symptoms, chronic_conditions, language, location, detailed_health_info, location_details)
        
        # Log user query to database
        session_id = session.get('session_id', secrets.token_hex(16))
        session['session_id'] = session_id
        
        try:
            conn = sqlite3.connect('admin_data.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_queries 
                (age, gender, symptoms, chronic_conditions, language, location, detailed_health_info, 
                 ai_diagnosis, recommended_specialty, matched_doctors_count, user_ip, session_id, diagnosis_report, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (age, gender_safe, symptoms, chronic_conditions, language, location, 
                  json.dumps(detailed_health_info), result['diagnosis'], 
                  result['recommended_specialty'], len(result['doctors']), 
                  get_real_ip(), session_id, result['diagnosis'], get_current_time().isoformat()))
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
        raw_recent_queries = cursor.fetchall()
        
        # Format timestamps for recent queries
        recent_queries = []
        for query in raw_recent_queries:
            formatted_query = list(query)
            formatted_query[0] = format_timestamp(query[0])  # Format timestamp
            recent_queries.append(tuple(formatted_query))
        
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
            SELECT id, timestamp, age, gender, symptoms, language, location, 
                   recommended_specialty, matched_doctors_count, user_ip
            FROM user_queries 
            ORDER BY timestamp DESC 
            LIMIT 50
        ''')
        raw_queries = cursor.fetchall()
        
        # Format timestamps for user queries
        user_queries = []
        for query in raw_queries:
            formatted_query = list(query)
            formatted_query[1] = format_timestamp(query[1])  # Format timestamp
            user_queries.append(tuple(formatted_query))
        
        # Get gender statistics for dashboard
        cursor.execute('''
            SELECT gender, COUNT(*) as count
            FROM user_queries 
            WHERE gender IS NOT NULL AND gender != ''
            GROUP BY gender 
            ORDER BY count DESC
        ''')
        gender_stats = cursor.fetchall()
        
        # Get location statistics for dashboard
        cursor.execute('''
            SELECT location, COUNT(*) as count
            FROM user_queries 
            WHERE location IS NOT NULL AND location != ''
            GROUP BY location 
            ORDER BY count DESC
            LIMIT 10
        ''')
        location_stats = cursor.fetchall()
        
        # Get doctor clicks
        cursor.execute('''
            SELECT dc.timestamp, dc.doctor_name, dc.doctor_specialty, 
                   uq.symptoms, dc.user_ip
            FROM doctor_clicks dc
            LEFT JOIN user_queries uq ON dc.query_id = uq.id
            ORDER BY dc.timestamp DESC 
            LIMIT 50
        ''')
        raw_clicks = cursor.fetchall()
        
        # Format timestamps for doctor clicks
        doctor_clicks = []
        for click in raw_clicks:
            formatted_click = list(click)
            formatted_click[0] = format_timestamp(click[0])  # Format timestamp
            doctor_clicks.append(tuple(formatted_click))
        
        conn.close()
        
        return render_template('admin/analytics.html',
                             event_stats=event_stats,
                             user_queries=user_queries,
                             doctor_clicks=doctor_clicks,
                             gender_stats=gender_stats,
                             location_stats=location_stats)
    except Exception as e:
        print(f"Analytics error: {e}")
        flash('載入分析數據時發生錯誤', 'error')
        return render_template('admin/analytics.html')

@app.route('/admin/config', methods=['GET', 'POST'])
@login_required
def admin_config():
    """Admin configuration page"""
    return render_template('admin/config.html', 
                         ai_config=AI_CONFIG,
                         whatsapp_config=WHATSAPP_CONFIG,
                         timezone_config=TIMEZONE_CONFIG)

@app.route('/admin/update-timezone', methods=['POST'])
@login_required
def update_timezone_config():
    """Update timezone configuration"""
    try:
        timezone = request.form.get('timezone', 'Asia/Hong_Kong')
        
        # Validate timezone
        try:
            pytz.timezone(timezone)
        except:
            flash('無效的時區設定', 'error')
            return redirect(url_for('admin_config'))
        
        # Update environment variable
        env_path = Path('.env')
        if env_path.exists():
            set_key(env_path, 'APP_TIMEZONE', timezone)
        else:
            with open('.env', 'w') as f:
                f.write(f'APP_TIMEZONE={timezone}\n')
        
        # Update runtime config
        TIMEZONE_CONFIG['timezone'] = timezone
        
        flash(f'時區已更新為 {timezone}', 'success')
        
    except Exception as e:
        print(f"Timezone update error: {e}")
        flash('更新時區設定時發生錯誤', 'error')
    
    return redirect(url_for('admin_config'))

@app.route('/admin/api/openai-models')
@require_admin
def get_openai_models_api():
    """API endpoint to fetch OpenAI models"""
    # Get API key from query parameter or use current config
    api_key = request.args.get('api_key')
    models = get_openai_models(api_key)
    return jsonify({'models': models})

@app.route('/admin/api/database-stats')
@require_admin
def get_database_stats():
    """API endpoint to get database statistics"""
    try:
        # Get doctors count from loaded data
        doctors_count = len(DOCTORS_DATA) if DOCTORS_DATA else 0
        
        # Get analytics data from admin_data.db
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Get today's queries
        today = get_current_time().strftime('%Y-%m-%d')
        try:
            cursor.execute('SELECT COUNT(*) FROM user_queries WHERE DATE(timestamp) = ?', (today,))
            queries_today = cursor.fetchone()[0]
        except:
            queries_today = 0
        
        # Get total queries
        try:
            cursor.execute('SELECT COUNT(*) FROM user_queries')
            total_queries = cursor.fetchone()[0]
        except:
            total_queries = 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'doctors_count': doctors_count,
                'queries_today': queries_today,
                'total_queries': total_queries
            }
        })
    except Exception as e:
        print(f"Database stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/users')
@require_admin
def get_admin_users_api():
    """API endpoint to get admin users list"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Check if admin_users table exists
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='admin_users'
        ''')
        
        if not cursor.fetchone():
            conn.close()
            return jsonify({
                'success': True,
                'users': []
            })
        
        # Check if all columns exist
        cursor.execute('PRAGMA table_info(admin_users)')
        columns = [col[1] for col in cursor.fetchall()]
        
        # Build query based on available columns
        base_columns = ['id', 'username', 'role']
        optional_columns = ['email', 'display_name', 'is_active', 'created_at']
        
        select_columns = base_columns.copy()
        for col in optional_columns:
            if col in columns:
                select_columns.append(col)
        
        query = f"SELECT {', '.join(select_columns)} FROM admin_users ORDER BY id DESC"
        cursor.execute(query)
        
        users = []
        for row in cursor.fetchall():
            user = {
                'id': row[0],
                'username': row[1],
                'role': row[2] if len(row) > 2 else 'admin',
                'email': row[3] if len(row) > 3 and 'email' in select_columns else None,
                'display_name': row[4] if len(row) > 4 and 'display_name' in select_columns else None,
                'is_active': bool(row[5]) if len(row) > 5 and 'is_active' in select_columns else True,
                'created_at': row[6] if len(row) > 6 and 'created_at' in select_columns else None
            }
            users.append(user)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'users': users
        })
    except Exception as e:
        print(f"Get admin users error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
        response.headers['Content-Disposition'] = f'attachment; filename=doctors_database_{get_current_time().strftime("%Y%m%d_%H%M%S")}.csv'
        
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
def get_database_stats_page():
    """Get database statistics"""
    try:
        stats = {
            'doctors_count': len(DOCTORS_DATA) if DOCTORS_DATA else 0,
            'doctors_fields': list(DOCTORS_DATA[0].keys()) if DOCTORS_DATA else [],
            'sample_doctor': DOCTORS_DATA[0] if DOCTORS_DATA else None,
            'user_queries_count': 0,
            'doctor_clicks_count': 0,
            'analytics_events_count': 0,
            'admin_users_count': 0
        }
        
        # Get analytics data count with table existence checks
        try:
            conn = sqlite3.connect('admin_data.db')
            cursor = conn.cursor()
            
            # Check if tables exist before querying
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            if 'user_queries' in existing_tables:
                cursor.execute('SELECT COUNT(*) FROM user_queries')
                stats['user_queries_count'] = cursor.fetchone()[0]
            
            if 'doctor_clicks' in existing_tables:
                cursor.execute('SELECT COUNT(*) FROM doctor_clicks')
                stats['doctor_clicks_count'] = cursor.fetchone()[0]
            
            if 'analytics' in existing_tables:
                cursor.execute('SELECT COUNT(*) FROM analytics')
                stats['analytics_events_count'] = cursor.fetchone()[0]
            
            if 'admin_users' in existing_tables:
                cursor.execute('SELECT COUNT(*) FROM admin_users')
                stats['admin_users_count'] = cursor.fetchone()[0]
            
            conn.close()
            
        except Exception as db_error:
            print(f"=== DATABASE QUERY ERROR IN STATS ===")
            print(f"Error: {db_error}")
            print(f"Error type: {type(db_error).__name__}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            # Try to reinitialize database
            try:
                print("=== ATTEMPTING DATABASE REINITIALIZATION ===")
                init_db()
                print("=== DATABASE REINITIALIZED AFTER ERROR ===")
            except Exception as init_error:
                print(f"=== FAILED TO REINITIALIZE DATABASE ===")
                print(f"Init error: {init_error}")
        
        return jsonify(stats)
        
    except Exception as e:
        print(f"Database stats error: {e}")
        return jsonify({
            'doctors_count': len(DOCTORS_DATA) if DOCTORS_DATA else 0,
            'user_queries_count': 0,
            'doctor_clicks_count': 0,
            'analytics_events_count': 0,
            'admin_users_count': 0,
            'error': 'Database temporarily unavailable'
        }), 200

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
        
        filename = f"analytics_{'_'.join(filename_parts)}_{date_range}_{get_current_time().strftime('%Y%m%d_%H%M%S')}.csv"
        
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

@app.route('/admin/doctors')
@require_permission('config')
def admin_doctors():
    """醫生資料庫管理頁面"""
    try:
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        # 獲取統計資料
        cursor.execute("SELECT COUNT(*) FROM doctors")
        total_doctors = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT COALESCE(specialty_zh, specialty_en, specialty)) FROM doctors WHERE COALESCE(specialty_zh, specialty_en, specialty) IS NOT NULL")
        total_specialties = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM doctors WHERE (languages_zh LIKE '%中文%' OR languages_zh LIKE '%English%' OR languages_en LIKE '%中文%' OR languages_en LIKE '%English%')")
        bilingual_doctors = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM doctors WHERE contact_numbers IS NOT NULL AND contact_numbers != ''")
        with_contact = cursor.fetchone()[0]
        
        # 獲取所有專科列表
        cursor.execute("SELECT DISTINCT COALESCE(specialty_zh, specialty_en, specialty) as specialty FROM doctors WHERE specialty IS NOT NULL ORDER BY specialty")
        specialties = [row[0] for row in cursor.fetchall() if row[0]]
        
        conn.close()
        
        return render_template('admin/doctors.html',
                             doctors=[],  # Empty list - will load via AJAX
                             total_doctors=total_doctors,
                             total_specialties=total_specialties,
                             bilingual_doctors=bilingual_doctors,
                             with_contact=with_contact,
                             specialties=specialties)
                             
    except Exception as e:
        print(f"Error in admin_doctors: {e}")
        flash('載入醫生資料時發生錯誤', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/doctors/paginated')
@require_permission('config')
def admin_doctors_paginated():
    """DataTables AJAX endpoint for paginated doctor data"""
    try:
        # Get DataTables parameters
        draw = request.args.get('draw', type=int, default=1)
        start = request.args.get('start', type=int, default=0)
        length = request.args.get('length', type=int, default=25)
        search_value = request.args.get('search[value]', default='')
        
        # Get sorting parameters
        order_column = request.args.get('order[0][column]', type=int, default=0)
        order_dir = request.args.get('order[0][dir]', default='asc')
        
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        # Column mapping for sorting
        columns = ['name', 'specialty', 'qualifications', 'contact_numbers', 'clinic_addresses', 'priority_flag']
        sort_column = columns[order_column] if order_column < len(columns) else 'name'
        
        # Base query
        base_query = """
            SELECT id, 
                   COALESCE(name_zh, name_en, name) as name,
                   COALESCE(specialty_zh, specialty_en, specialty) as specialty,
                   COALESCE(qualifications_zh, qualifications_en, qualifications) as qualifications,
                   contact_numbers,
                   clinic_addresses,
                   priority_flag
            FROM doctors
        """
        
        # Add search filter if provided
        where_clause = ""
        params = []
        if search_value:
            where_clause = """
                WHERE (COALESCE(name_zh, name_en, name) LIKE ? 
                   OR COALESCE(specialty_zh, specialty_en, specialty) LIKE ?
                   OR contact_numbers LIKE ?
                   OR clinic_addresses LIKE ?)
            """
            search_param = f'%{search_value}%'
            params = [search_param, search_param, search_param, search_param]
        
        # Get total count (without search)
        cursor.execute("SELECT COUNT(*) FROM doctors")
        records_total = cursor.fetchone()[0]
        
        # Get filtered count (with search)
        if search_value:
            cursor.execute(f"SELECT COUNT(*) FROM doctors {where_clause}", params)
            records_filtered = cursor.fetchone()[0]
        else:
            records_filtered = records_total
        
        # Get paginated data with sorting
        order_clause = f"ORDER BY {sort_column} {order_dir.upper()}"
        query = f"{base_query} {where_clause} {order_clause} LIMIT ? OFFSET ?"
        params.extend([length, start])
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        
        data = []
        for row in cursor.fetchall():
            doctor_dict = dict(zip(columns, row))
            data.append(doctor_dict)
        
        conn.close()
        
        return jsonify({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data
        })
        
    except Exception as e:
        print(f"Error in admin_doctors_paginated: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/doctors/<int:doctor_id>', methods=['GET'])
@require_permission('config')
def get_doctor_details(doctor_id):
    """獲取醫生詳細資料 (AJAX)"""
    try:
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM doctors WHERE id = ?", (doctor_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [description[0] for description in cursor.description]
            doctor_data = dict(zip(columns, row))
            conn.close()
            return jsonify(doctor_data)
        else:
            conn.close()
            return jsonify({'error': 'Doctor not found'}), 404
            
    except Exception as e:
        print(f"Error getting doctor details: {e}")
        return jsonify({'error': 'Database error'}), 500

@app.route('/admin/specialties')
@require_permission('config')
def get_specialties():
    """Get all unique specialties from database"""
    try:
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        # Get unique Chinese specialties
        cursor.execute('''
            SELECT DISTINCT specialty_zh 
            FROM doctors 
            WHERE specialty_zh IS NOT NULL AND specialty_zh != ''
            ORDER BY specialty_zh
        ''')
        chinese_specialties = [row[0] for row in cursor.fetchall()]
        
        # Get unique English specialties
        cursor.execute('''
            SELECT DISTINCT specialty_en 
            FROM doctors 
            WHERE specialty_en IS NOT NULL AND specialty_en != ''
            ORDER BY specialty_en
        ''')
        english_specialties = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'chinese': chinese_specialties,
            'english': english_specialties
        })
    except Exception as e:
        print(f"Error fetching specialties: {e}")
        return jsonify({'error': 'Failed to fetch specialties'}), 500

@app.route('/admin/doctors/data')
@require_permission('config')
def get_doctors_data():
    """Get all doctors data for specialty mapping"""
    try:
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT specialty_zh, specialty_en 
            FROM doctors 
            WHERE specialty_zh IS NOT NULL AND specialty_en IS NOT NULL 
            AND specialty_zh != '' AND specialty_en != ''
        ''')
        
        doctors = []
        for row in cursor.fetchall():
            doctors.append({
                'specialty_zh': row[0],
                'specialty_en': row[1]
            })
        
        conn.close()
        return jsonify(doctors)
        
    except Exception as e:
        print(f"Error fetching doctors data: {e}")
        return jsonify({'error': 'Failed to fetch doctors data'}), 500

@app.route('/admin/doctors/<int:doctor_id>/update', methods=['POST'])
@require_permission('config')
def update_doctor(doctor_id):
    """更新醫生資料"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        # Update doctor record
        cursor.execute('''
            UPDATE doctors SET
                name_zh = ?, specialty_zh = ?, qualifications_zh = ?, languages_zh = ?,
                name_en = ?, specialty_en = ?, qualifications_en = ?, languages_en = ?,
                contact_numbers = ?, email = ?, clinic_addresses = ?,
                consultation_hours = ?, consultation_fee = ?, profile_url = ?,
                registration_number = ?, priority_flag = ?,
                name = ?, specialty = ?, qualifications = ?, languages = ?,
                phone = ?, address = ?
            WHERE id = ?
        ''', (
            data.get('name_zh'), data.get('specialty_zh'), data.get('qualifications_zh'), data.get('languages_zh'),
            data.get('name_en'), data.get('specialty_en'), data.get('qualifications_en'), data.get('languages_en'),
            data.get('contact_numbers'), data.get('email'), data.get('clinic_addresses'),
            data.get('consultation_hours'), data.get('consultation_fee'), data.get('profile_url'),
            data.get('registration_number'), data.get('priority_flag', 0),
            # Legacy columns - use Chinese first, then English
            data.get('name_zh') or data.get('name_en'),
            data.get('specialty_zh') or data.get('specialty_en'),
            data.get('qualifications_zh') or data.get('qualifications_en'),
            data.get('languages_zh') or data.get('languages_en'),
            data.get('contact_numbers'),
            data.get('clinic_addresses'),
            doctor_id
        ))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Doctor not found'}), 404
        
        conn.commit()
        conn.close()
        
        # Log the update
        log_analytics('doctor_update', {
            'doctor_id': doctor_id,
            'updated_fields': list(data.keys())
        }, get_real_ip(), request.user_agent.string)
        
        return jsonify({'success': True, 'message': 'Doctor updated successfully'})
        
    except Exception as e:
        print(f"Error updating doctor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/doctors/add', methods=['POST'])
@require_permission('config')
def add_doctor():
    """新增醫生"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        # Insert new doctor record
        cursor.execute('''
            INSERT INTO doctors (
                name_zh, specialty_zh, qualifications_zh, languages_zh,
                name_en, specialty_en, qualifications_en, languages_en,
                contact_numbers, email, clinic_addresses,
                consultation_hours, consultation_fee, profile_url,
                registration_number, priority_flag,
                name, specialty, qualifications, languages,
                phone, address
            ) VALUES (
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?,
                ?, ?
            )
        ''', (
            data.get('name_zh'), data.get('specialty_zh'), data.get('qualifications_zh'), data.get('languages_zh'),
            data.get('name_en'), data.get('specialty_en'), data.get('qualifications_en'), data.get('languages_en'),
            data.get('contact_numbers'), data.get('email'), data.get('clinic_addresses'),
            data.get('consultation_hours'), data.get('consultation_fee'), data.get('profile_url'),
            data.get('registration_number'), data.get('priority_flag', 0),
            # Legacy columns - use Chinese first, then English
            data.get('name_zh') or data.get('name_en'),
            data.get('specialty_zh') or data.get('specialty_en'),
            data.get('qualifications_zh') or data.get('qualifications_en'),
            data.get('languages_zh') or data.get('languages_en'),
            data.get('contact_numbers'),
            data.get('clinic_addresses')
        ))
        
        new_doctor_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Log the addition
        log_analytics('doctor_add', {
            'doctor_id': new_doctor_id,
            'name': data.get('name_zh') or data.get('name_en')
        }, get_real_ip(), request.user_agent.string)
        
        return jsonify({'success': True, 'message': 'Doctor added successfully', 'doctor_id': new_doctor_id})
        
    except Exception as e:
        print(f"Error adding doctor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/doctors/<int:doctor_id>/delete', methods=['DELETE'])
@require_permission('config')
def delete_doctor(doctor_id):
    """刪除醫生"""
    try:
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        # Get doctor info for logging
        cursor.execute("SELECT name_zh, name_en FROM doctors WHERE id = ?", (doctor_id,))
        doctor = cursor.fetchone()
        
        if not doctor:
            conn.close()
            return jsonify({'success': False, 'error': 'Doctor not found'}), 404
        
        # Delete doctor record
        cursor.execute("DELETE FROM doctors WHERE id = ?", (doctor_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Doctor not found'}), 404
        
        conn.commit()
        conn.close()
        
        # Log the deletion
        log_analytics('doctor_delete', {
            'doctor_id': doctor_id,
            'name': doctor[0] or doctor[1]
        }, get_real_ip(), request.user_agent.string)
        
        return jsonify({'success': True, 'message': 'Doctor deleted successfully'})
        
    except Exception as e:
        print(f"Error deleting doctor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
        raw_recent_queries = cursor.fetchall()
        
        # Format timestamps for recent queries
        recent_queries = []
        for query in raw_recent_queries:
            formatted_query = list(query)
            formatted_query[0] = format_timestamp(query[0])  # Format timestamp
            recent_queries.append(tuple(formatted_query))
        
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

@app.route('/admin/api/user-reports/<user_ip>')
@require_admin
def get_user_reports(user_ip):
    """API endpoint to get user diagnosis reports"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Get all user queries with diagnosis reports
        cursor.execute('''
            SELECT id, timestamp, age, gender, symptoms, chronic_conditions, 
                   recommended_specialty, ai_diagnosis, language, location, 
                   diagnosis_report
            FROM user_queries 
            WHERE user_ip = ?
            ORDER BY timestamp DESC
        ''', (user_ip,))
        queries = cursor.fetchall()
        
        conn.close()
        
        reports = []
        for query in queries:
            reports.append({
                'id': query[0],
                'timestamp': query[1],
                'age': query[2],
                'gender': query[3],
                'symptoms': query[4],
                'chronic_conditions': query[5],
                'specialty': query[6],
                'emergency_level': 'Yes' if check_emergency_needed(query[7]) else 'No',  # Use emergency detection instead of severity
                'language': query[8],
                'location': query[9],
                'diagnosis_report': query[10]
            })
        
        return jsonify({
            'reports': reports
        })
    except Exception as e:
        print(f"User reports error: {e}")
        return jsonify({'error': 'Failed to fetch user reports'}), 500

@app.route('/report/<report_id>')
def view_report(report_id):
    """Display diagnosis report"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT report_data, created_at, doctor_name, doctor_specialty 
            FROM diagnosis_reports 
            WHERE id = ?
        ''', (report_id,))
        
        report_row = cursor.fetchone()
        conn.close()
        
        if not report_row:
            return "報告未找到", 404
            
        report_data, created_at, doctor_name, doctor_specialty = report_row
        
        # Convert newlines to HTML breaks for display
        report_html = report_data.replace('\n', '<br>')
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI醫療診斷報告</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
                .report {{ background: #f9f9f9; padding: 20px; border-radius: 10px; white-space: pre-line; }}
                .header {{ text-align: center; color: #2c3e50; margin-bottom: 20px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #7f8c8d; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏥 AI醫療診斷報告</h1>
            </div>
            <div class="report">
                {report_html}
            </div>
            <div class="footer">
                <p>此報告生成於: {created_at}</p>
                <p><small>免責聲明：此分析僅供參考，不能替代專業醫療診斷，請務必諮詢合格醫生。</small></p>
            </div>
        </body>
        </html>
        """
        
    except Exception as e:
        print(f"Report display error: {e}")
        return "報告顯示錯誤", 500

@app.route('/get_whatsapp_url', methods=['POST'])
def get_whatsapp_url():
    """Generate WhatsApp URL with diagnosis report"""
    try:
        data = request.get_json()
        doctor_name = data.get('doctor_name')
        doctor_specialty = data.get('doctor_specialty')
        
        # Get session info
        session_id = session.get('session_id')
        query_id = session.get('last_query_id')
        
        # Your designated WhatsApp number (replace with your actual number)
        whatsapp_number = os.getenv('WHATSAPP_TARGET_NUMBER', '85294974070')
        
        # Log to database
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO doctor_clicks (doctor_name, doctor_specialty, user_ip, session_id, query_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (doctor_name, doctor_specialty, get_real_ip(), session_id, query_id))
        conn.commit()
        
        # Get user query data for diagnosis report
        whatsapp_url = f"https://wa.me/{whatsapp_number}"
        
        if query_id:
            cursor.execute('''
                SELECT age, gender, symptoms, chronic_conditions, language, location, 
                       detailed_health_info, ai_diagnosis, recommended_specialty
                FROM user_queries WHERE id = ?
            ''', (query_id,))
            user_query_row = cursor.fetchone()
            
            if user_query_row:
                user_query_data = {
                    'age': user_query_row[0],
                    'gender': user_query_row[1],
                    'symptoms': user_query_row[2],
                    'chronic_conditions': user_query_row[3],
                    'language': user_query_row[4],
                    'location': user_query_row[5],
                    'detailed_health_info': user_query_row[6],
                    'ai_diagnosis': user_query_row[7],
                    'recommended_specialty': user_query_row[8]
                }
                
                doctor_data = {
                    'doctor_name': doctor_name,
                    'doctor_specialty': doctor_specialty
                }
                
                # Generate unique report ID and store report
                import uuid
                report_id = str(uuid.uuid4())
                
                # Store the full diagnosis report in database
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO diagnosis_reports (id, query_id, doctor_name, doctor_specialty, report_data, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (report_id, query_id, doctor_name, doctor_specialty, 
                         format_diagnosis_report_full(user_query_data, doctor_data), 
                         get_current_time().isoformat()))
                except sqlite3.OperationalError as e:
                    print(f"Database error: {e}")
                    # Create table if it doesn't exist
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS diagnosis_reports (
                            id TEXT PRIMARY KEY, 
                            query_id INTEGER, 
                            doctor_name TEXT, 
                            doctor_specialty TEXT, 
                            report_data TEXT, 
                            created_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        INSERT OR REPLACE INTO diagnosis_reports (id, query_id, doctor_name, doctor_specialty, report_data, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (report_id, query_id, doctor_name, doctor_specialty, 
                         format_diagnosis_report_full(user_query_data, doctor_data), 
                         get_current_time().isoformat()))
                conn.commit()
                
                # Generate report URL
                report_url = f"{request.scheme}://{request.host}/report/{report_id}"
                
                # Generate WhatsApp message with report link
                message = format_whatsapp_message(doctor_data, report_url)
                print(f"DEBUG: Generated message length: {len(message)}")
                
                # URL encode the message for WhatsApp web - use quote instead of quote_plus for better emoji handling
                from urllib.parse import quote
                encoded_message = quote(message, safe='')
                whatsapp_url = f"https://wa.me/{whatsapp_number}?text={encoded_message}"
                print(f"DEBUG: Final URL length: {len(whatsapp_url)}")
        
        conn.close()
        
        # Log analytics
        log_analytics('doctor_click', {
            'doctor_name': doctor_name, 'doctor_specialty': doctor_specialty
        }, get_real_ip(), request.user_agent.string, session_id)
        
        return jsonify({'success': True, 'whatsapp_url': whatsapp_url})
    except Exception as e:
        print(f"WhatsApp URL generation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate WhatsApp URL: {str(e)}'}), 500

@app.route('/track_click', methods=['POST'])
def track_click():
    """Legacy endpoint - now redirects to get_whatsapp_url"""
    return get_whatsapp_url()

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

@app.route('/admin/bug-reports')
@require_admin
def admin_bug_reports():
    """Bug reports management page"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Create bug_reports table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bug_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                contact_info TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                url TEXT,
                user_agent TEXT,
                status TEXT DEFAULT 'new',
                image_path TEXT
            )
        ''')
        
        # Add image_path column if it doesn't exist (for existing tables)
        try:
            cursor.execute('ALTER TABLE bug_reports ADD COLUMN image_path TEXT')
        except sqlite3.OperationalError:
            # Column already exists
            pass
        
        # Get all bug reports
        cursor.execute('''
            SELECT id, description, contact_info, timestamp, url, user_agent, status, image_path
            FROM bug_reports 
            ORDER BY timestamp DESC
        ''')
        bug_reports = cursor.fetchall()
        
        # Convert to list of dicts for easier template handling
        reports = []
        for report in bug_reports:
            reports.append({
                'id': report[0],
                'description': report[1],
                'contact_info': report[2],
                'timestamp': report[3],
                'url': report[4],
                'user_agent': report[5],
                'status': report[6],
                'image_path': report[7] if len(report) > 7 else None
            })
        
        # Get stats
        cursor.execute('''
            SELECT status, COUNT(*) 
            FROM bug_reports 
            GROUP BY status
        ''')
        status_counts = dict(cursor.fetchall())
        
        cursor.execute('SELECT COUNT(*) FROM bug_reports')
        total_count = cursor.fetchone()[0]
        
        stats = {
            'new': status_counts.get('new', 0),
            'in_progress': status_counts.get('in-progress', 0),
            'resolved': status_counts.get('resolved', 0),
            'total': total_count
        }
        
        conn.close()
        
        return render_template('admin/bug-reports.html', 
                             bug_reports=reports, 
                             stats=stats)
        
    except Exception as e:
        logger.error(f"Error loading bug reports: {e}")
        flash('載入問題回報時發生錯誤', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/api/bug-reports/<int:report_id>/status', methods=['POST'])
@require_admin
def update_bug_report_status(report_id):
    """Update bug report status"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['new', 'in-progress', 'resolved']:
            return jsonify({'error': '無效的狀態'}), 400
        
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE bug_reports 
            SET status = ? 
            WHERE id = ?
        ''', (new_status, report_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '狀態已更新'})
        
    except Exception as e:
        logger.error(f"Error updating bug report status: {e}")
        return jsonify({'error': '更新狀態時發生錯誤'}), 500

@app.route('/admin/api/bug-reports/<int:report_id>', methods=['DELETE'])
@require_admin
def delete_bug_report(report_id):
    """Delete bug report"""
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM bug_reports WHERE id = ?', (report_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '問題回報已刪除'})
        
    except Exception as e:
        logger.error(f"Error deleting bug report: {e}")
        return jsonify({'error': '刪除問題回報時發生錯誤'}), 500

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

def cleanup_old_diagnosis_reports():
    """Clean up diagnosis reports older than 30 days"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Calculate cutoff date (30 days ago)
        cutoff_date = datetime.now() - timedelta(days=30)
        cutoff_timestamp = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
        
        # Delete old diagnosis reports
        cursor.execute("""
            DELETE FROM diagnosis_reports 
            WHERE created_at < ?
        """, (cutoff_timestamp,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Cleaned up {deleted_count} diagnosis reports older than 30 days")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error during diagnosis reports cleanup: {str(e)}")
        return 0

@app.route('/submit-bug-report', methods=['POST'])
def submit_bug_report():
    """Handle bug report submissions and send to WhatsApp"""
    try:
        # Handle both JSON and form data
        if request.content_type and 'multipart/form-data' in request.content_type:
            description = request.form.get('description', '').strip()
            contact_info = request.form.get('contact_info', '').strip()
            url = request.form.get('url', '')
            user_agent = request.form.get('user_agent', '')
            image_file = request.files.get('image')
        elif request.content_type and 'application/json' in request.content_type:
            data = request.get_json()
            description = data.get('description', '').strip()
            contact_info = data.get('contact_info', '').strip()
            url = data.get('url', '')
            user_agent = data.get('user_agent', '')
            image_file = None
        else:
            # Fallback for other content types
            try:
                data = request.get_json(force=True)
                description = data.get('description', '').strip()
                contact_info = data.get('contact_info', '').strip()
                url = data.get('url', '')
                user_agent = data.get('user_agent', '')
                image_file = None
            except:
                description = request.form.get('description', '').strip()
                contact_info = request.form.get('contact_info', '').strip()
                url = request.form.get('url', '')
                user_agent = request.form.get('user_agent', '')
                image_file = request.files.get('image')

        # Format bug report message
        bug_message = f"""🐛 **系統問題回報**

📝 **問題描述:**
{description}

📞 **聯絡方式:** {contact_info}
🕐 **回報時間:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🌐 **頁面:** {url}
💻 **瀏覽器:** {user_agent[:100]}...

---
此問題由 Doctor AI 系統自動轉發"""

        # Send to WhatsApp if enabled
        if WHATSAPP_CONFIG['enabled'] and whatsapp_client:
            try:
                # Send to the configured notification number
                target_number = WHATSAPP_CONFIG.get('target_number', '')
                if target_number:
                    whatsapp_client.emit('send_message', {
                        'to': target_number,
                        'message': bug_message
                    })
                    logger.info(f"Bug report sent to WhatsApp: {target_number}")
                else:
                    logger.warning("No WhatsApp target number configured for bug reports")
            except Exception as whatsapp_error:
                logger.error(f"Failed to send bug report to WhatsApp: {whatsapp_error}")
        
        # Connect to database
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Create bug_reports table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bug_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                contact_info TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                url TEXT,
                user_agent TEXT,
                status TEXT DEFAULT 'new',
                image_path TEXT
            )
        ''')
        
        # Insert bug report
        cursor.execute('''
            INSERT INTO bug_reports (description, contact_info, url, user_agent, image_path)
            VALUES (?, ?, ?, ?, ?)
        ''', (description, contact_info, url, user_agent, image_path))
        
        report_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Send to WhatsApp
        try:
            if whatsapp_client and whatsapp_client.connected:
                target_number = WHATSAPP_CONFIG.get('notification_number')
                if target_number:
                    bug_message = f"🐛 新問題回報 #{report_id}\n\n描述: {description}\n"
                    if contact_info:
                        bug_message += f"聯絡方式: {contact_info}\n"
                    if url:
                        bug_message += f"頁面: {url}\n"
                    if image_path:
                        bug_message += f"附件: 已上傳圖片\n"
                    bug_message += f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    
                    whatsapp_client.emit('send_message', {
                        'to': target_number,
                        'message': bug_message
                    })
                    logger.info(f"Bug report sent to WhatsApp: {target_number}")
                else:
                    logger.warning("No WhatsApp target number configured for bug reports")
        except Exception as whatsapp_error:
            logger.error(f"Failed to send bug report to WhatsApp: {whatsapp_error}")
        
        return jsonify({'success': True, 'message': '問題回報已成功提交'})
        
    except Exception as e:
        logger.error(f"Error processing bug report: {e}")
        return jsonify({'error': '處理問題回報時發生錯誤'}), 500

def run_scheduled_tasks():
    """Run scheduled maintenance tasks in background thread"""
    def scheduler_thread():
        # Schedule cleanup to run daily at 2 AM
        schedule.every().day.at("02:00").do(cleanup_old_diagnosis_reports)
        
        while True:
            schedule.run_pending()
            time.sleep(3600)  # Check every hour
    
    # Start scheduler in background thread
    scheduler = threading.Thread(target=scheduler_thread, daemon=True)
    scheduler.start()
    logger.info("Scheduled tasks initialized - diagnosis reports cleanup will run daily at 2 AM")

if __name__ == '__main__':
    # Initialize database and load saved config
    init_db()
    load_ai_config_from_db()
    load_whatsapp_config_from_db()
    
    # Initialize WhatsApp client
    init_whatsapp_client()
    
    # Start scheduled tasks
    run_scheduled_tasks()
    
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
