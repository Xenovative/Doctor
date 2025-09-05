#!/usr/bin/env python3
import sqlite3
import csv
import os
from datetime import datetime

def fix_chinese_migration():
    """Fix the migration to properly import Chinese names"""
    
    csv_file = "assets/finddoc_doctors_detailed_full_20250905.csv"
    db_file = "doctors.db"
    
    print("🔄 Fixing Chinese name migration...")
    
    # Backup current database
    if os.path.exists(db_file):
        backup_name = f"doctors_backup_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        os.rename(db_file, backup_name)
        print(f"✅ Backed up database to {backup_name}")
    
    # Create new database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Create doctors table with proper UTF-8 support
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
            phone TEXT,
            address TEXT,
            
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Read CSV with proper UTF-8 encoding
    print("📖 Reading CSV with UTF-8 encoding...")
    
    with open(csv_file, 'r', encoding='utf-8-sig') as file:  # utf-8-sig handles BOM
        reader = csv.DictReader(file)
        
        insert_count = 0
        error_count = 0
        
        for row in reader:
            try:
                # Debug first few records
                if insert_count < 3:
                    print(f"Row {insert_count + 1}: name_zh='{row.get('name_zh', 'MISSING')}', name_en='{row.get('name_en', 'MISSING')}'")
                
                # Insert with explicit UTF-8 handling
                cursor.execute('''
                    INSERT INTO doctors (
                        name_zh, specialty_zh, qualifications_zh, languages_zh,
                        name_en, specialty_en, qualifications_en, languages_en,
                        profile_url, registration_number, contact_numbers, email,
                        consultation_fee, consultation_hours, clinic_addresses, languages_available,
                        name, specialty, qualifications, languages, phone, address
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('name_zh') or None,
                    row.get('specialty_zh') or None,
                    row.get('qualifications_zh') or None,
                    row.get('languages_zh') or None,
                    row.get('name_en') or None,
                    row.get('specialty_en') or None,
                    row.get('qualifications_en') or None,
                    row.get('languages_en') or None,
                    row.get('profile_url') or None,
                    row.get('registration_number') or None,
                    row.get('contact_numbers') or None,
                    row.get('email') or None,
                    row.get('consultation_fee') or None,
                    row.get('consultation_hours') or None,
                    row.get('clinic_addresses') or None,
                    row.get('languages_available') or None,
                    # Legacy mappings - use Chinese first, then English
                    row.get('name_zh') or row.get('name_en') or None,
                    row.get('specialty_zh') or row.get('specialty_en') or None,
                    row.get('qualifications_zh') or row.get('qualifications_en') or None,
                    row.get('languages_zh') or row.get('languages_en') or None,
                    row.get('contact_numbers') or None,
                    row.get('clinic_addresses') or None
                ))
                
                insert_count += 1
                if insert_count % 1000 == 0:
                    print(f"  Inserted {insert_count:,} records...")
                    
            except Exception as e:
                error_count += 1
                if error_count <= 5:
                    print(f"  ❌ Error inserting row {insert_count}: {e}")
    
    # Create indexes
    cursor.execute("CREATE INDEX idx_name_zh ON doctors(name_zh)")
    cursor.execute("CREATE INDEX idx_name_en ON doctors(name_en)")
    cursor.execute("CREATE INDEX idx_specialty_zh ON doctors(specialty_zh)")
    cursor.execute("CREATE INDEX idx_specialty_en ON doctors(specialty_en)")
    
    # Verify Chinese names
    cursor.execute("SELECT COUNT(*) FROM doctors WHERE name_zh IS NOT NULL AND name_zh != ''")
    zh_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM doctors")
    total_count = cursor.fetchone()[0]
    
    # Sample Chinese names
    cursor.execute("SELECT name_zh, name_en FROM doctors WHERE name_zh IS NOT NULL LIMIT 5")
    samples = cursor.fetchall()
    
    conn.commit()
    conn.close()
    
    print(f"✅ Migration completed!")
    print(f"   Total records: {total_count:,}")
    print(f"   Chinese names: {zh_count:,}")
    print(f"   Errors: {error_count:,}")
    
    print(f"\n📝 Sample Chinese names:")
    for i, (zh, en) in enumerate(samples, 1):
        print(f"   {i}. '{zh}' / '{en}'")

if __name__ == "__main__":
    fix_chinese_migration()
