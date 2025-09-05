#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

def add_priority_column():
    """Add priority_flag column to doctors table"""
    
    db_path = 'doctors.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(doctors)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'priority_flag' in columns:
            print("✅ priority_flag column already exists")
            conn.close()
            return True
        
        # Add the column
        cursor.execute("ALTER TABLE doctors ADD COLUMN priority_flag INTEGER DEFAULT 0")
        conn.commit()
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(doctors)")
        new_columns = [row[1] for row in cursor.fetchall()]
        
        if 'priority_flag' in new_columns:
            print("✅ Successfully added priority_flag column to doctors table")
            
            # Show some sample data
            cursor.execute("SELECT COUNT(*) FROM doctors")
            total_count = cursor.fetchone()[0]
            print(f"📊 Total doctors in database: {total_count:,}")
            
            conn.close()
            return True
        else:
            print("❌ Failed to add priority_flag column")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Error adding priority_flag column: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Adding priority_flag column to doctors database...")
    success = add_priority_column()
    
    if success:
        print("🎉 Database migration completed successfully!")
    else:
        print("💥 Database migration failed!")
