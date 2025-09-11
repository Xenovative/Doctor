#!/usr/bin/env python3
"""
Database cleanup script to fix doctor names being stored in specialty fields
"""

import sqlite3
import re

def fix_doctor_specialty_data():
    """Fix doctor names that are incorrectly stored in specialty fields"""
    db_path = 'doctors.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Find records where specialty fields contain doctor names (starting with "Dr.")
        cursor.execute("""
            SELECT id, name, name_zh, name_en, specialty, specialty_zh, specialty_en 
            FROM doctors 
            WHERE specialty LIKE 'Dr.%' OR specialty_zh LIKE 'Dr.%' OR specialty_en LIKE 'Dr.%'
        """)
        
        problematic_records = cursor.fetchall()
        print(f"Found {len(problematic_records)} records with doctor names in specialty fields")
        
        fixed_count = 0
        
        for record in problematic_records:
            id, name, name_zh, name_en, specialty, specialty_zh, specialty_en = record
            
            print(f"\nProcessing ID {id}:")
            print(f"  Name: {name} | {name_zh} | {name_en}")
            print(f"  Current specialty: {specialty} | {specialty_zh} | {specialty_en}")
            
            # Clear specialty fields that contain doctor names
            new_specialty = None if specialty and specialty.startswith('Dr.') else specialty
            new_specialty_zh = None if specialty_zh and specialty_zh.startswith('Dr.') else specialty_zh
            new_specialty_en = None if specialty_en and specialty_en.startswith('Dr.') else specialty_en
            
            # Try to infer actual specialty from name patterns
            inferred_specialty_zh = None
            inferred_specialty_en = None
            
            # Check for common specialty patterns in names
            if name_zh:
                if '泌尿外科' in name_zh:
                    inferred_specialty_zh = '泌尿外科'
                    inferred_specialty_en = 'Urology'
                elif '物理治療師' in name_zh:
                    inferred_specialty_zh = '物理治療'
                    inferred_specialty_en = 'Physiotherapy'
                elif '心理學家' in name_zh:
                    inferred_specialty_zh = '心理學'
                    inferred_specialty_en = 'Psychology'
                elif '營養師' in name_zh:
                    inferred_specialty_zh = '營養學'
                    inferred_specialty_en = 'Nutrition'
                elif '牙醫' in name_zh:
                    inferred_specialty_zh = '牙科'
                    inferred_specialty_en = 'Dentistry'
                elif '中醫' in name_zh:
                    inferred_specialty_zh = '中醫'
                    inferred_specialty_en = 'Traditional Chinese Medicine'
            
            # Use inferred specialty if we cleared the original and found a pattern
            if new_specialty is None and inferred_specialty_zh:
                new_specialty_zh = inferred_specialty_zh
                new_specialty_en = inferred_specialty_en
                print(f"  Inferred specialty: {inferred_specialty_zh} | {inferred_specialty_en}")
            
            # Update the record
            cursor.execute("""
                UPDATE doctors 
                SET specialty = ?, specialty_zh = ?, specialty_en = ?
                WHERE id = ?
            """, (new_specialty, new_specialty_zh, new_specialty_en, id))
            
            fixed_count += 1
            print(f"  Fixed specialty: {new_specialty} | {new_specialty_zh} | {new_specialty_en}")
        
        conn.commit()
        conn.close()
        
        print(f"\nSuccessfully fixed {fixed_count} records")
        return True
        
    except Exception as e:
        print(f"Error fixing doctor specialty data: {e}")
        return False

if __name__ == "__main__":
    print("Fixing doctor specialty data...")
    success = fix_doctor_specialty_data()
    if success:
        print("Data cleanup completed successfully!")
    else:
        print("Data cleanup failed!")
