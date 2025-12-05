#!/usr/bin/env python3
"""
Migration script to add 'reservations' permission to existing admin users.
Run this once after updating the codebase.
"""

import sqlite3
import json

def migrate():
    print("Adding 'reservations' permission to existing admin users...")
    
    conn = sqlite3.connect('admin_data.db')
    cursor = conn.cursor()
    
    # Get all users with their tab_permissions
    cursor.execute('SELECT id, username, tab_permissions FROM admin_users')
    users = cursor.fetchall()
    
    updated_count = 0
    for user_id, username, tab_perms_json in users:
        if tab_perms_json:
            try:
                tab_perms = json.loads(tab_perms_json)
            except:
                tab_perms = {}
        else:
            tab_perms = {}
        
        # Add reservations permission if not present
        if 'reservations' not in tab_perms:
            tab_perms['reservations'] = True
            cursor.execute(
                'UPDATE admin_users SET tab_permissions = ? WHERE id = ?',
                (json.dumps(tab_perms), user_id)
            )
            print(f"  ✓ Added 'reservations' permission to user: {username}")
            updated_count += 1
        else:
            print(f"  - User {username} already has 'reservations' permission")
    
    conn.commit()
    conn.close()
    
    print(f"\nMigration complete. Updated {updated_count} users.")

if __name__ == '__main__':
    migrate()
