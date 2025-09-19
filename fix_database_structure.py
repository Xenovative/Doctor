#!/usr/bin/env python3
"""
Database Structure Fix Script for AI Hong Kong Medical Matching System
This script fixes all database structure issues in one go.

Recent Updates:
- Added tab_permissions column to admin_users table with default permissions
- Added severe_cases table for monitoring critical medical cases
- Added bug_reports table for issue tracking
- Added gender and priority columns to user_queries table
- Added analysis_report column to user_queries table
- Updated all indexes for better performance
- Includes comprehensive verification of all tables and columns

This script is safe to run multiple times and will only add missing components.
"""

import sqlite3
import os
import shutil
from datetime import datetime
import sys

def create_backup(db_path):
    """Create a backup of the database before making changes"""
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist, will be created fresh")
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}_backup_{timestamp}"
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ Created backup: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return None

def fix_doctors_db():
    """Fix doctors.db structure"""
    print("\n=== FIXING DOCTORS.DB STRUCTURE ===")
    
    # Create backup
    backup_path = create_backup('doctors.db')
    
    try:
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        # Get existing table info
        cursor.execute("PRAGMA table_info(doctors)")
        existing_columns = {row[1]: row[2] for row in cursor.fetchall()}
        print(f"Found {len(existing_columns)} existing columns")
        
        # Define required columns with their types
        required_columns = {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'name_zh': 'TEXT',
            'specialty_zh': 'TEXT', 
            'qualifications_zh': 'TEXT',
            'languages_zh': 'TEXT',
            'name_en': 'TEXT',
            'specialty_en': 'TEXT',
            'qualifications_en': 'TEXT', 
            'languages_en': 'TEXT',
            'contact_numbers': 'TEXT',
            'email': 'TEXT',
            'clinic_addresses': 'TEXT',
            'consultation_hours': 'TEXT',
            'consultation_fee': 'TEXT',
            'profile_url': 'TEXT',
            'registration_number': 'TEXT',
            'languages_available': 'TEXT',
            'priority_flag': 'INTEGER DEFAULT 0',
            # Legacy columns for compatibility
            'name': 'TEXT',
            'specialty': 'TEXT',
            'qualifications': 'TEXT',
            'languages': 'TEXT',
            'phone': 'TEXT',
            'address': 'TEXT'
        }
        
        # Check if doctors table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='doctors'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            print("Creating doctors table from scratch...")
            columns_def = ', '.join([f"{col} {type_def}" for col, type_def in required_columns.items()])
            cursor.execute(f"CREATE TABLE doctors ({columns_def})")
            print("✅ Created doctors table")
        else:
            # Add missing columns
            missing_columns = set(required_columns.keys()) - set(existing_columns.keys())
            
            for column in missing_columns:
                column_type = required_columns[column].split(' DEFAULT ')[0]  # Remove DEFAULT part for ALTER TABLE
                try:
                    cursor.execute(f"ALTER TABLE doctors ADD COLUMN {column} {column_type}")
                    print(f"✅ Added column: {column}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e):
                        print(f"⚠️  Warning adding column {column}: {e}")
        
        # Create indexes for better performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_doctors_specialty ON doctors(specialty)",
            "CREATE INDEX IF NOT EXISTS idx_doctors_specialty_zh ON doctors(specialty_zh)",
            "CREATE INDEX IF NOT EXISTS idx_doctors_name ON doctors(name)",
            "CREATE INDEX IF NOT EXISTS idx_doctors_name_zh ON doctors(name_zh)",
            "CREATE INDEX IF NOT EXISTS idx_doctors_priority ON doctors(priority_flag)",
            "CREATE INDEX IF NOT EXISTS idx_doctors_addresses ON doctors(clinic_addresses)",
            "CREATE INDEX IF NOT EXISTS idx_doctors_address ON doctors(address)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                print(f"✅ Created index")
            except Exception as e:
                print(f"⚠️  Warning creating index: {e}")
        
        conn.commit()
        conn.close()
        print("✅ doctors.db structure fixed successfully")
        
    except Exception as e:
        print(f"❌ Error fixing doctors.db: {e}")
        if backup_path and os.path.exists(backup_path):
            print(f"Restoring from backup: {backup_path}")
            shutil.copy2(backup_path, 'doctors.db')

def fix_admin_data_db():
    """Fix admin_data.db structure"""
    print("\n=== FIXING ADMIN_DATA.DB STRUCTURE ===")
    
    # Create backup
    backup_path = create_backup('admin_data.db')
    
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                user_ip TEXT,
                user_agent TEXT,
                data TEXT,
                session_id TEXT
            )
        ''')
        
        # User queries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                age INTEGER,
                symptoms TEXT,
                chronic_conditions TEXT,
                language TEXT,
                location TEXT,
                detailed_health_info TEXT,
                ai_diagnosis TEXT,
                recommended_specialty TEXT,
                matched_doctors_count INTEGER,
                user_ip TEXT,
                session_id TEXT
            )
        ''')
        
        # Check for missing columns in user_queries
        cursor.execute("PRAGMA table_info(user_queries)")
        columns = [row[1] for row in cursor.fetchall()]
        
        user_queries_required_columns = {
            'analysis_report': 'TEXT',
            'gender': 'TEXT',
            'priority': 'TEXT DEFAULT "normal"'
        }
        
        for column, column_type in user_queries_required_columns.items():
            if column not in columns:
                try:
                    cursor.execute(f"ALTER TABLE user_queries ADD COLUMN {column} {column_type}")
                    print(f"✅ Added {column} column to user_queries")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e):
                        print(f"⚠️  Warning adding {column} column: {e}")
        
        # Doctor clicks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS doctor_clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                doctor_name TEXT,
                doctor_specialty TEXT,
                user_ip TEXT,
                session_id TEXT,
                query_id INTEGER,
                FOREIGN KEY (query_id) REFERENCES user_queries (id)
            )
        ''')
        
        # System config table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT UNIQUE,
                config_value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Admin users table with 2FA support
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'admin',
                permissions TEXT DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                is_active BOOLEAN DEFAULT 1,
                created_by INTEGER,
                totp_secret TEXT,
                totp_enabled BOOLEAN DEFAULT 0,
                backup_codes TEXT,
                FOREIGN KEY (created_by) REFERENCES admin_users (id)
            )
        ''')
        
        # Check for missing columns in admin_users
        cursor.execute("PRAGMA table_info(admin_users)")
        admin_columns = [row[1] for row in cursor.fetchall()]
        
        admin_required_columns = {
            'totp_secret': 'TEXT',
            'totp_enabled': 'BOOLEAN DEFAULT 0',
            'backup_codes': 'TEXT',
            'tab_permissions': 'TEXT DEFAULT NULL'
        }
        
        for column, column_type in admin_required_columns.items():
            if column not in admin_columns:
                try:
                    cursor.execute(f"ALTER TABLE admin_users ADD COLUMN {column} {column_type}")
                    print(f"✅ Added {column} column to admin_users")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e):
                        print(f"⚠️  Warning adding {column} column: {e}")
        
        # Set default tab permissions for users who don't have them
        import json
        default_tab_permissions = {
            "dashboard": True,
            "analytics": True,
            "config": True,
            "doctors": True,
            "users": True,
            "bug_reports": True,
            "severe_cases": True
        }
        
        try:
            cursor.execute('SELECT id FROM admin_users WHERE tab_permissions IS NULL OR tab_permissions = ""')
            users_without_permissions = cursor.fetchall()
            
            if users_without_permissions:
                default_permissions_json = json.dumps(default_tab_permissions)
                for (user_id,) in users_without_permissions:
                    cursor.execute('UPDATE admin_users SET tab_permissions = ? WHERE id = ?', 
                                 (default_permissions_json, user_id))
                print(f"✅ Set default tab permissions for {len(users_without_permissions)} users")
        except Exception as e:
            print(f"⚠️  Warning setting default tab permissions: {e}")
        
        # Admin config table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Severe cases table for monitoring critical medical cases
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS severe_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_query_id INTEGER,
                age INTEGER,
                gender TEXT,
                symptoms TEXT,
                chronic_conditions TEXT,
                severe_symptoms TEXT,
                severe_conditions TEXT,
                user_ip TEXT,
                session_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                admin_reviewed BOOLEAN DEFAULT 0,
                admin_notes TEXT,
                user_acknowledged BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_query_id) REFERENCES user_queries (id)
            )
        ''')
        
        # Bug reports table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bug_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                contact_info TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                url TEXT,
                user_agent TEXT,
                status TEXT DEFAULT 'open',
                image_path TEXT
            )
        ''')
        
        # Create indexes for better performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON analytics(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_event_type ON analytics(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_user_queries_timestamp ON user_queries(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_user_queries_ip ON user_queries(user_ip)",
            "CREATE INDEX IF NOT EXISTS idx_user_queries_gender ON user_queries(gender)",
            "CREATE INDEX IF NOT EXISTS idx_user_queries_priority ON user_queries(priority)",
            "CREATE INDEX IF NOT EXISTS idx_doctor_clicks_timestamp ON doctor_clicks(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(config_key)",
            "CREATE INDEX IF NOT EXISTS idx_admin_config_key ON admin_config(key)",
            "CREATE INDEX IF NOT EXISTS idx_severe_cases_timestamp ON severe_cases(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_severe_cases_user_query ON severe_cases(user_query_id)",
            "CREATE INDEX IF NOT EXISTS idx_severe_cases_reviewed ON severe_cases(admin_reviewed)",
            "CREATE INDEX IF NOT EXISTS idx_bug_reports_timestamp ON bug_reports(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_bug_reports_status ON bug_reports(status)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                print(f"✅ Created index")
            except Exception as e:
                print(f"⚠️  Warning creating index: {e}")
        
        conn.commit()
        conn.close()
        print("✅ admin_data.db structure fixed successfully")
        
    except Exception as e:
        print(f"❌ Error fixing admin_data.db: {e}")
        if backup_path and os.path.exists(backup_path):
            print(f"Restoring from backup: {backup_path}")
            shutil.copy2(backup_path, 'admin_data.db')

def verify_database_structure():
    """Verify that all database structures are correct"""
    print("\n=== VERIFYING DATABASE STRUCTURE ===")
    
    # Verify doctors.db
    try:
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM doctors")
        doctor_count = cursor.fetchone()[0]
        print(f"✅ doctors.db: {doctor_count} doctors found")
        
        cursor.execute("PRAGMA table_info(doctors)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"✅ doctors table has {len(columns)} columns")
        
        conn.close()
    except Exception as e:
        print(f"❌ Error verifying doctors.db: {e}")
    
    # Verify admin_data.db
    try:
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        
        # Check all required tables
        required_tables = ['analytics', 'user_queries', 'doctor_clicks', 'system_config', 'admin_users', 'admin_config', 'severe_cases', 'bug_reports']
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        for table in required_tables:
            if table in existing_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ {table}: {count} records")
            else:
                print(f"❌ Missing table: {table}")
        
        # Verify critical columns exist
        print("\n--- Verifying Critical Columns ---")
        
        # Check user_queries columns
        cursor.execute("PRAGMA table_info(user_queries)")
        user_queries_columns = [row[1] for row in cursor.fetchall()]
        required_user_queries_columns = ['analysis_report', 'gender', 'priority']
        for col in required_user_queries_columns:
            if col in user_queries_columns:
                print(f"✅ user_queries.{col} exists")
            else:
                print(f"❌ user_queries.{col} missing")
        
        # Check admin_users columns
        cursor.execute("PRAGMA table_info(admin_users)")
        admin_users_columns = [row[1] for row in cursor.fetchall()]
        required_admin_columns = ['totp_secret', 'totp_enabled', 'backup_codes', 'tab_permissions']
        for col in required_admin_columns:
            if col in admin_users_columns:
                print(f"✅ admin_users.{col} exists")
            else:
                print(f"❌ admin_users.{col} missing")
        
        # Check if users have tab_permissions set
        cursor.execute('SELECT COUNT(*) FROM admin_users WHERE tab_permissions IS NOT NULL AND tab_permissions != ""')
        users_with_permissions = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM admin_users')
        total_users = cursor.fetchone()[0]
        print(f"✅ Tab permissions: {users_with_permissions}/{total_users} users have permissions set")
        
        conn.close()
    except Exception as e:
        print(f"❌ Error verifying admin_data.db: {e}")

def main():
    """Main function to run all database fixes"""
    print("🔧 AI Hong Kong Medical System - Database Structure Fix")
    print("=" * 60)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"Working directory: {script_dir}")
    
    try:
        # Fix both databases
        fix_doctors_db()
        fix_admin_data_db()
        
        # Verify everything is working
        verify_database_structure()
        
        print("\n" + "=" * 60)
        print("🎉 Database structure fix completed successfully!")
        print("All tables and columns should now be properly configured.")
        
    except Exception as e:
        print(f"\n❌ Fatal error during database fix: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
