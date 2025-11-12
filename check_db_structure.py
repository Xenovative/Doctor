import sqlite3

# Check doctors.db structure
print("=== DOCTORS.DB STRUCTURE ===\n")
conn = sqlite3.connect('doctors.db')
cursor = conn.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
for row in cursor.fetchall():
    if row[0]:
        print(row[0])
        print("\n")
conn.close()

# Check admin_data.db structure
print("\n=== ADMIN_DATA.DB STRUCTURE ===\n")
conn = sqlite3.connect('admin_data.db')
cursor = conn.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
for row in cursor.fetchall():
    if row[0]:
        print(row[0])
        print("\n")
conn.close()
