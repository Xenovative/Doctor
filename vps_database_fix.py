#!/usr/bin/env python3
"""
VPS Database Fix Script for Doctor AI System
This script fixes doctor names being stored in specialty fields and sets NULL specialties to General Practitioner
"""

import sqlite3
import os
import shutil
from datetime import datetime

def create_backup(db_path):
    """Create a backup of the database"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_{timestamp}"
    shutil.copy2(db_path, backup_path)
    print(f"Backup created: {backup_path}")
    return backup_path

def fix_doctor_database():
    """Main function to fix doctor database issues"""
    db_path = 'doctors.db'
    
    print("=== Doctor Database Fix Script for VPS ===")
    print(f"Starting database cleanup at {datetime.now()}")
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found in current directory")
        print("Please run this script from your Doctor AI application directory")
        return False
    
    # Create backup
    backup_path = create_backup(db_path)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check how many records need fixing
        cursor.execute("SELECT COUNT(*) FROM doctors WHERE specialty LIKE 'Dr.%' OR specialty_zh LIKE 'Dr.%' OR specialty_en LIKE 'Dr.%'")
        problematic_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM doctors WHERE specialty IS NULL OR specialty = '' OR TRIM(specialty) = '' OR specialty_zh IS NULL OR specialty_zh = '' OR TRIM(specialty_zh) = ''")
        null_specialty_count = cursor.fetchone()[0]
        
        print(f"Found {problematic_count} records with doctor names in specialty fields")
        print(f"Found {null_specialty_count} records with NULL/empty specialties")
        
        if problematic_count == 0 and null_specialty_count == 0:
            print("No issues found in database. Exiting.")
            conn.close()
            return True
        
        # Fix 1: Clear doctor names from specialty fields
        print("Step 1: Clearing doctor names from specialty fields...")
        cursor.execute("""
            UPDATE doctors 
            SET specialty = CASE 
                WHEN specialty LIKE 'Dr.%' THEN NULL 
                ELSE specialty 
            END,
            specialty_zh = CASE 
                WHEN specialty_zh LIKE 'Dr.%' THEN NULL 
                ELSE specialty_zh 
            END,
            specialty_en = CASE 
                WHEN specialty_en LIKE 'Dr.%' THEN NULL 
                ELSE specialty_en 
            END
            WHERE specialty LIKE 'Dr.%' OR specialty_zh LIKE 'Dr.%' OR specialty_en LIKE 'Dr.%'
        """)
        
        # Fix 2: Infer specialties from name patterns
        print("Step 2: Inferring specialties from name patterns...")
        
        specialty_patterns = [
            ('泌尿外科', 'Urology', '%泌尿外科%'),
            ('物理治療', 'Physiotherapy', '%物理治療師%'),
            ('心理學', 'Psychology', '%心理學家%'),
            ('營養學', 'Nutrition', '%營養師%'),
            ('牙科', 'Dentistry', '%牙醫%'),
            ('中醫', 'Traditional Chinese Medicine', '%中醫%')
        ]
        
        for specialty_zh, specialty_en, pattern in specialty_patterns:
            cursor.execute("""
                UPDATE doctors 
                SET specialty_zh = ?, specialty_en = ?, specialty = ?
                WHERE (specialty IS NULL OR specialty = '') 
                AND (name_zh LIKE ? OR name LIKE ?)
            """, (specialty_zh, specialty_en, specialty_zh, pattern, pattern))
        
        # Fix 3: Set remaining NULL specialties to General Practitioner
        print("Step 3: Setting NULL specialties to General Practitioner...")
        cursor.execute("""
            UPDATE doctors 
            SET specialty = '全科醫生', specialty_zh = '全科醫生', specialty_en = 'General Practitioner' 
            WHERE specialty IS NULL OR specialty = '' OR TRIM(specialty) = ''
        """)
        
        cursor.execute("""
            UPDATE doctors 
            SET specialty_zh = '全科醫生', specialty_en = 'General Practitioner' 
            WHERE specialty_zh IS NULL OR specialty_zh = '' OR TRIM(specialty_zh) = ''
        """)
        
        # Commit changes
        conn.commit()
        
        # Verify the fixes
        cursor.execute("SELECT COUNT(*) FROM doctors WHERE specialty = '全科醫生'")
        fixed_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM doctors WHERE specialty LIKE 'Dr.%' OR specialty_zh LIKE 'Dr.%' OR specialty_en LIKE 'Dr.%'")
        remaining_issues = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM doctors WHERE specialty IS NULL OR specialty = '' OR specialty_zh IS NULL OR specialty_zh = ''")
        null_count = cursor.fetchone()[0]
        
        conn.close()
        
        print("\n=== Fix Results ===")
        print(f"Records set to General Practitioner: {fixed_count}")
        print(f"Remaining problematic records: {remaining_issues}")
        print(f"Remaining NULL records: {null_count}")
        
        if remaining_issues == 0 and null_count == 0:
            print("✅ Database cleanup completed successfully!")
        else:
            print("⚠️  Some issues may remain. Please check manually.")
        
        print(f"\nBackup created: {backup_path}")
        print(f"Database fix completed at {datetime.now()}")
        print("=== Script completed ===")
        
        return True
        
    except Exception as e:
        print(f"Error during database fix: {e}")
        print(f"Database backup available at: {backup_path}")
        return False

if __name__ == "__main__":
    success = fix_doctor_database()
    exit(0 if success else 1)
