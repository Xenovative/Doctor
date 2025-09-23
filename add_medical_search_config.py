#!/usr/bin/env python3
"""
Add medical search configuration table to database
"""

import sqlite3
import os

def add_medical_search_config_table():
    """Add medical_search_config table to store search API settings"""
    
    # Database path
    db_path = 'doctor_ai.db'
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create medical_search_config table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medical_search_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT UNIQUE NOT NULL,
                config_value TEXT NOT NULL,
                description TEXT,
                config_type TEXT DEFAULT 'string',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert default configuration values
        default_configs = [
            ('primary_search_api', 'pubmed', 'Primary medical search API to use', 'select'),
            ('secondary_search_api', 'none', 'Secondary medical search API (fallback)', 'select'),
            ('articles_per_symptom', '2', 'Number of articles to fetch per symptom', 'number'),
            ('max_symptoms_processed', '4', 'Maximum number of symptoms to process', 'number'),
            ('max_total_articles', '8', 'Maximum total articles to display', 'number'),
            ('search_timeout', '10', 'API request timeout in seconds', 'number'),
            ('pubmed_retmax', '3', 'PubMed API retmax parameter', 'number'),
            ('enable_cochrane', 'false', 'Enable Cochrane Library search', 'boolean'),
            ('enable_google_scholar', 'false', 'Enable Google Scholar search', 'boolean'),
            ('search_filters', 'clinical,diagnosis,treatment', 'Search filters to apply', 'text'),
            ('relevance_threshold', '0.5', 'Minimum relevance score for articles', 'number'),
            ('cache_duration', '3600', 'Cache duration for search results (seconds)', 'number')
        ]
        
        for config_key, config_value, description, config_type in default_configs:
            cursor.execute('''
                INSERT OR IGNORE INTO medical_search_config 
                (config_key, config_value, description, config_type) 
                VALUES (?, ?, ?, ?)
            ''', (config_key, config_value, description, config_type))
        
        conn.commit()
        print("✅ Medical search configuration table created successfully!")
        print(f"✅ Added {len(default_configs)} default configuration entries")
        
        # Show current config
        cursor.execute('SELECT config_key, config_value, description FROM medical_search_config ORDER BY config_key')
        configs = cursor.fetchall()
        
        print("\n📋 Current Medical Search Configuration:")
        for key, value, desc in configs:
            print(f"  {key}: {value} ({desc})")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = add_medical_search_config_table()
    if success:
        print("\n🎉 Medical search configuration setup completed!")
    else:
        print("\n💥 Setup failed!")
