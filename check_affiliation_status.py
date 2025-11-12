"""
Check and display affiliation status of doctors
"""
import sqlite3

def check_affiliation():
    conn = sqlite3.connect('doctors.db')
    cursor = conn.cursor()
    
    # Check if is_affiliated column exists
    cursor.execute("PRAGMA table_info(doctors)")
    columns = [row[1] for row in cursor.fetchall()]
    
    print("=== Database Column Check ===")
    if 'is_affiliated' in columns:
        print("✅ is_affiliated column EXISTS")
    else:
        print("❌ is_affiliated column MISSING")
        print("\nYou need to run the migration:")
        print("python create_affiliation_system.py")
        conn.close()
        return
    
    # Check for doctor_accounts table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='doctor_accounts'")
    if cursor.fetchone():
        print("✅ doctor_accounts table EXISTS")
    else:
        print("❌ doctor_accounts table MISSING")
        print("\nYou need to run the migration:")
        print("python create_affiliation_system.py")
        conn.close()
        return
    
    print("\n=== Affiliation Status ===")
    
    # Get all doctors with their affiliation status
    cursor.execute("""
        SELECT d.id, d.name_zh, d.name_en, d.is_affiliated, da.username
        FROM doctors d
        LEFT JOIN doctor_accounts da ON d.id = da.doctor_id
        ORDER BY d.id
        LIMIT 20
    """)
    
    doctors = cursor.fetchall()
    
    if not doctors:
        print("No doctors found in database")
        conn.close()
        return
    
    affiliated_count = 0
    print(f"\nShowing first 20 doctors:")
    print("-" * 80)
    print(f"{'ID':<5} {'Name':<30} {'Affiliated':<12} {'Username':<20}")
    print("-" * 80)
    
    for doctor in doctors:
        doc_id, name_zh, name_en, is_affiliated, username = doctor
        name = name_zh or name_en or 'Unknown'
        affiliated_status = "✅ YES" if is_affiliated else "❌ NO"
        username_display = username or "-"
        
        print(f"{doc_id:<5} {name[:28]:<30} {affiliated_status:<12} {username_display:<20}")
        
        if is_affiliated:
            affiliated_count += 1
    
    print("-" * 80)
    print(f"\nTotal doctors checked: {len(doctors)}")
    print(f"Affiliated doctors: {affiliated_count}")
    print(f"Non-affiliated doctors: {len(doctors) - affiliated_count}")
    
    if affiliated_count == 0:
        print("\n⚠️  NO AFFILIATED DOCTORS FOUND!")
        print("\nTo create an affiliated doctor account:")
        print("1. Go to /admin/doctors")
        print("2. Click '編輯' on any doctor")
        print("3. Click '創建醫生帳戶' button")
        print("4. Fill in username and password")
        print("5. The doctor will be marked as affiliated")
    
    conn.close()

if __name__ == '__main__':
    check_affiliation()
