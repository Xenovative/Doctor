#!/usr/bin/env python3
"""
Database migration script to add diagnosis_report column to user_queries table
"""

import sqlite3
import os

def add_diagnosis_report_column():
    """Add diagnosis_report column to user_queries table"""
    db_path = 'admin_data.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if diagnosis_report column already exists
        cursor.execute("PRAGMA table_info(user_queries)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'diagnosis_report' in columns:
            print("diagnosis_report column already exists in user_queries table")
            conn.close()
            return True
        
        # Add the diagnosis_report column
        cursor.execute('''
            ALTER TABLE user_queries 
            ADD COLUMN diagnosis_report TEXT
        ''')
        
        conn.commit()
        conn.close()
        
        print("Successfully added diagnosis_report column to user_queries table")
        return True
        
    except Exception as e:
        print(f"Error adding diagnosis_report column: {e}")
        return False

if __name__ == "__main__":
    print("Adding diagnosis_report column to user_queries table...")
    success = add_diagnosis_report_column()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
