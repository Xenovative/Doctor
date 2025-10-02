#!/usr/bin/env python3
"""
Simple script to add GP (General Practitioner) as fallback specialty 
for doctors who have no specialty assigned.
"""
import sqlite3

def add_gp_fallback():
    """Add GP as fallback specialty for doctors with no specialty"""
    conn = sqlite3.connect('doctors.db')
    cursor = conn.cursor()
    
    print("🏥 Adding GP Fallback Specialty")
    print("=" * 40)
    
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
        print("\nDoctors that will get GP specialty:")
        for doctor in doctors_without_specialty[:10]:  # Show first 10
            doc_id, name_zh, name_en = doctor
            name = name_zh or name_en or f'ID {doc_id}'
            print(f"  - {name}")
        
        if len(doctors_without_specialty) > 10:
            print(f"  ... and {len(doctors_without_specialty) - 10} more")
        
        # Confirm before proceeding
        response = input(f"\nAdd GP specialty to {len(doctors_without_specialty)} doctors? (y/N): ").strip().lower()
        
        if response == 'y':
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
            conn.commit()
            
            print(f"\n✅ Successfully added GP specialty to {affected_rows} doctors!")
            
            # Verify the changes
            cursor.execute('''
                SELECT COUNT(*) FROM doctors 
                WHERE specialty_zh = '全科醫生' AND specialty_en = 'General Practitioner'
            ''')
            gp_count = cursor.fetchone()[0]
            print(f"✅ Verified: {gp_count} doctors now have GP specialty")
            
        else:
            print("❌ No changes made.")
    else:
        print("✅ All doctors already have specialties!")
    
    conn.close()

def show_specialty_stats():
    """Show statistics about doctor specialties"""
    conn = sqlite3.connect('doctors.db')
    cursor = conn.cursor()
    
    print("\n📊 Specialty Statistics:")
    print("=" * 40)
    
    # Total doctors
    cursor.execute("SELECT COUNT(*) FROM doctors")
    total = cursor.fetchone()[0]
    print(f"Total doctors: {total}")
    
    # Doctors with specialty
    cursor.execute('''
        SELECT COUNT(*) FROM doctors 
        WHERE specialty_zh IS NOT NULL OR specialty_en IS NOT NULL OR specialty IS NOT NULL
    ''')
    with_specialty = cursor.fetchone()[0]
    print(f"Doctors with specialty: {with_specialty}")
    
    # Doctors without specialty
    without_specialty = total - with_specialty
    print(f"Doctors without specialty: {without_specialty}")
    
    # GP doctors
    cursor.execute('''
        SELECT COUNT(*) FROM doctors 
        WHERE specialty_zh = '全科醫生' OR specialty_en = 'General Practitioner'
    ''')
    gp_count = cursor.fetchone()[0]
    print(f"GP doctors: {gp_count}")
    
    # Top specialties
    print("\nTop 10 specialties:")
    cursor.execute('''
        SELECT 
            COALESCE(specialty_zh, specialty_en, specialty) as specialty,
            COUNT(*) as count
        FROM doctors 
        WHERE COALESCE(specialty_zh, specialty_en, specialty) IS NOT NULL
        GROUP BY specialty
        ORDER BY count DESC
        LIMIT 10
    ''')
    
    for specialty, count in cursor.fetchall():
        print(f"  {specialty}: {count}")
    
    conn.close()

if __name__ == "__main__":
    show_specialty_stats()
    print()
    add_gp_fallback()
    print()
    show_specialty_stats()
