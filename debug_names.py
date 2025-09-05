import sqlite3

def check_chinese_names():
    """Check Chinese names in database"""
    
    conn = sqlite3.connect('doctors.db')
    cursor = conn.cursor()
    
    # Check total records
    cursor.execute("SELECT COUNT(*) FROM doctors")
    total = cursor.fetchone()[0]
    print(f"Total doctors: {total:,}")
    
    # Check Chinese names
    cursor.execute("SELECT COUNT(*) FROM doctors WHERE name_zh IS NOT NULL AND name_zh != ''")
    with_zh = cursor.fetchone()[0]
    print(f"With Chinese names: {with_zh:,}")
    
    # Check English names
    cursor.execute("SELECT COUNT(*) FROM doctors WHERE name_en IS NOT NULL AND name_en != ''")
    with_en = cursor.fetchone()[0]
    print(f"With English names: {with_en:,}")
    
    # Sample records
    cursor.execute("SELECT name_zh, name_en, name FROM doctors LIMIT 10")
    samples = cursor.fetchall()
    
    print("\nSample records:")
    for i, (zh, en, legacy) in enumerate(samples, 1):
        print(f"{i:2d}. ZH: '{zh}' | EN: '{en}' | Legacy: '{legacy}'")
    
    # Check column structure
    cursor.execute("PRAGMA table_info(doctors)")
    columns = cursor.fetchall()
    print(f"\nColumns in doctors table:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    conn.close()

if __name__ == "__main__":
    check_chinese_names()
