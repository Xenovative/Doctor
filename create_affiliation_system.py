"""
Migration script to create doctor affiliation and reservation system
Adds tables for:
- Affiliated doctor accounts
- Doctor availability schedules
- Patient reservations
- Reservation status tracking
"""

import sqlite3
from datetime import datetime

def create_affiliation_tables():
    """Create all tables needed for doctor affiliation and reservation system"""
    
    # Connect to doctors.db for affiliated doctor data
    conn_doctors = sqlite3.connect('doctors.db')
    cursor_doctors = conn_doctors.cursor()
    
    # Connect to admin_data.db for reservations
    conn_admin = sqlite3.connect('admin_data.db')
    cursor_admin = conn_admin.cursor()
    
    print("Creating affiliation system tables...")
    
    # 1. Add affiliation columns to existing doctors table
    print("\n1. Adding affiliation columns to doctors table...")
    try:
        cursor_doctors.execute("""
            ALTER TABLE doctors ADD COLUMN is_affiliated INTEGER DEFAULT 0
        """)
        print("   ✓ Added is_affiliated column")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("   ℹ is_affiliated column already exists")
        else:
            raise
    
    try:
        cursor_doctors.execute("""
            ALTER TABLE doctors ADD COLUMN affiliation_status TEXT DEFAULT 'none'
        """)
        print("   ✓ Added affiliation_status column (none/pending/approved/suspended)")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("   ℹ affiliation_status column already exists")
        else:
            raise
    
    try:
        cursor_doctors.execute("""
            ALTER TABLE doctors ADD COLUMN affiliation_date TEXT
        """)
        print("   ✓ Added affiliation_date column")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("   ℹ affiliation_date column already exists")
        else:
            raise
    
    try:
        cursor_doctors.execute("""
            ALTER TABLE doctors ADD COLUMN accepts_reservations INTEGER DEFAULT 0
        """)
        print("   ✓ Added accepts_reservations column")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("   ℹ accepts_reservations column already exists")
        else:
            raise
    
    try:
        cursor_doctors.execute("""
            ALTER TABLE doctors ADD COLUMN online_consultation INTEGER DEFAULT 0
        """)
        print("   ✓ Added online_consultation column")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("   ℹ online_consultation column already exists")
        else:
            raise
    
    try:
        cursor_doctors.execute("""
            ALTER TABLE doctors ADD COLUMN verified_credentials INTEGER DEFAULT 0
        """)
        print("   ✓ Added verified_credentials column")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("   ℹ verified_credentials column already exists")
        else:
            raise
    
    # 2. Create doctor_accounts table for authentication
    print("\n2. Creating doctor_accounts table...")
    cursor_doctors.execute("""
        CREATE TABLE IF NOT EXISTS doctor_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            totp_enabled INTEGER DEFAULT 0,
            totp_secret TEXT,
            backup_codes TEXT,
            is_active INTEGER DEFAULT 1,
            email_verified INTEGER DEFAULT 0,
            phone_verified INTEGER DEFAULT 0,
            last_login DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (doctor_id) REFERENCES doctors (id) ON DELETE CASCADE
        )
    """)
    print("   ✓ Created doctor_accounts table")
    
    # 3. Create doctor_availability table for schedules
    print("\n3. Creating doctor_availability table...")
    cursor_doctors.execute("""
        CREATE TABLE IF NOT EXISTS doctor_availability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            day_of_week INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            slot_duration INTEGER DEFAULT 30,
            max_patients_per_slot INTEGER DEFAULT 1,
            is_active INTEGER DEFAULT 1,
            location TEXT,
            consultation_type TEXT DEFAULT 'in-person',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (doctor_id) REFERENCES doctors (id) ON DELETE CASCADE
        )
    """)
    print("   ✓ Created doctor_availability table")
    
    # 4. Create doctor_time_off table for exceptions
    print("\n4. Creating doctor_time_off table...")
    cursor_doctors.execute("""
        CREATE TABLE IF NOT EXISTS doctor_time_off (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            reason TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (doctor_id) REFERENCES doctors (id) ON DELETE CASCADE
        )
    """)
    print("   ✓ Created doctor_time_off table")
    
    # 5. Create reservations table in admin_data.db
    print("\n5. Creating reservations table...")
    cursor_admin.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            patient_name TEXT NOT NULL,
            patient_phone TEXT NOT NULL,
            patient_email TEXT,
            patient_age INTEGER,
            patient_gender TEXT,
            reservation_date TEXT NOT NULL,
            reservation_time TEXT NOT NULL,
            consultation_type TEXT DEFAULT 'in-person',
            symptoms TEXT,
            chronic_conditions TEXT,
            query_id INTEGER,
            status TEXT DEFAULT 'pending',
            confirmation_code TEXT UNIQUE,
            doctor_notes TEXT,
            cancellation_reason TEXT,
            reminder_sent INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            confirmed_at DATETIME,
            cancelled_at DATETIME,
            completed_at DATETIME,
            FOREIGN KEY (query_id) REFERENCES user_queries (id)
        )
    """)
    print("   ✓ Created reservations table")
    
    # 6. Create reservation_history table for audit trail
    print("\n6. Creating reservation_history table...")
    cursor_admin.execute("""
        CREATE TABLE IF NOT EXISTS reservation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reservation_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            old_status TEXT,
            new_status TEXT,
            notes TEXT,
            performed_by TEXT,
            performed_by_type TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (reservation_id) REFERENCES reservations (id) ON DELETE CASCADE
        )
    """)
    print("   ✓ Created reservation_history table")
    
    # 7. Create doctor_reviews table
    print("\n7. Creating doctor_reviews table...")
    cursor_admin.execute("""
        CREATE TABLE IF NOT EXISTS doctor_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            reservation_id INTEGER,
            patient_name TEXT,
            rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
            review_text TEXT,
            is_verified INTEGER DEFAULT 0,
            is_visible INTEGER DEFAULT 1,
            admin_response TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (reservation_id) REFERENCES reservations (id)
        )
    """)
    print("   ✓ Created doctor_reviews table")
    
    # 8. Create doctor_notifications table
    print("\n8. Creating doctor_notifications table...")
    cursor_doctors.execute("""
        CREATE TABLE IF NOT EXISTS doctor_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            notification_type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            related_id INTEGER,
            is_read INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            read_at DATETIME,
            FOREIGN KEY (doctor_id) REFERENCES doctors (id) ON DELETE CASCADE
        )
    """)
    print("   ✓ Created doctor_notifications table")
    
    # Create indexes for performance
    print("\n9. Creating indexes...")
    
    # doctors.db indexes
    cursor_doctors.execute("""
        CREATE INDEX IF NOT EXISTS idx_doctors_affiliated 
        ON doctors(is_affiliated, affiliation_status)
    """)
    cursor_doctors.execute("""
        CREATE INDEX IF NOT EXISTS idx_doctor_accounts_email 
        ON doctor_accounts(email)
    """)
    cursor_doctors.execute("""
        CREATE INDEX IF NOT EXISTS idx_doctor_availability_doctor 
        ON doctor_availability(doctor_id, day_of_week, is_active)
    """)
    cursor_doctors.execute("""
        CREATE INDEX IF NOT EXISTS idx_doctor_time_off_dates 
        ON doctor_time_off(doctor_id, start_date, end_date)
    """)
    cursor_doctors.execute("""
        CREATE INDEX IF NOT EXISTS idx_doctor_notifications_doctor 
        ON doctor_notifications(doctor_id, is_read, created_at)
    """)
    
    # admin_data.db indexes
    cursor_admin.execute("""
        CREATE INDEX IF NOT EXISTS idx_reservations_doctor 
        ON reservations(doctor_id, reservation_date, status)
    """)
    cursor_admin.execute("""
        CREATE INDEX IF NOT EXISTS idx_reservations_patient 
        ON reservations(patient_phone, patient_email)
    """)
    cursor_admin.execute("""
        CREATE INDEX IF NOT EXISTS idx_reservations_confirmation 
        ON reservations(confirmation_code)
    """)
    cursor_admin.execute("""
        CREATE INDEX IF NOT EXISTS idx_reservation_history_reservation 
        ON reservation_history(reservation_id, created_at)
    """)
    cursor_admin.execute("""
        CREATE INDEX IF NOT EXISTS idx_doctor_reviews_doctor 
        ON doctor_reviews(doctor_id, is_visible, created_at)
    """)
    
    print("   ✓ Created all indexes")
    
    # Commit changes
    conn_doctors.commit()
    conn_admin.commit()
    
    print("\n" + "="*60)
    print("✅ Affiliation system tables created successfully!")
    print("="*60)
    
    # Print summary
    print("\n📊 Summary:")
    print(f"   • Modified doctors table with {6} new columns")
    print(f"   • Created {4} new tables in doctors.db")
    print(f"   • Created {3} new tables in admin_data.db")
    print(f"   • Created {10} indexes for performance")
    
    # Close connections
    conn_doctors.close()
    conn_admin.close()
    
    print("\n✅ Migration completed successfully!")
    print("\nNext steps:")
    print("1. Run this script: python create_affiliation_system.py")
    print("2. Implement doctor portal routes in app.py")
    print("3. Create doctor portal templates")
    print("4. Implement reservation system endpoints")
    print("5. Update admin panel with affiliation management")

if __name__ == "__main__":
    try:
        create_affiliation_tables()
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
