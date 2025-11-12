"""
Debug affiliation status - check what's actually in the database
"""
import sqlite3

def debug_affiliation():
    conn = sqlite3.connect('doctors.db')
    cursor = conn.cursor()
    
    print("=== Checking 陳海聰醫生 ===\n")
    
    # Search for the doctor
    cursor.execute("""
        SELECT id, name_zh, name_en, is_affiliated, affiliation_status
        FROM doctors
        WHERE name_zh LIKE '%陳海%' OR name_zh LIKE '%海聰%'
        LIMIT 5
    """)
    
    doctors = cursor.fetchall()
    
    if not doctors:
        print("❌ No doctors found matching '陳海聰'")
        conn.close()
        return
    
    print(f"Found {len(doctors)} matching doctor(s):\n")
    
    for doctor in doctors:
        doc_id, name_zh, name_en, is_affiliated, affiliation_status = doctor
        print(f"Doctor ID: {doc_id}")
        print(f"Name (ZH): {name_zh}")
        print(f"Name (EN): {name_en}")
        print(f"is_affiliated: {is_affiliated}")
        print(f"affiliation_status: {affiliation_status}")
        
        # Check for account
        cursor.execute("""
            SELECT id, username, is_active
            FROM doctor_accounts
            WHERE doctor_id = ?
        """, (doc_id,))
        
        account = cursor.fetchone()
        
        if account:
            print(f"✅ HAS ACCOUNT:")
            print(f"   Account ID: {account[0]}")
            print(f"   Username: {account[1]}")
            print(f"   Active: {account[2]}")
        else:
            print(f"❌ NO ACCOUNT")
        
        print("-" * 50)
    
    print("\n=== All Doctors with Accounts ===\n")
    
    cursor.execute("""
        SELECT d.id, d.name_zh, d.is_affiliated, da.username
        FROM doctors d
        INNER JOIN doctor_accounts da ON d.id = da.doctor_id
        WHERE da.is_active = 1
    """)
    
    all_with_accounts = cursor.fetchall()
    
    if all_with_accounts:
        print(f"Total doctors with accounts: {len(all_with_accounts)}\n")
        for doc in all_with_accounts:
            doc_id, name, is_aff, username = doc
            status = "✅ Affiliated" if is_aff else "❌ NOT Affiliated"
            print(f"ID {doc_id}: {name} ({username}) - {status}")
    else:
        print("No doctors with accounts found")
    
    conn.close()

if __name__ == '__main__':
    debug_affiliation()
