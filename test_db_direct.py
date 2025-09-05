#!/usr/bin/env python3
import sqlite3
import os

# Check if database exists
if not os.path.exists('doctors.db'):
    print("❌ doctors.db not found!")
    exit(1)

print(f"📊 Database size: {os.path.getsize('doctors.db')/1024/1024:.1f} MB")

try:
    conn = sqlite3.connect('doctors.db')
    cursor = conn.cursor()
    
    # Get table info
    cursor.execute("PRAGMA table_info(doctors)")
    columns = cursor.fetchall()
    print(f"\n📋 Table structure ({len(columns)} columns):")
    for col in columns[:10]:  # Show first 10 columns
        print(f"  {col[1]} ({col[2]})")
    
    # Count total records
    cursor.execute("SELECT COUNT(*) FROM doctors")
    total = cursor.fetchone()[0]
    print(f"\n👥 Total records: {total:,}")
    
    # Check Chinese names specifically
    cursor.execute("SELECT COUNT(*) FROM doctors WHERE name_zh IS NOT NULL AND name_zh != '' AND name_zh != 'NULL'")
    zh_count = cursor.fetchone()[0]
    print(f"🇨🇳 Chinese names: {zh_count:,}")
    
    # Check English names
    cursor.execute("SELECT COUNT(*) FROM doctors WHERE name_en IS NOT NULL AND name_en != '' AND name_en != 'NULL'")
    en_count = cursor.fetchone()[0]
    print(f"🇬🇧 English names: {en_count:,}")
    
    # Sample data
    cursor.execute("SELECT id, name_zh, name_en, name FROM doctors WHERE id <= 5")
    samples = cursor.fetchall()
    
    print(f"\n📝 Sample records:")
    for sample in samples:
        print(f"  ID {sample[0]}: ZH='{sample[1]}' | EN='{sample[2]}' | Legacy='{sample[3]}'")
    
    # Check for actual Chinese characters
    cursor.execute("SELECT name_zh FROM doctors WHERE name_zh LIKE '%醫生%' OR name_zh LIKE '%Dr%' LIMIT 3")
    chinese_samples = cursor.fetchall()
    print(f"\n🔍 Chinese character samples:")
    for i, (name,) in enumerate(chinese_samples, 1):
        print(f"  {i}. '{name}'")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
