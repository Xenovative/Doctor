#!/usr/bin/env python3
"""
Create medical_search_config table for Doctor AI app
This script creates the database table needed for medical search configuration management
"""

import sqlite3
import os
from datetime import datetime

def create_medical_search_config_table():
    """Create medical_search_config table with default values"""
    
    # Database file path
    db_path = 'doctor_ai.db'
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Creating medical_search_config table...")
        
        # Create the table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medical_search_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT UNIQUE NOT NULL,
                config_value TEXT NOT NULL,
                config_type TEXT NOT NULL DEFAULT 'string',
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Default configuration values
        default_configs = [
            ('primary_search_api', 'pubmed', 'select', '主要醫學搜尋API'),
            ('secondary_search_api', 'none', 'select', '備用醫學搜尋API'),
            ('articles_per_symptom', '2', 'number', '每個症狀搜尋的文章數量'),
            ('max_symptoms_processed', '4', 'number', '最大處理症狀數量'),
            ('max_total_articles', '8', 'number', '最大總文章數量'),
            ('search_timeout', '10', 'number', '搜尋超時時間（秒）'),
            ('pubmed_retmax', '3', 'number', 'PubMed搜尋結果限制'),
            ('enable_cochrane', 'false', 'boolean', '啟用Cochrane Library'),
            ('enable_google_scholar', 'false', 'boolean', '啟用Google Scholar'),
            ('search_filters', 'clinical,diagnosis,treatment', 'text', '搜尋過濾器'),
            ('relevance_threshold', '0.5', 'number', '相關性門檻值'),
            ('cache_duration', '3600', 'number', '快取持續時間（秒）')
        ]
        
        # Insert default configurations
        for config_key, config_value, config_type, description in default_configs:
            cursor.execute('''
                INSERT OR IGNORE INTO medical_search_config 
                (config_key, config_value, config_type, description)
                VALUES (?, ?, ?, ?)
            ''', (config_key, config_value, config_type, description))
        
        # Commit changes
        conn.commit()
        
        # Verify table creation
        cursor.execute('SELECT COUNT(*) FROM medical_search_config')
        count = cursor.fetchone()[0]
        
        print(f"✅ medical_search_config table created successfully!")
        print(f"✅ Inserted {count} default configuration entries")
        
        # Show current configurations
        print("\n📋 Current Medical Search Configuration:")
        cursor.execute('SELECT config_key, config_value, config_type, description FROM medical_search_config ORDER BY config_key')
        configs = cursor.fetchall()
        
        for config_key, config_value, config_type, description in configs:
            print(f"   {config_key}: {config_value} ({config_type}) - {description}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating medical_search_config table: {e}")
        return False

def verify_table():
    """Verify the table was created correctly"""
    try:
        conn = sqlite3.connect('doctor_ai.db')
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='medical_search_config'")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            print("✅ Table verification: medical_search_config exists")
            
            # Check table structure
            cursor.execute("PRAGMA table_info(medical_search_config)")
            columns = cursor.fetchall()
            print("📊 Table structure:")
            for col in columns:
                print(f"   {col[1]} ({col[2]})")
            
            # Check data count
            cursor.execute("SELECT COUNT(*) FROM medical_search_config")
            count = cursor.fetchone()[0]
            print(f"📈 Configuration entries: {count}")
            
        else:
            print("❌ Table verification failed: medical_search_config does not exist")
        
        conn.close()
        return table_exists
        
    except Exception as e:
        print(f"❌ Error verifying table: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Medical Search Configuration Table Setup")
    print("=" * 50)
    
    # Create table
    success = create_medical_search_config_table()
    
    if success:
        print("\n🔍 Verifying table creation...")
        verify_table()
        print("\n🎉 Medical search configuration table setup complete!")
        print("\n💡 You can now use the admin panel to configure medical search settings.")
    else:
        print("\n❌ Failed to create medical search configuration table")
        print("Please check the error messages above and try again.")
