#!/usr/bin/env python3
import sqlite3
import csv
import os
from datetime import datetime

def migrate_database():
    """Migrate new CSV data to SQLite database"""
    
    # File paths
    csv_file = "assets/finddoc_doctors_detailed_full_20250905.csv"
    db_file = "doctors.db"
    
    print(f"🔄 Starting migration from {csv_file}")
    
    # Backup existing database
    if os.path.exists(db_file):
        backup_name = f"doctors_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        os.rename(db_file, backup_name)
        print(f"✅ Backed up existing database to {backup_name}")
    
    # Create new database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Create doctors table with all CSV columns
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
            
            -- Legacy columns for compatibility
            name TEXT,
            specialty TEXT,
            qualifications TEXT,
            languages TEXT,
            clinic_name TEXT,
            phone TEXT,
            address TEXT,
            district TEXT,
            
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Read and insert CSV data
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        insert_count = 0
        for row in reader:
            # Insert with both new and legacy column mappings
            cursor.execute('''
                INSERT INTO doctors (
                    name_zh, specialty_zh, qualifications_zh, languages_zh,
                    name_en, specialty_en, qualifications_en, languages_en,
                    profile_url, registration_number, contact_numbers, email,
                    consultation_fee, consultation_hours, clinic_addresses, languages_available,
                    name, specialty, qualifications, languages, phone, address
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row.get('name_zh', ''),
                row.get('specialty_zh', ''),
                row.get('qualifications_zh', ''),
                row.get('languages_zh', ''),
                row.get('name_en', ''),
                row.get('specialty_en', ''),
                row.get('qualifications_en', ''),
                row.get('languages_en', ''),
                row.get('profile_url', ''),
                row.get('registration_number', ''),
                row.get('contact_numbers', ''),
                row.get('email', ''),
                row.get('consultation_fee', ''),
                row.get('consultation_hours', ''),
                row.get('clinic_addresses', ''),
                row.get('languages_available', ''),
                # Legacy mappings
                row.get('name_zh', row.get('name_en', '')),  # name
                row.get('specialty_zh', row.get('specialty_en', '')),  # specialty
                row.get('qualifications_zh', row.get('qualifications_en', '')),  # qualifications
                row.get('languages_zh', row.get('languages_en', '')),  # languages
                row.get('contact_numbers', ''),  # phone
                row.get('clinic_addresses', '')  # address
            ))
            
            insert_count += 1
            if insert_count % 1000 == 0:
                print(f"  Inserted {insert_count:,} records...")
    
    # Create indexes
    cursor.execute("CREATE INDEX idx_name_zh ON doctors(name_zh)")
    cursor.execute("CREATE INDEX idx_name_en ON doctors(name_en)")
    cursor.execute("CREATE INDEX idx_specialty_zh ON doctors(specialty_zh)")
    cursor.execute("CREATE INDEX idx_specialty_en ON doctors(specialty_en)")
    cursor.execute("CREATE INDEX idx_name ON doctors(name)")
    cursor.execute("CREATE INDEX idx_specialty ON doctors(specialty)")
    
    # Get final count
    cursor.execute("SELECT COUNT(*) FROM doctors")
    total_count = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    
    print(f"✅ Migration completed successfully!")
    print(f"   Total records: {total_count:,}")
    print(f"   Database: {db_file}")

if __name__ == "__main__":
    migrate_database()
