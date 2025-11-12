"""
Add notes column to reservations table if it doesn't exist
"""
import sqlite3

def add_notes_column():
    conn = sqlite3.connect('admin_data.db')
    cursor = conn.cursor()
    
    # Check if notes column exists
    cursor.execute("PRAGMA table_info(reservations)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'notes' not in columns:
        print("Adding 'notes' column to reservations table...")
        cursor.execute("""
            ALTER TABLE reservations 
            ADD COLUMN notes TEXT
        """)
        conn.commit()
        print("✅ Added 'notes' column successfully")
    else:
        print("✅ 'notes' column already exists")
    
    conn.close()

if __name__ == '__main__':
    add_notes_column()
