#!/usr/bin/env python3
"""
Database Migration Script: Add tab_permissions column to admin_users table

This script adds a new JSON column 'tab_permissions' to the admin_users table
to support fine-grained tab access control for admin users.

Usage:
    python add_tab_permissions_column.py

The script will:
1. Backup the current database
2. Add the tab_permissions column
3. Set default permissions for existing users
4. Verify the migration was successful
"""

import sqlite3
import json
import os
import shutil
from datetime import datetime

# Database file path
DB_PATH = 'admin_data.db'

# Default tab permissions for existing users
DEFAULT_TAB_PERMISSIONS = {
    "dashboard": True,
    "analytics": True,
    "config": True,
    "doctors": True,
    "users": True,
    "bug_reports": True
}

def backup_database():
    """Create a backup of the database before migration"""
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} not found. Creating new database...")
        return False
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{DB_PATH}.backup_{timestamp}"
    
    try:
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to backup database: {e}")
        return False

def check_column_exists():
    """Check if tab_permissions column already exists"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(admin_users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        conn.close()
        return 'tab_permissions' in columns
    except Exception as e:
        print(f"❌ Error checking column existence: {e}")
        return False

def create_admin_users_table_if_not_exists():
    """Create admin_users table if it doesn't exist"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'admin',
                permissions TEXT DEFAULT '{}',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                created_by INTEGER,
                totp_secret TEXT,
                totp_enabled INTEGER DEFAULT 0,
                backup_codes TEXT,
                FOREIGN KEY (created_by) REFERENCES admin_users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Admin users table created/verified")
        return True
    except Exception as e:
        print(f"❌ Error creating admin_users table: {e}")
        return False

def add_tab_permissions_column():
    """Add tab_permissions column to admin_users table"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Add the new column
        cursor.execute('''
            ALTER TABLE admin_users 
            ADD COLUMN tab_permissions TEXT DEFAULT NULL
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Added tab_permissions column to admin_users table")
        return True
    except Exception as e:
        print(f"❌ Error adding tab_permissions column: {e}")
        return False

def set_default_permissions():
    """Set default tab permissions for all existing users"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all existing users
        cursor.execute('SELECT id, username, role FROM admin_users')
        users = cursor.fetchall()
        
        if not users:
            print("ℹ️  No existing users found")
            conn.close()
            return True
        
        # Set default permissions for each user
        default_permissions_json = json.dumps(DEFAULT_TAB_PERMISSIONS)
        
        for user_id, username, role in users:
            cursor.execute('''
                UPDATE admin_users 
                SET tab_permissions = ? 
                WHERE id = ?
            ''', (default_permissions_json, user_id))
            
            print(f"✅ Set default permissions for user: {username} (role: {role})")
        
        conn.commit()
        conn.close()
        print(f"✅ Updated {len(users)} users with default tab permissions")
        return True
    except Exception as e:
        print(f"❌ Error setting default permissions: {e}")
        return False

def verify_migration():
    """Verify that the migration was successful"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(admin_users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'tab_permissions' not in columns:
            print("❌ Migration verification failed: tab_permissions column not found")
            conn.close()
            return False
        
        # Check if users have permissions set
        cursor.execute('SELECT id, username, tab_permissions FROM admin_users')
        users = cursor.fetchall()
        
        for user_id, username, tab_permissions in users:
            if tab_permissions:
                try:
                    perms = json.loads(tab_permissions)
                    print(f"✅ User {username} has permissions: {list(perms.keys())}")
                except json.JSONDecodeError:
                    print(f"⚠️  User {username} has invalid JSON permissions")
            else:
                print(f"⚠️  User {username} has no permissions set")
        
        conn.close()
        print("✅ Migration verification completed")
        return True
    except Exception as e:
        print(f"❌ Error verifying migration: {e}")
        return False

def main():
    """Main migration function"""
    print("=" * 60)
    print("DATABASE MIGRATION: Add tab_permissions column")
    print("=" * 60)
    
    # Step 1: Create table if it doesn't exist
    if not create_admin_users_table_if_not_exists():
        print("❌ Migration failed at table creation step")
        return False
    
    # Step 2: Check if migration is needed
    if check_column_exists():
        print("ℹ️  tab_permissions column already exists. Migration not needed.")
        return True
    
    # Step 3: Backup database
    backup_success = backup_database()
    if not backup_success and os.path.exists(DB_PATH):
        print("⚠️  Backup failed, but continuing with migration...")
    
    # Step 4: Add the column
    if not add_tab_permissions_column():
        print("❌ Migration failed at column addition step")
        return False
    
    # Step 5: Set default permissions
    if not set_default_permissions():
        print("❌ Migration failed at setting default permissions step")
        return False
    
    # Step 6: Verify migration
    if not verify_migration():
        print("❌ Migration verification failed")
        return False
    
    print("=" * 60)
    print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Restart your application")
    print("2. Test the admin panel tab permissions")
    print("3. Use the admin config page to manage user permissions")
    print("\nDefault permissions granted to all users:")
    for tab, enabled in DEFAULT_TAB_PERMISSIONS.items():
        print(f"  - {tab}: {'✅' if enabled else '❌'}")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
