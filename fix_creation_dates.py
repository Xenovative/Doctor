#!/usr/bin/env python3
"""
Script to investigate and fix corrupted user creation dates in admin_users table.
All users showing 1970/1/1 indicates Unix epoch (timestamp 0) issue.
"""

import sqlite3
import json
from datetime import datetime

def analyze_creation_dates():
    """Analyze the current state of creation dates in admin_users table"""
    print("=== ANALYZING ADMIN_USERS CREATION DATES ===\n")
    
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Check table schema
        print("1. Checking table schema:")
        cursor.execute("PRAGMA table_info(admin_users)")
        columns = cursor.fetchall()
        
        created_at_column = None
        for col in columns:
            print(f"   {col[1]} ({col[2]}) - Default: {col[4]}")
            if col[1] == 'created_at':
                created_at_column = col
        
        if not created_at_column:
            print("   ❌ No 'created_at' column found!")
            return
        
        print(f"\n2. Created_at column details:")
        print(f"   Type: {created_at_column[2]}")
        print(f"   Default: {created_at_column[4]}")
        
        # Check current data
        print("\n3. Current user data:")
        cursor.execute("SELECT id, username, role, created_at FROM admin_users ORDER BY id")
        users = cursor.fetchall()
        
        for user in users:
            user_id, username, role, created_at = user
            print(f"   ID: {user_id}, User: {username}, Role: {role}, Created: {created_at}")
            
            # Try to parse the created_at value
            if created_at:
                try:
                    # Try as timestamp
                    if isinstance(created_at, (int, float)):
                        dt = datetime.fromtimestamp(created_at)
                        print(f"      → Timestamp {created_at} = {dt}")
                    else:
                        # Try as string
                        print(f"      → String value: '{created_at}'")
                except Exception as e:
                    print(f"      → Parse error: {e}")
            else:
                print(f"      → NULL value")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error analyzing database: {e}")

def fix_creation_dates():
    """Fix the corrupted creation dates by setting them to current timestamp"""
    print("\n=== FIXING CREATION DATES ===\n")
    
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Get current timestamp
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        current_timestamp = int(datetime.now().timestamp())
        
        print(f"Current time: {current_time}")
        print(f"Current timestamp: {current_timestamp}")
        
        # Check what format the created_at column expects
        cursor.execute("PRAGMA table_info(admin_users)")
        columns = cursor.fetchall()
        created_at_type = None
        
        for col in columns:
            if col[1] == 'created_at':
                created_at_type = col[2].upper()
                break
        
        print(f"Created_at column type: {created_at_type}")
        
        # Get users with problematic dates (NULL, 0, or very old dates)
        cursor.execute("""
            SELECT id, username, created_at 
            FROM admin_users 
            WHERE created_at IS NULL 
               OR created_at = 0 
               OR created_at = '0'
               OR created_at < 946684800
        """)  # 946684800 = 2000-01-01 timestamp
        
        problematic_users = cursor.fetchall()
        
        if not problematic_users:
            print("✅ No problematic creation dates found!")
            return
        
        print(f"Found {len(problematic_users)} users with problematic creation dates:")
        for user in problematic_users:
            print(f"   ID: {user[0]}, User: {user[1]}, Created: {user[2]}")
        
        # Decide on the fix based on column type
        if 'TIMESTAMP' in created_at_type or 'DATETIME' in created_at_type:
            # Use datetime string format
            fix_value = current_time
            print(f"\nUsing datetime format: {fix_value}")
        else:
            # Use timestamp integer
            fix_value = current_timestamp
            print(f"\nUsing timestamp format: {fix_value}")
        
        # Apply the fix
        print("\nApplying fixes...")
        for user in problematic_users:
            user_id = user[0]
            username = user[1]
            
            cursor.execute("""
                UPDATE admin_users 
                SET created_at = ? 
                WHERE id = ?
            """, (fix_value, user_id))
            
            print(f"   ✅ Fixed user '{username}' (ID: {user_id})")
        
        # Commit changes
        conn.commit()
        print(f"\n✅ Successfully updated {len(problematic_users)} users")
        
        # Verify the fix
        print("\n4. Verifying fixes:")
        cursor.execute("SELECT id, username, created_at FROM admin_users ORDER BY id")
        users = cursor.fetchall()
        
        for user in users:
            user_id, username, created_at = user
            print(f"   ID: {user_id}, User: {username}, Created: {created_at}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error fixing creation dates: {e}")

def main():
    """Main function to analyze and fix creation dates"""
    print("Admin Users Creation Date Fix Script")
    print("=" * 50)
    
    # First analyze the current state
    analyze_creation_dates()
    
    # Ask for confirmation before fixing
    print("\n" + "=" * 50)
    response = input("Do you want to fix the creation dates? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        fix_creation_dates()
        print("\n✅ Creation date fix completed!")
    else:
        print("\n❌ Fix cancelled by user")

if __name__ == "__main__":
    main()
