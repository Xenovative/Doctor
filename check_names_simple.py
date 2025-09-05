import sqlite3
import sys

conn = sqlite3.connect('doctors.db')
cursor = conn.cursor()

# Check first 5 records
cursor.execute("SELECT id, name_zh, name_en, name FROM doctors LIMIT 5")
rows = cursor.fetchall()

print("First 5 doctors:")
for row in rows:
    print(f"ID: {row[0]} | ZH: '{row[1]}' | EN: '{row[2]}' | Legacy: '{row[3]}'")

# Count non-null Chinese names
cursor.execute("SELECT COUNT(*) FROM doctors WHERE name_zh IS NOT NULL AND name_zh != ''")
zh_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM doctors")
total = cursor.fetchone()[0]

print(f"\nStats: {zh_count}/{total} have Chinese names")

conn.close()
