"""
Quick check and migrate script for affiliation system
Checks if tables exist and creates them if needed
"""

import sqlite3
import sys

def check_table_exists(cursor, table_name):
    """Check if a table exists"""
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None

def main():
    print("🔍 Checking database structure...")
    
    # Check doctors.db
    conn = sqlite3.connect('doctors.db')
    cursor = conn.cursor()
    
    required_tables = [
        'doctor_accounts',
        'doctor_availability', 
        'doctor_time_off',
        'doctor_notifications'
    ]
    
    missing_tables = []
    for table in required_tables:
        if not check_table_exists(cursor, table):
            missing_tables.append(table)
            print(f"❌ Missing table: {table}")
        else:
            print(f"✅ Table exists: {table}")
    
    conn.close()
    
    # Check admin_data.db
    conn = sqlite3.connect('admin_data.db')
    cursor = conn.cursor()
    
    admin_tables = [
        'reservations',
        'reservation_history',
        'doctor_reviews'
    ]
    
    for table in admin_tables:
        if not check_table_exists(cursor, table):
            missing_tables.append(table)
            print(f"❌ Missing table: {table}")
        else:
            print(f"✅ Table exists: {table}")
    
    conn.close()
    
    if missing_tables:
        print(f"\n⚠️  Missing {len(missing_tables)} tables!")
        print("\n📋 To create missing tables, run:")
        print("   python setup_affiliation_system.py")
        print("\nOr manually run:")
        print("   python create_affiliation_system.py")
        return False
    else:
        print("\n✅ All required tables exist!")
        return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
