#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database migration script to add gender column to user_queries table
with backward compatibility for existing records
"""

import sqlite3
import os

def add_gender_column():
    """Add gender column to user_queries table if it doesn't exist"""
    db_path = 'admin_data.db'
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found. Creating new database...")
        # Database will be created when we connect
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if gender column already exists
        cursor.execute("PRAGMA table_info(user_queries)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'gender' not in columns:
            print("Adding gender column to user_queries table...")
            cursor.execute('''
                ALTER TABLE user_queries 
                ADD COLUMN gender TEXT DEFAULT NULL
            ''')
            print("Gender column added successfully!")
        else:
            print("Gender column already exists in user_queries table.")
        
        # Verify the table structure
        cursor.execute("PRAGMA table_info(user_queries)")
        table_info = cursor.fetchall()
        print("\nCurrent table structure:")
        for column in table_info:
            print(f"  {column[1]} ({column[2]}) - {'NOT NULL' if column[3] else 'NULL'}")
        
        conn.commit()
        conn.close()
        print("\nMigration completed successfully!")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    add_gender_column()
