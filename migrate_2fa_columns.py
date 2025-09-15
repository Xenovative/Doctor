#!/usr/bin/env python3
"""
Database migration script to add 2FA columns to admin_users table
"""
import sqlite3
import os

def migrate_admin_users_table():
    """Add 2FA columns to admin_users table if they don't exist"""
    try:
        # Connect to admin database
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(admin_users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"Current admin_users columns: {columns}")
        
        # Add totp_enabled column if it doesn't exist
        if 'totp_enabled' not in columns:
            cursor.execute('ALTER TABLE admin_users ADD COLUMN totp_enabled INTEGER DEFAULT 0')
            print("Added totp_enabled column")
        else:
            print("totp_enabled column already exists")
            
        # Add totp_secret column if it doesn't exist
        if 'totp_secret' not in columns:
            cursor.execute('ALTER TABLE admin_users ADD COLUMN totp_secret TEXT')
            print("Added totp_secret column")
        else:
            print("totp_secret column already exists")
            
        # Add backup_codes column if it doesn't exist
        if 'backup_codes' not in columns:
            cursor.execute('ALTER TABLE admin_users ADD COLUMN backup_codes TEXT')
            print("Added backup_codes column")
        else:
            print("backup_codes column already exists")
        
        conn.commit()
        
        # Verify the migration
        cursor.execute("PRAGMA table_info(admin_users)")
        new_columns = [column[1] for column in cursor.fetchall()]
        print(f"Updated admin_users columns: {new_columns}")
        
        conn.close()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Starting 2FA database migration...")
    migrate_admin_users_table()
