"""
Quick Setup Script for Doctor Affiliation System
Automates the setup process and creates test data
"""

import sqlite3
import hashlib
import secrets
from datetime import datetime

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def setup_system():
    print("="*60)
    print("Doctor Affiliation System - Quick Setup")
    print("="*60)
    
    # Step 1: Run migration
    print("\n[1/5] Running database migration...")
    try:
        from create_affiliation_system import create_affiliation_tables
        create_affiliation_tables()
        print("✓ Database migration completed")
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return
    
    # Step 2: Create test doctor account
    print("\n[2/5] Creating test doctor account...")
    try:
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        # Check if test doctor exists
        cursor.execute("SELECT id FROM doctors WHERE email = 'test.doctor@example.com'")
        existing = cursor.fetchone()
        
        if existing:
            doctor_id = existing[0]
            print(f"✓ Test doctor already exists (ID: {doctor_id})")
        else:
            # Create test doctor
            cursor.execute("""
                INSERT INTO doctors (
                    name_zh, specialty_zh, qualifications_zh, languages_zh,
                    name_en, specialty_en, qualifications_en, languages_en,
                    email, contact_numbers, consultation_fee, consultation_hours,
                    clinic_addresses, is_affiliated, affiliation_status,
                    accepts_reservations, online_consultation, verified_credentials,
                    affiliation_date
                ) VALUES (
                    '測試醫生', '全科', '香港大學醫學院', '粵語、英語',
                    'Dr. Test', 'General Practice', 'MBBS, HKU', 'Cantonese, English',
                    'test.doctor@example.com', '9123-4567', 'HK$500', '週一至五 9:00-18:00',
                    '香港中環皇后大道中1號', 1, 'approved', 1, 1, 1,
                    CURRENT_TIMESTAMP
                )
            """)
            doctor_id = cursor.lastrowid
            print(f"✓ Test doctor created (ID: {doctor_id})")
        
        # Create doctor account
        cursor.execute("SELECT id FROM doctor_accounts WHERE doctor_id = ?", (doctor_id,))
        if not cursor.fetchone():
            test_password = "test123"
            password_hash = hash_password(test_password)
            
            cursor.execute("""
                INSERT INTO doctor_accounts (
                    doctor_id, username, password_hash, email, phone, is_active,
                    email_verified, phone_verified
                ) VALUES (?, ?, ?, ?, ?, 1, 1, 1)
            """, (doctor_id, 'testdoctor', password_hash, 'test.doctor@example.com', '91234567'))
            
            print(f"✓ Doctor account created")
            print(f"  Username: testdoctor")
            print(f"  Password: {test_password}")
        else:
            print("✓ Doctor account already exists")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"✗ Failed to create test doctor: {e}")
        return
    
    # Step 3: Create sample availability
    print("\n[3/5] Creating sample availability schedule...")
    try:
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        # Check if availability exists
        cursor.execute("SELECT COUNT(*) FROM doctor_availability WHERE doctor_id = ?", (doctor_id,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Create Monday to Friday, 9:00-18:00
            for day in range(5):  # 0=Monday to 4=Friday
                cursor.execute("""
                    INSERT INTO doctor_availability (
                        doctor_id, day_of_week, start_time, end_time,
                        slot_duration, max_patients_per_slot, location,
                        consultation_type, is_active
                    ) VALUES (?, ?, '09:00', '18:00', 30, 1, '中環診所', 'in-person', 1)
                """, (doctor_id, day))
            
            print("✓ Sample availability created (Mon-Fri, 9:00-18:00)")
        else:
            print(f"✓ Availability already exists ({count} schedules)")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"✗ Failed to create availability: {e}")
    
    # Step 4: Create sample reservation
    print("\n[4/5] Creating sample reservation...")
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Check if reservation exists
        cursor.execute("SELECT COUNT(*) FROM reservations WHERE doctor_id = ?", (doctor_id,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            from datetime import datetime, timedelta
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            confirmation_code = secrets.token_urlsafe(8).upper()
            
            cursor.execute("""
                INSERT INTO reservations (
                    doctor_id, patient_name, patient_phone, patient_email,
                    patient_age, patient_gender, reservation_date, reservation_time,
                    consultation_type, symptoms, status, confirmation_code
                ) VALUES (?, '測試病人', '98765432', 'patient@example.com',
                         35, '男', ?, '10:00', 'in-person', '頭痛、發燒', 'pending', ?)
            """, (doctor_id, tomorrow, confirmation_code))
            
            print(f"✓ Sample reservation created")
            print(f"  Date: {tomorrow} 10:00")
            print(f"  Confirmation code: {confirmation_code}")
        else:
            print(f"✓ Reservations already exist ({count} reservations)")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"✗ Failed to create reservation: {e}")
    
    # Step 5: Verify setup
    print("\n[5/5] Verifying setup...")
    try:
        conn_doctors = sqlite3.connect('doctors.db')
        conn_admin = sqlite3.connect('admin_data.db')
        
        cursor_doctors = conn_doctors.cursor()
        cursor_admin = conn_admin.cursor()
        
        # Count affiliated doctors
        cursor_doctors.execute("SELECT COUNT(*) FROM doctors WHERE is_affiliated = 1")
        affiliated_count = cursor_doctors.fetchone()[0]
        
        # Count doctor accounts
        cursor_doctors.execute("SELECT COUNT(*) FROM doctor_accounts")
        accounts_count = cursor_doctors.fetchone()[0]
        
        # Count availability schedules
        cursor_doctors.execute("SELECT COUNT(*) FROM doctor_availability")
        schedules_count = cursor_doctors.fetchone()[0]
        
        # Count reservations
        cursor_admin.execute("SELECT COUNT(*) FROM reservations")
        reservations_count = cursor_admin.fetchone()[0]
        
        print(f"✓ Affiliated doctors: {affiliated_count}")
        print(f"✓ Doctor accounts: {accounts_count}")
        print(f"✓ Availability schedules: {schedules_count}")
        print(f"✓ Reservations: {reservations_count}")
        
        conn_doctors.close()
        conn_admin.close()
        
    except Exception as e:
        print(f"✗ Verification failed: {e}")
    
    # Final instructions
    print("\n" + "="*60)
    print("✅ Setup completed successfully!")
    print("="*60)
    print("\nNext steps:")
    print("1. Start your Flask app: python app.py")
    print("2. Doctor login: http://localhost:5000/doctor/login")
    print("   - Username: testdoctor")
    print("   - Password: test123")
    print("3. Admin panel: http://localhost:5000/admin/affiliation/requests")
    print("4. Test booking: Browse doctors and click '立即預約'")
    print("\nFor full documentation, see:")
    print("- AFFILIATION_SYSTEM_README.md")
    print("- INTEGRATION_GUIDE.md")
    print("="*60)

if __name__ == "__main__":
    try:
        setup_system()
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
