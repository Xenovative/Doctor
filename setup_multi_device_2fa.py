#!/usr/bin/env python3
"""
Multi-Device 2FA Database Migration Script
Creates the necessary database structure for supporting multiple 2FA devices per admin user.
"""

import sqlite3
import json
import hashlib
import os
from datetime import datetime

def migrate_multi_device_2fa():
    """Migrate database to support multi-device 2FA"""
    
    print("=== MULTI-DEVICE 2FA MIGRATION ===")
    
    try:
        # Connect to admin database
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Create admin_2fa_devices table
        print("Creating admin_2fa_devices table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_2fa_devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                device_name TEXT NOT NULL,
                totp_secret TEXT NOT NULL,
                is_primary BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_used DATETIME,
                device_info TEXT,
                FOREIGN KEY (user_id) REFERENCES admin_users (id),
                UNIQUE(user_id, device_name)
            )
        ''')
        
        # Create index for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_admin_2fa_devices_user_id 
            ON admin_2fa_devices (user_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_admin_2fa_devices_active 
            ON admin_2fa_devices (user_id, is_active)
        ''')
        
        # Migrate existing single-device 2FA to multi-device structure
        print("Migrating existing 2FA data...")
        cursor.execute('''
            SELECT id, username, totp_secret, totp_enabled, backup_codes 
            FROM admin_users 
            WHERE totp_enabled = 1 AND totp_secret IS NOT NULL
        ''')
        
        existing_2fa_users = cursor.fetchall()
        
        for user_id, username, totp_secret, totp_enabled, backup_codes in existing_2fa_users:
            # Check if this user already has devices in the new table
            cursor.execute('SELECT COUNT(*) FROM admin_2fa_devices WHERE user_id = ?', (user_id,))
            if cursor.fetchone()[0] == 0:
                # Migrate the existing device as "Primary Device"
                cursor.execute('''
                    INSERT INTO admin_2fa_devices 
                    (user_id, device_name, totp_secret, is_primary, is_active, created_at, device_info)
                    VALUES (?, ?, ?, 1, 1, ?, ?)
                ''', (user_id, "Primary Device", totp_secret, datetime.now(), 
                      json.dumps({"migrated": True, "original_setup": True})))
                
                print(f"Migrated 2FA for user: {username}")
        
        # Add new columns to admin_users for multi-device management
        print("Adding multi-device management columns...")
        
        # Check if columns exist before adding
        cursor.execute("PRAGMA table_info(admin_users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'multi_device_2fa_enabled' not in columns:
            cursor.execute('ALTER TABLE admin_users ADD COLUMN multi_device_2fa_enabled BOOLEAN DEFAULT 0')
        
        if 'max_2fa_devices' not in columns:
            cursor.execute('ALTER TABLE admin_users ADD COLUMN max_2fa_devices INTEGER DEFAULT 3')
        
        # Update users who have migrated devices
        cursor.execute('''
            UPDATE admin_users 
            SET multi_device_2fa_enabled = 1 
            WHERE id IN (SELECT DISTINCT user_id FROM admin_2fa_devices)
        ''')
        
        conn.commit()
        
        # Verify migration
        print("\n=== VERIFICATION ===")
        
        # Check admin_2fa_devices table
        cursor.execute('SELECT COUNT(*) FROM admin_2fa_devices')
        device_count = cursor.fetchone()[0]
        print(f"Total 2FA devices: {device_count}")
        
        # Check users with multi-device 2FA
        cursor.execute('SELECT COUNT(*) FROM admin_users WHERE multi_device_2fa_enabled = 1')
        multi_device_users = cursor.fetchone()[0]
        print(f"Users with multi-device 2FA: {multi_device_users}")
        
        # Show device details
        cursor.execute('''
            SELECT au.username, ad.device_name, ad.is_primary, ad.is_active, ad.created_at
            FROM admin_users au
            JOIN admin_2fa_devices ad ON au.id = ad.user_id
            ORDER BY au.username, ad.is_primary DESC, ad.created_at
        ''')
        
        devices = cursor.fetchall()
        if devices:
            print("\nCurrent 2FA devices:")
            for username, device_name, is_primary, is_active, created_at in devices:
                status = "Primary" if is_primary else "Secondary"
                active = "Active" if is_active else "Inactive"
                print(f"  {username}: {device_name} ({status}, {active}) - {created_at}")
        
        conn.close()
        
        print("\n=== MIGRATION COMPLETED SUCCESSFULLY ===")
        print("Multi-device 2FA structure is now ready!")
        
        return True
        
    except Exception as e:
        print(f"=== MIGRATION ERROR ===")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        
        return False

if __name__ == "__main__":
    success = migrate_multi_device_2fa()
    if success:
        print("\nYou can now use multi-device 2FA functionality!")
    else:
        print("\nMigration failed. Please check the errors above.")
