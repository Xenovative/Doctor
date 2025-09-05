import sqlite3

conn = sqlite3.connect('doctors.db')
cursor = conn.cursor()

# Check if we have English data
cursor.execute("""
    SELECT id, name_zh, name_en, languages_zh, languages_en, qualifications_zh, qualifications_en 
    FROM doctors 
    WHERE (languages_en IS NOT NULL AND languages_en != '' AND languages_en != 'NULL')
       OR (qualifications_en IS NOT NULL AND qualifications_en != '' AND qualifications_en != 'NULL')
    LIMIT 5
""")

results = cursor.fetchall()
print(f"Found {len(results)} doctors with English data:")
print()

for row in results:
    print(f"ID: {row[0]}")
    print(f"Name ZH: {row[1]}")
    print(f"Name EN: {row[2]}")
    print(f"Languages ZH: {row[3][:100] if row[3] else 'None'}...")
    print(f"Languages EN: {row[4][:100] if row[4] else 'None'}...")
    print(f"Qualifications ZH: {row[5][:100] if row[5] else 'None'}...")
    print(f"Qualifications EN: {row[6][:100] if row[6] else 'None'}...")
    print("-" * 80)

# Check total counts
cursor.execute("SELECT COUNT(*) FROM doctors WHERE languages_en IS NOT NULL AND languages_en != '' AND languages_en != 'NULL'")
lang_en_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM doctors WHERE qualifications_en IS NOT NULL AND qualifications_en != '' AND qualifications_en != 'NULL'")
qual_en_count = cursor.fetchone()[0]

print(f"Total doctors with English languages: {lang_en_count}")
print(f"Total doctors with English qualifications: {qual_en_count}")

conn.close()
