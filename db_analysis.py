import sqlite3
import os

def analyze_db(db_path, name):
    print(f"\n=== {name} ===")
    print(f"Path: {db_path}")
    print(f"Size: {os.path.getsize(db_path):,} bytes ({os.path.getsize(db_path)/1024/1024:.1f} MB)")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables: {[t[0] for t in tables]}")
    
    # Analyze doctors table if exists
    if ('doctors',) in tables:
        cursor.execute("PRAGMA table_info(doctors)")
        columns = cursor.fetchall()
        print(f"Doctors table columns: {len(columns)}")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        cursor.execute("SELECT COUNT(*) FROM doctors")
        count = cursor.fetchone()[0]
        print(f"Doctor records: {count:,}")
        
        # Sample data
        cursor.execute("SELECT * FROM doctors LIMIT 2")
        samples = cursor.fetchall()
        if samples:
            print("Sample records:")
            for i, sample in enumerate(samples):
                print(f"  Record {i+1}: {sample[:3]}...")
    
    conn.close()

# Analyze all databases
dbs = [
    ("doctors.db", "Current"),
    ("doctors.db.backup_20250905_154930", "Large Backup 1"),
    ("doctors.db.backup_20250905_155008", "Large Backup 2"),
    ("doctors_old_backup_20250905_155713.db", "Old Large Backup")
]

for db_file, name in dbs:
    if os.path.exists(db_file):
        analyze_db(db_file, name)
