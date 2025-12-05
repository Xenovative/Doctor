#!/usr/bin/env python3
"""
Migration script to add diagnosis_references table for tracking reference codes.

This table stores reference codes generated with each diagnosis, allowing:
1. Users to reference their diagnosis when booking appointments
2. Doctors to verify patient diagnoses
3. Admin to track usage for billing purposes
"""

import sqlite3
import os
from datetime import datetime

def create_backup(db_path):
    """Create a backup of the database before making changes"""
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist, will be created fresh")
        return None
    
    import shutil
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}_backup_{timestamp}"
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ Created backup: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return None

def add_diagnosis_references_table():
    """Add diagnosis_references table to admin_data.db"""
    print("\n=== ADDING DIAGNOSIS REFERENCES TABLE ===")
    
    db_path = 'admin_data.db'
    create_backup(db_path)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create diagnosis_references table
        print("Creating diagnosis_references table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS diagnosis_references (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference_code TEXT UNIQUE NOT NULL,
                query_id INTEGER NOT NULL,
                session_id TEXT,
                user_ip TEXT,
                
                -- Diagnosis summary
                symptoms TEXT,
                ai_analysis TEXT,
                recommended_specialty TEXT,
                matched_doctors_count INTEGER DEFAULT 0,
                
                -- Usage tracking
                is_used INTEGER DEFAULT 0,
                used_at DATETIME,
                used_by_doctor_id INTEGER,
                used_by_doctor_name TEXT,
                
                -- Billing
                is_billed INTEGER DEFAULT 0,
                billed_at DATETIME,
                billing_amount REAL DEFAULT 0,
                billing_notes TEXT,
                
                -- Timestamps
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                
                FOREIGN KEY (query_id) REFERENCES user_queries (id)
            )
        """)
        print("✅ Created diagnosis_references table")
        
        # Create indexes for performance
        print("Creating indexes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_diagnosis_references_code 
            ON diagnosis_references(reference_code)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_diagnosis_references_query 
            ON diagnosis_references(query_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_diagnosis_references_created 
            ON diagnosis_references(created_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_diagnosis_references_used 
            ON diagnosis_references(is_used, used_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_diagnosis_references_billed 
            ON diagnosis_references(is_billed, billed_at)
        """)
        print("✅ Created indexes")
        
        # Add reference_code column to user_queries if not exists
        print("Checking user_queries table for reference_code column...")
        cursor.execute("PRAGMA table_info(user_queries)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'reference_code' not in columns:
            cursor.execute("ALTER TABLE user_queries ADD COLUMN reference_code TEXT")
            print("✅ Added reference_code column to user_queries")
        else:
            print("ℹ️ reference_code column already exists in user_queries")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_migration():
    """Verify the migration was successful"""
    print("\n=== VERIFYING MIGRATION ===")
    
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Check diagnosis_references table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='diagnosis_references'")
        if cursor.fetchone():
            print("✅ diagnosis_references table exists")
            
            cursor.execute("PRAGMA table_info(diagnosis_references)")
            columns = [row[1] for row in cursor.fetchall()]
            print(f"   Columns: {', '.join(columns)}")
        else:
            print("❌ diagnosis_references table NOT found")
        
        # Check user_queries reference_code column
        cursor.execute("PRAGMA table_info(user_queries)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'reference_code' in columns:
            print("✅ reference_code column exists in user_queries")
        else:
            print("❌ reference_code column NOT found in user_queries")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("DIAGNOSIS REFERENCES MIGRATION SCRIPT")
    print("=" * 60)
    
    success = add_diagnosis_references_table()
    
    if success:
        verify_migration()
    
    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)
