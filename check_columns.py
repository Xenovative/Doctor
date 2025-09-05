import sqlite3

conn = sqlite3.connect('doctors.db')
cursor = conn.cursor()

# Check if columns exist
cursor.execute("PRAGMA table_info(doctors)")
columns = cursor.fetchall()
print("All columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# Check sample data
cursor.execute("SELECT languages_en, qualifications_en, languages_zh, qualifications_zh FROM doctors LIMIT 3")
results = cursor.fetchall()
print("\nSample data:")
for i, row in enumerate(results, 1):
    print(f"Row {i}:")
    print(f"  EN Languages: {row[0]}")
    print(f"  EN Qualifications: {row[1]}")
    print(f"  ZH Languages: {row[2]}")
    print(f"  ZH Qualifications: {row[3]}")
    print()

conn.close()
