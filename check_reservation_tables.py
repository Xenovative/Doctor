"""
Check if reservation tables exist and have correct schema
"""
import sqlite3

def check_tables():
    conn = sqlite3.connect('admin_data.db')
    cursor = conn.cursor()
    
    # Check if reservations table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='reservations'
    """)
    
    if cursor.fetchone():
        print("✅ reservations table exists")
        
        # Get column info
        cursor.execute("PRAGMA table_info(reservations)")
        columns = cursor.fetchall()
        print("\nColumns in reservations table:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    else:
        print("❌ reservations table does NOT exist")
    
    # Check if reservation_history table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='reservation_history'
    """)
    
    if cursor.fetchone():
        print("\n✅ reservation_history table exists")
        
        # Get column info
        cursor.execute("PRAGMA table_info(reservation_history)")
        columns = cursor.fetchall()
        print("\nColumns in reservation_history table:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    else:
        print("\n❌ reservation_history table does NOT exist")
    
    conn.close()

if __name__ == '__main__':
    check_tables()
