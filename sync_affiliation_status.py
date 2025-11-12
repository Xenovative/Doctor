"""
Sync affiliation status between doctor_accounts and doctors tables
This ensures doctors with accounts are properly marked as affiliated
"""
import sqlite3
from datetime import datetime

def sync_affiliation_status():
    """Sync is_affiliated flag based on doctor_accounts table"""
    conn = sqlite3.connect('doctors.db')
    cursor = conn.cursor()
    
    print("=== Syncing Affiliation Status ===\n")
    
    # Get all doctors with accounts
    cursor.execute("""
        SELECT da.doctor_id, da.username, d.name_zh, d.name_en, d.is_affiliated, d.affiliation_status
        FROM doctor_accounts da
        JOIN doctors d ON da.doctor_id = d.id
        WHERE da.is_active = 1
    """)
    
    accounts = cursor.fetchall()
    
    if not accounts:
        print("No doctor accounts found.")
        conn.close()
        return
    
    print(f"Found {len(accounts)} doctor accounts\n")
    
    updated_count = 0
    
    for account in accounts:
        doctor_id, username, name_zh, name_en, is_affiliated, affiliation_status = account
        name = name_zh or name_en or 'Unknown'
        
        # Check if needs update
        if not is_affiliated or affiliation_status != 'approved':
            print(f"Updating: {name} (ID: {doctor_id}, Username: {username})")
            print(f"  Before: is_affiliated={is_affiliated}, status={affiliation_status}")
            
            cursor.execute("""
                UPDATE doctors
                SET is_affiliated = 1,
                    affiliation_status = 'approved',
                    affiliation_date = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), doctor_id))
            
            updated_count += 1
            print(f"  After: is_affiliated=1, status=approved ✅\n")
        else:
            print(f"Already synced: {name} (ID: {doctor_id}) ✅")
    
    conn.commit()
    conn.close()
    
    print(f"\n{'='*50}")
    print(f"Sync Complete!")
    print(f"Total accounts: {len(accounts)}")
    print(f"Updated: {updated_count}")
    print(f"Already synced: {len(accounts) - updated_count}")
    print(f"{'='*50}\n")
    
    if updated_count > 0:
        print("✅ Affiliation badges should now appear in the doctor database!")
        print("   Refresh the /admin/doctors page to see the changes.")
    else:
        print("✅ All accounts are already properly synced!")

if __name__ == '__main__':
    try:
        sync_affiliation_status()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
