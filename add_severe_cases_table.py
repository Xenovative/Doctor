#!/usr/bin/env python3
"""
Database Migration Script: Add Severe Cases Logging Table
This script adds a table to log severe medical cases for admin monitoring.
"""

import sqlite3
import os
from datetime import datetime

def add_severe_cases_table():
    """Add severe_cases table to admin_data.db"""
    
    db_path = 'admin_data.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database {db_path} does not exist!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='severe_cases'
        """)
        
        if cursor.fetchone():
            print("✅ severe_cases table already exists")
            conn.close()
            return True
        
        # Create severe_cases table
        cursor.execute('''
            CREATE TABLE severe_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_query_id INTEGER,
                age INTEGER,
                gender TEXT,
                symptoms TEXT,
                chronic_conditions TEXT,
                severe_symptoms TEXT,
                severe_conditions TEXT,
                user_ip TEXT,
                session_id TEXT,
                timestamp TEXT,
                user_acknowledged BOOLEAN DEFAULT FALSE,
                admin_reviewed BOOLEAN DEFAULT FALSE,
                admin_notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_query_id) REFERENCES user_queries (id)
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('''
            CREATE INDEX idx_severe_cases_timestamp ON severe_cases(timestamp)
        ''')
        
        cursor.execute('''
            CREATE INDEX idx_severe_cases_reviewed ON severe_cases(admin_reviewed)
        ''')
        
        conn.commit()
        print("✅ Successfully created severe_cases table with indexes")
        
        # Verify table creation
        cursor.execute("SELECT sql FROM sqlite_master WHERE name='severe_cases'")
        table_schema = cursor.fetchone()
        if table_schema:
            print(f"📋 Table schema: {table_schema[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating severe_cases table: {e}")
        return False

if __name__ == "__main__":
    print("🏥 Adding severe cases logging table...")
    success = add_severe_cases_table()
    
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        exit(1)
