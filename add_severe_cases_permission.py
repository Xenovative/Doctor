#!/usr/bin/env python3
"""
Database Migration Script: Add severe_cases permission to admin users

This script adds the 'severe_cases' permission to all existing admin users
who currently have 'analytics' permission, ensuring proper access control
for the severe cases monitoring functionality.

Usage:
    python add_severe_cases_permission.py
"""

import sqlite3
import json
import os
from datetime import datetime

# Database file path
DB_PATH = 'admin_data.db'

def backup_database():
    """Create a backup of the database before migration"""
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} not found.")
        return False
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{DB_PATH}.backup_severe_cases_{timestamp}"
    
    try:
        import shutil
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to backup database: {e}")
        return False

def add_severe_cases_permission():
    """Add severe_cases permission to all users who have analytics permission"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all users with their current permissions
        cursor.execute('SELECT id, username, tab_permissions FROM admin_users')
        users = cursor.fetchall()
        
        if not users:
            print("ℹ️  No users found")
            conn.close()
            return True
        
        updated_count = 0
        
        for user_id, username, tab_permissions_str in users:
            try:
                # Parse existing permissions
                if tab_permissions_str:
                    permissions = json.loads(tab_permissions_str)
                else:
                    permissions = {}
                
                # Check if user has analytics permission
                has_analytics = permissions.get('analytics', False)
                
                # Add severe_cases permission if user has analytics permission
                if has_analytics and 'severe_cases' not in permissions:
                    permissions['severe_cases'] = True
                    
                    # Update the user's permissions
                    updated_permissions = json.dumps(permissions)
                    cursor.execute('''
                        UPDATE admin_users 
                        SET tab_permissions = ? 
                        WHERE id = ?
                    ''', (updated_permissions, user_id))
                    
                    print(f"✅ Added severe_cases permission to user: {username}")
                    updated_count += 1
                elif 'severe_cases' in permissions:
                    print(f"ℹ️  User {username} already has severe_cases permission")
                else:
                    print(f"ℹ️  User {username} doesn't have analytics permission, skipping")
                    
            except json.JSONDecodeError:
                print(f"⚠️  User {username} has invalid JSON permissions, skipping")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"✅ Updated {updated_count} users with severe_cases permission")
        return True
        
    except Exception as e:
        print(f"❌ Error adding severe_cases permission: {e}")
        return False

def verify_migration():
    """Verify that the migration was successful"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT username, tab_permissions FROM admin_users')
        users = cursor.fetchall()
        
        print("\n📋 Current user permissions:")
        for username, tab_permissions_str in users:
            if tab_permissions_str:
                try:
                    permissions = json.loads(tab_permissions_str)
                    has_analytics = permissions.get('analytics', False)
                    has_severe_cases = permissions.get('severe_cases', False)
                    
                    print(f"  👤 {username}:")
                    print(f"    - analytics: {'✅' if has_analytics else '❌'}")
                    print(f"    - severe_cases: {'✅' if has_severe_cases else '❌'}")
                except json.JSONDecodeError:
                    print(f"  👤 {username}: ⚠️  Invalid JSON permissions")
            else:
                print(f"  👤 {username}: ❌ No permissions set")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verifying migration: {e}")
        return False

def main():
    """Main migration function"""
    print("=" * 60)
    print("DATABASE MIGRATION: Add severe_cases permission")
    print("=" * 60)
    
    # Step 1: Backup database
    if not backup_database():
        print("⚠️  Backup failed, but continuing with migration...")
    
    # Step 2: Add severe_cases permission
    if not add_severe_cases_permission():
        print("❌ Migration failed")
        return False
    
    # Step 3: Verify migration
    if not verify_migration():
        print("❌ Migration verification failed")
        return False
    
    print("=" * 60)
    print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Update app.py routes to use 'severe_cases' permission")
    print("2. Update admin templates to use 'severe_cases' permission")
    print("3. Restart your application")
    print("4. Test the severe cases access control")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
