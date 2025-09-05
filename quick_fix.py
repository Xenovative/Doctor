import sqlite3
import csv
import os

# Quick fix for Chinese names
csv_file = "assets/finddoc_doctors_detailed_full_20250905.csv"

# Backup current DB
if os.path.exists("doctors.db"):
    os.rename("doctors.db", f"doctors_backup_{os.path.getmtime('doctors.db'):.0f}.db")

# Create new DB
conn = sqlite3.connect("doctors.db")
cursor = conn.cursor()

# Simple table creation
cursor.execute('''
    CREATE TABLE doctors (
        id INTEGER PRIMARY KEY,
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

# Read CSV and insert
with open(csv_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    count = 0
    for row in reader:
        cursor.execute('''INSERT INTO doctors (
            name_zh, specialty_zh, qualifications_zh, languages_zh,
            name_en, specialty_en, qualifications_en, languages_en,
            profile_url, registration_number, contact_numbers, email,
            consultation_fee, consultation_hours, clinic_addresses, languages_available,
            name, specialty, qualifications, languages, phone, address
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
            row.get('name_zh'), row.get('specialty_zh'), row.get('qualifications_zh'), row.get('languages_zh'),
            row.get('name_en'), row.get('specialty_en'), row.get('qualifications_en'), row.get('languages_en'),
            row.get('profile_url'), row.get('registration_number'), row.get('contact_numbers'), row.get('email'),
            row.get('consultation_fee'), row.get('consultation_hours'), row.get('clinic_addresses'), row.get('languages_available'),
            row.get('name_zh') or row.get('name_en'),
            row.get('specialty_zh') or row.get('specialty_en'),
            row.get('qualifications_zh') or row.get('qualifications_en'),
            row.get('languages_zh') or row.get('languages_en'),
            row.get('contact_numbers'),
            row.get('clinic_addresses')
        ))
        count += 1

conn.commit()

# Verify
cursor.execute("SELECT COUNT(*) FROM doctors WHERE name_zh IS NOT NULL AND name_zh != ''")
zh_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM doctors")
total = cursor.fetchone()[0]

print(f"Imported {total} doctors, {zh_count} with Chinese names")

# Sample
cursor.execute("SELECT name_zh, name_en FROM doctors WHERE name_zh IS NOT NULL LIMIT 3")
samples = cursor.fetchall()
for i, (zh, en) in enumerate(samples, 1):
    print(f"{i}. {zh} / {en}")

conn.close()
