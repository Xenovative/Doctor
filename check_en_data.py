import sqlite3

conn = sqlite3.connect('doctors.db')
cursor = conn.cursor()

# Check a specific doctor's data
cursor.execute("""
    SELECT name_zh, name_en, languages_zh, languages_en, qualifications_zh, qualifications_en 
    FROM doctors 
    WHERE id = 1
""")

result = cursor.fetchone()
if result:
    print("Doctor ID 1:")
    print(f"Name ZH: {result[0]}")
    print(f"Name EN: {result[1]}")
    print(f"Languages ZH: {result[2]}")
    print(f"Languages EN: {result[3]}")
    print(f"Qualifications ZH: {result[4][:100] if result[4] else None}...")
    print(f"Qualifications EN: {result[5][:100] if result[5] else None}...")

# Check if any records have English data
cursor.execute("SELECT COUNT(*) FROM doctors WHERE languages_en IS NOT NULL AND languages_en != ''")
lang_count = cursor.fetchone()[0]
print(f"\nDoctors with English languages: {lang_count}")

cursor.execute("SELECT COUNT(*) FROM doctors WHERE qualifications_en IS NOT NULL AND qualifications_en != ''")
qual_count = cursor.fetchone()[0]
print(f"Doctors with English qualifications: {qual_count}")

conn.close()
