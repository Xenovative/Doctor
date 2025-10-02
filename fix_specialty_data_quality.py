#!/usr/bin/env python3
"""
Script to identify and fix data quality issues where doctor names appear in specialty fields
"""
import sqlite3
import re

def analyze_specialty_data():
    """Analyze specialty fields to find names that shouldn't be there"""
    conn = sqlite3.connect('doctors.db')
    cursor = conn.cursor()
    
    # Get all doctors with their name and specialty data
    cursor.execute('''
        SELECT id, name_zh, name_en, name, specialty_zh, specialty_en, specialty
        FROM doctors
        WHERE specialty_zh IS NOT NULL OR specialty_en IS NOT NULL OR specialty IS NOT NULL
    ''')
    
    doctors = cursor.fetchall()
    issues_found = []
    
    print("Analyzing specialty data quality...")
    print("=" * 60)
    
    for doctor in doctors:
        doc_id, name_zh, name_en, name, specialty_zh, specialty_en, specialty = doctor
        
        # Collect all possible names for this doctor
        doctor_names = []
        if name_zh: doctor_names.append(name_zh.strip())
        if name_en: doctor_names.append(name_en.strip())
        if name: doctor_names.append(name.strip())
        
        # Check if any specialty field contains a doctor name
        specialty_fields = [
            ('specialty_zh', specialty_zh),
            ('specialty_en', specialty_en),
            ('specialty', specialty)
        ]
        
        for field_name, field_value in specialty_fields:
            if field_value:
                field_value = field_value.strip()
                
                # Check if specialty field contains any doctor name
                for doctor_name in doctor_names:
                    if doctor_name and doctor_name.lower() in field_value.lower():
                        issues_found.append({
                            'id': doc_id,
                            'field': field_name,
                            'current_value': field_value,
                            'doctor_names': doctor_names,
                            'issue': f"Specialty field '{field_name}' contains doctor name '{doctor_name}'"
                        })
                        print(f"ID {doc_id}: {field_name} = '{field_value}' (contains name: {doctor_name})")
                
                # Check for English name patterns in specialty fields (the main issue)
                name_patterns = [
                    r'^[A-Z][a-z]+\s+[A-Z][a-z]+$',  # Full English name like "John Smith"
                    r'^[A-Z][a-z]+,\s*[A-Z][a-z]+$',  # Last, First format like "Smith, John"
                    r'Dr\.?\s+[A-Z][a-z]+',  # Dr. Smith
                    r'醫生|醫師',  # Chinese doctor titles
                ]
                
                for pattern in name_patterns:
                    if re.search(pattern, field_value):
                        # Check if it's not a legitimate specialty
                        known_specialties = [
                            '內科', '外科', '小兒科', '婦產科', '骨科', '皮膚科', '眼科', '耳鼻喉科',
                            'Internal Medicine', 'Surgery', 'Pediatrics', 'Obstetrics', 'Orthopedics',
                            'Dermatology', 'Ophthalmology', 'Otolaryngology', 'Cardiology', 'Neurology'
                        ]
                        
                        is_known_specialty = any(spec.lower() in field_value.lower() for spec in known_specialties)
                        
                        if not is_known_specialty:
                            issues_found.append({
                                'id': doc_id,
                                'field': field_name,
                                'current_value': field_value,
                                'doctor_names': doctor_names,
                                'issue': f"Specialty field '{field_name}' contains suspicious name pattern"
                            })
                            print(f"ID {doc_id}: {field_name} = '{field_value}' (suspicious pattern)")
    
    conn.close()
    
    print(f"\nFound {len(issues_found)} data quality issues")
    return issues_found

def fix_specialty_data(issues, dry_run=True):
    """Fix the identified specialty data issues"""
    conn = sqlite3.connect('doctors.db')
    cursor = conn.cursor()
    
    print(f"\n{'DRY RUN - ' if dry_run else ''}Fixing specialty data issues...")
    print("=" * 60)
    
    fixed_count = 0
    
    for issue in issues:
        doc_id = issue['id']
        field = issue['field']
        current_value = issue['current_value']
        
        print(f"\nID {doc_id}: Fixing {field}")
        print(f"  Current: '{current_value}'")
        
        # Strategy: Clear the problematic field and let the CASE statement handle fallbacks
        if not dry_run:
            cursor.execute(f"UPDATE doctors SET {field} = NULL WHERE id = ?", (doc_id,))
            print(f"  Action: Set {field} to NULL")
        else:
            print(f"  Action: Would set {field} to NULL")
        
        fixed_count += 1
    
    if not dry_run:
        conn.commit()
        print(f"\n✅ Fixed {fixed_count} specialty data issues")
        
        # Now add GP fallback for doctors with no specialty
        add_gp_fallback(cursor, dry_run=False)
    else:
        print(f"\n📋 Would fix {fixed_count} specialty data issues")
    
    conn.close()
    return fixed_count

def add_gp_fallback(cursor=None, dry_run=True):
    """Add GP as fallback specialty for doctors with no specialty"""
    should_close = False
    if cursor is None:
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        should_close = True
    
    print(f"\n{'DRY RUN - ' if dry_run else ''}Adding GP fallback for doctors without specialty...")
    print("=" * 60)
    
    # Find doctors with no specialty
    cursor.execute('''
        SELECT id, name_zh, name_en
        FROM doctors 
        WHERE (specialty_zh IS NULL OR specialty_zh = '') 
          AND (specialty_en IS NULL OR specialty_en = '') 
          AND (specialty IS NULL OR specialty = '')
    ''')
    
    doctors_without_specialty = cursor.fetchall()
    
    print(f"Found {len(doctors_without_specialty)} doctors without specialty")
    
    if doctors_without_specialty:
        for doctor in doctors_without_specialty[:10]:  # Show first 10
            doc_id, name_zh, name_en = doctor
            name = name_zh or name_en or f'ID {doc_id}'
            print(f"  - {name}")
        
        if len(doctors_without_specialty) > 10:
            print(f"  ... and {len(doctors_without_specialty) - 10} more")
        
        if not dry_run:
            # Add GP specialty to all doctors without specialty
            cursor.execute('''
                UPDATE doctors SET 
                  specialty_zh = '全科醫生',
                  specialty_en = 'General Practitioner'
                WHERE (specialty_zh IS NULL OR specialty_zh = '') 
                  AND (specialty_en IS NULL OR specialty_en = '') 
                  AND (specialty IS NULL OR specialty = '')
            ''')
            
            affected_rows = cursor.rowcount
            print(f"\n✅ Added GP specialty to {affected_rows} doctors")
            
            if should_close:
                conn.commit()
        else:
            print(f"\n📋 Would add GP specialty to {len(doctors_without_specialty)} doctors")
    else:
        print("✅ All doctors already have specialties!")
    
    if should_close:
        conn.close()
    
    return len(doctors_without_specialty)

def suggest_correct_specialties():
    """Suggest correct specialties based on other data"""
    conn = sqlite3.connect('doctors.db')
    cursor = conn.cursor()
    
    print("\nSuggesting correct specialties...")
    print("=" * 60)
    
    # Find doctors with NULL specialties but might have clues in other fields
    cursor.execute('''
        SELECT id, name_zh, name_en, qualifications_zh, qualifications_en, clinic_addresses
        FROM doctors
        WHERE (specialty_zh IS NULL OR specialty_zh = '') 
        AND (specialty_en IS NULL OR specialty_en = '')
        AND (specialty IS NULL OR specialty = '')
        LIMIT 20
    ''')
    
    doctors = cursor.fetchall()
    
    specialty_keywords = {
        '內科': ['internal', 'medicine', '內科', '一般內科'],
        '外科': ['surgery', 'surgical', '外科', '普通外科'],
        '小兒科': ['pediatric', 'paediatric', '小兒', '兒科'],
        '婦產科': ['obstetric', 'gynecology', '婦產', '婦科'],
        '骨科': ['orthopedic', 'orthopaedic', '骨科', '骨傷'],
        '皮膚科': ['dermatology', '皮膚科', '皮膚'],
        '眼科': ['ophthalmology', '眼科', '眼'],
        '耳鼻喉科': ['otolaryngology', 'ent', '耳鼻喉', '耳鼻咽喉'],
        '心臟科': ['cardiology', '心臟科', '心血管'],
        '神經科': ['neurology', '神經科', '腦神經'],
        '精神科': ['psychiatry', '精神科', '心理'],
        '急診科': ['emergency', '急診科', '急診'],
        '全科醫生': ['general practitioner', 'gp', '全科', '家庭醫學']
    }
    
    suggestions = []
    
    for doctor in doctors:
        doc_id, name_zh, name_en, qual_zh, qual_en, address = doctor
        
        # Look for specialty clues in qualifications and address
        text_to_search = ' '.join(filter(None, [qual_zh or '', qual_en or '', address or ''])).lower()
        
        suggested_specialties = []
        for specialty, keywords in specialty_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_to_search:
                    suggested_specialties.append(specialty)
                    break
        
        if suggested_specialties:
            suggestions.append({
                'id': doc_id,
                'name': name_zh or name_en or 'Unknown',
                'suggested_specialties': suggested_specialties,
                'evidence': text_to_search[:100] + '...' if len(text_to_search) > 100 else text_to_search
            })
    
    print(f"Found {len(suggestions)} doctors with suggested specialties:")
    for suggestion in suggestions[:10]:  # Show first 10
        print(f"ID {suggestion['id']}: {suggestion['name']}")
        print(f"  Suggested: {', '.join(suggestion['suggested_specialties'])}")
        print(f"  Evidence: {suggestion['evidence']}")
        print()
    
    conn.close()
    return suggestions

if __name__ == "__main__":
    print("🔍 Doctor Specialty Data Quality Checker & Fixer")
    print("=" * 60)
    
    # Step 1: Analyze current issues
    issues = analyze_specialty_data()
    
    if issues:
        print(f"\n⚠️  Found {len(issues)} issues that need fixing")
        
        # Ask user if they want to fix the issues
        response = input("\nDo you want to fix these issues? (y/N): ").strip().lower()
        
        if response == 'y':
            # First do a dry run
            print("\n--- DRY RUN ---")
            fix_specialty_data(issues, dry_run=True)
            
            confirm = input("\nProceed with actual fixes? (y/N): ").strip().lower()
            if confirm == 'y':
                fix_specialty_data(issues, dry_run=False)
                print("\n✅ Data quality issues have been fixed!")
            else:
                print("❌ No changes made.")
        else:
            print("❌ No changes made.")
    else:
        print("✅ No specialty data quality issues found!")
        
        # Even if no issues found, check for doctors without specialty
        print("\n" + "=" * 60)
        print("Checking for doctors without specialty...")
        add_gp_fallback(dry_run=True)
        
        response = input("\nDo you want to add GP specialty to doctors without specialty? (y/N): ").strip().lower()
        if response == 'y':
            add_gp_fallback(dry_run=False)
    
    # Step 2: Suggest correct specialties for remaining empty fields
    print("\n" + "=" * 60)
    suggest_correct_specialties()
