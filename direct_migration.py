import sqlite3
import csv
import os
from datetime import datetime

# Direct migration without complex logic
csv_file = "assets/finddoc_doctors_detailed_full_20250905.csv"

# Backup existing database
if os.path.exists("doctors.db"):
    backup_name = f"doctors_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    os.rename("doctors.db", backup_name)
    print(f"Backed up to {backup_name}")

# Create database
conn = sqlite3.connect("doctors.db")
cursor = conn.cursor()

# Create table
cursor.execute('''
    CREATE TABLE doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name_zh TEXT,
        specialty_zh TEXT,
        qualifications_zh TEXT,
        languages_zh TEXT,
        name_en TEXT,
        specialty_en TEXT,
        qualifications_en TEXT,
        languages_en TEXT,
        profile_url TEXT,
        registration_number TEXT,
        contact_numbers TEXT,
        email TEXT,
        consultation_fee TEXT,
        consultation_hours TEXT,
        clinic_addresses TEXT,
        languages_available TEXT,
        name TEXT,
        specialty TEXT,
        qualifications TEXT,
        languages TEXT,
        phone TEXT,
        address TEXT
    )
''')

# Read CSV
with open(csv_file, 'r', encoding='utf-8-sig') as file:
    reader = csv.DictReader(file)
    
    for row in reader:
        cursor.execute('''
            INSERT INTO doctors (
                name_zh, specialty_zh, qualifications_zh, languages_zh,
                name_en, specialty_en, qualifications_en, languages_en,
                profile_url, registration_number, contact_numbers, email,
                consultation_fee, consultation_hours, clinic_addresses, languages_available,
                name, specialty, qualifications, languages, phone, address
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            row['name_zh'],
            row['specialty_zh'], 
            row['qualifications_zh'],
            row['languages_zh'],
            row['name_en'],
            row['specialty_en'],
            row['qualifications_en'], 
            row['languages_en'],
            row['profile_url'],
            row['registration_number'],
            row['contact_numbers'],
            row['email'],
            row['consultation_fee'],
            row['consultation_hours'],
            row['clinic_addresses'],
            row['languages_available'],
            row['name_zh'] if row['name_zh'] else row['name_en'],
            row['specialty_zh'] if row['specialty_zh'] else row['specialty_en'],
            row['qualifications_zh'] if row['qualifications_zh'] else row['qualifications_en'],
            row['languages_zh'] if row['languages_zh'] else row['languages_en'],
            row['contact_numbers'],
            row['clinic_addresses']
        ))

conn.commit()

# Verify
cursor.execute("SELECT COUNT(*) FROM doctors")
total = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM doctors WHERE name_zh IS NOT NULL AND name_zh != ''")
zh_count = cursor.fetchone()[0]

cursor.execute("SELECT name_zh, name_en FROM doctors WHERE name_zh IS NOT NULL AND name_zh != '' LIMIT 5")
samples = cursor.fetchall()

print(f"Total: {total}")
print(f"Chinese names: {zh_count}")
print("Samples:")
for zh, en in samples:
    print(f"  {zh} / {en}")

conn.close()
