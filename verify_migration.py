import sqlite3
import os

def verify_migration():
    """Verify the database migration was successful"""
    
    db_file = "doctors.db"
    
    if not os.path.exists(db_file):
        print("❌ Database not found!")
        return
    
    # Check database size
    size_mb = os.path.getsize(db_file) / 1024 / 1024
    print(f"📊 Database size: {size_mb:.1f} MB")
    
    # Connect and analyze
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"📋 Tables: {tables}")
    
    # Check doctors table
    if 'doctors' in tables:
        # Get column info
        cursor.execute("PRAGMA table_info(doctors)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"📝 Columns ({len(columns)}): {columns[:10]}...")
        
        # Get record count
        cursor.execute("SELECT COUNT(*) FROM doctors")
        count = cursor.fetchone()[0]
        print(f"👥 Total doctors: {count:,}")
        
        # Sample records
        cursor.execute("SELECT name_zh, specialty_zh, name_en, specialty_en FROM doctors LIMIT 3")
        samples = cursor.fetchall()
        print("📄 Sample records:")
        for i, sample in enumerate(samples, 1):
            print(f"  {i}. {sample[0]} ({sample[1]}) / {sample[2]} ({sample[3]})")
        
        # Check legacy compatibility columns
        cursor.execute("SELECT name, specialty, languages FROM doctors WHERE name IS NOT NULL LIMIT 3")
        legacy_samples = cursor.fetchall()
        print("🔄 Legacy compatibility:")
        for i, sample in enumerate(legacy_samples, 1):
            print(f"  {i}. {sample[0]} - {sample[1]} - {sample[2]}")
    
    conn.close()
    print("✅ Migration verification complete!")

if __name__ == "__main__":
    verify_migration()
