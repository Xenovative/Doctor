#!/usr/bin/env python3
"""
Fix User Permissions Script

This script ensures all admin users have proper tab permissions set.
Run this on the production server to fix any login issues.
"""

import sqlite3
import json

# Database file path
DB_PATH = 'admin_data.db'

# Default tab permissions
DEFAULT_TAB_PERMISSIONS = {
    "dashboard": True,
    "analytics": True,
    "config": True,
    "doctors": True,
    "users": True,
    "bug_reports": True
}

def fix_user_permissions():
    """Fix tab permissions for all users"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all users
        cursor.execute('SELECT id, username, tab_permissions FROM admin_users')
        users = cursor.fetchall()
        
        print(f"Found {len(users)} users")
        
        for user_id, username, tab_permissions in users:
            if not tab_permissions:
                # Set default permissions
                cursor.execute('''
                    UPDATE admin_users 
                    SET tab_permissions = ? 
                    WHERE id = ?
                ''', (json.dumps(DEFAULT_TAB_PERMISSIONS), user_id))
                print(f"✅ Fixed permissions for user: {username}")
            else:
                print(f"✅ User {username} already has permissions")
        
        conn.commit()
        conn.close()
        print("✅ All user permissions fixed")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing permissions: {e}")
        return False

def check_database_schema():
    """Check if tab_permissions column exists"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(admin_users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        conn.close()
        
        if 'tab_permissions' in columns:
            print("✅ tab_permissions column exists")
            return True
        else:
            print("❌ tab_permissions column missing - run add_tab_permissions_column.py first")
            return False
            
    except Exception as e:
        print(f"❌ Error checking schema: {e}")
        return False

def list_users():
    """List all users and their status"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username, role, is_active, tab_permissions FROM admin_users')
        users = cursor.fetchall()
        
        print("\nCurrent users:")
        print("-" * 60)
        for user_id, username, role, is_active, tab_permissions in users:
            status = "Active" if is_active else "Inactive"
            has_perms = "Yes" if tab_permissions else "No"
            print(f"ID: {user_id}, Username: {username}, Role: {role}, Status: {status}, Tab Perms: {has_perms}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error listing users: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("FIX USER PERMISSIONS SCRIPT")
    print("=" * 50)
    
    # Check schema first
    if not check_database_schema():
        print("\n❌ Please run the migration script first:")
        print("python add_tab_permissions_column.py")
        exit(1)
    
    # List current users
    list_users()
    
    # Fix permissions
    print("\nFixing user permissions...")
    if fix_user_permissions():
        print("\n✅ SUCCESS: All user permissions have been fixed")
        print("\nUsers should now be able to log in properly.")
    else:
        print("\n❌ FAILED: Could not fix user permissions")
        exit(1)
