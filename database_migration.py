#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Migration Tool for Doctor AI System
Seamlessly integrates new crawled database with existing system
"""

import sqlite3
import pandas as pd
import os
import shutil
from datetime import datetime
import json
import csv
import io

class DatabaseMigrator:
    def __init__(self):
        self.current_db = "doctors.db"
        self.backup_dbs = [
            "doctors.db.backup_20250905_154930",  # 9.4MB
            "doctors.db.backup_20250905_155008",  # 9.4MB  
            "doctors_old_backup_20250905_155713.db"  # 8.9MB
        ]
        self.csv_file = "assets/finddoc_doctors_detailed_full_20250905.csv"
        
    def analyze_current_structure(self):
        """Analyze current database and CSV structure"""
        print("🔍 ANALYZING CURRENT DATABASE STRUCTURE")
        print("=" * 60)
        
        # Check current database
        if os.path.exists(self.current_db):
            self._analyze_db(self.current_db, "Current Database")
        
        # Check backup databases
        for backup_db in self.backup_dbs:
            if os.path.exists(backup_db):
                self._analyze_db(backup_db, f"Backup: {backup_db}")
        
        # Check CSV file
        if os.path.exists(self.csv_file):
            self._analyze_csv(self.csv_file)
        else:
            print(f"❌ CSV file not found: {self.csv_file}")
    
    def _analyze_db(self, db_path, name):
        """Analyze individual database"""
        try:
            size_mb = os.path.getsize(db_path) / 1024 / 1024
            print(f"\n📊 {name} ({size_mb:.1f} MB)")
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"Tables: {tables}")
            
            # Check doctors table if exists
            if 'doctors' in tables:
                cursor.execute("PRAGMA table_info(doctors)")
                columns = cursor.fetchall()
                print(f"Doctors table: {len(columns)} columns")
                
                cursor.execute("SELECT COUNT(*) FROM doctors")
                count = cursor.fetchone()[0]
                print(f"Records: {count:,}")
                
                # Sample record
                cursor.execute("SELECT * FROM doctors LIMIT 1")
                sample = cursor.fetchone()
                if sample:
                    print(f"Sample: {sample[:3]}...")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error analyzing {name}: {e}")
    
    def _analyze_csv(self, csv_path):
        """Analyze CSV file structure"""
        try:
            size_mb = os.path.getsize(csv_path) / 1024 / 1024
            print(f"\n📊 CSV File ({size_mb:.1f} MB)")
            
            # Read first few rows to understand structure
            df = pd.read_csv(csv_path, nrows=5)
            print(f"Columns ({len(df.columns)}): {list(df.columns)}")
            print(f"Sample data:")
            for i, row in df.iterrows():
                print(f"  Row {i+1}: {dict(list(row.items())[:3])}...")
                
            # Get total row count
            total_rows = sum(1 for line in open(csv_path, 'r', encoding='utf-8')) - 1
            print(f"Total records: {total_rows:,}")
            
        except Exception as e:
            print(f"❌ Error analyzing CSV: {e}")
    
    def create_unified_database(self):
        """Create new unified database structure"""
        print("\n🔧 CREATING UNIFIED DATABASE STRUCTURE")
        print("=" * 60)
        
        # Backup current database
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"doctors_backup_before_migration_{timestamp}.db"
        
        if os.path.exists(self.current_db):
            shutil.copy2(self.current_db, backup_name)
            print(f"✅ Current database backed up to: {backup_name}")
        
        # Create new database with enhanced structure
        conn = sqlite3.connect(self.current_db)
        cursor = conn.cursor()
        
        # Drop existing doctors table if exists
        cursor.execute("DROP TABLE IF EXISTS doctors")
        
        # Create enhanced doctors table
        cursor.execute('''
            CREATE TABLE doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                specialty TEXT,
                subspecialty TEXT,
                languages TEXT,
                qualifications TEXT,
                experience_years INTEGER,
                clinic_name TEXT,
                clinic_addresses TEXT,
                contact_numbers TEXT,
                email TEXT,
                website TEXT,
                district TEXT,
                area TEXT,
                region TEXT,
                consultation_fee_range TEXT,
                services TEXT,
                hospital_affiliations TEXT,
                medical_school TEXT,
                license_number TEXT,
                gender TEXT,
                consultation_hours TEXT,
                emergency_services BOOLEAN DEFAULT 0,
                telemedicine BOOLEAN DEFAULT 0,
                insurance_accepted TEXT,
                rating REAL DEFAULT 0.0,
                review_count INTEGER DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                data_source TEXT DEFAULT 'migration',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX idx_doctors_name ON doctors(name)")
        cursor.execute("CREATE INDEX idx_doctors_specialty ON doctors(specialty)")
        cursor.execute("CREATE INDEX idx_doctors_district ON doctors(district)")
        cursor.execute("CREATE INDEX idx_doctors_languages ON doctors(languages)")
        
        conn.commit()
        conn.close()
        
        print("✅ New unified database structure created")
        
    def migrate_csv_data(self):
        """Migrate data from CSV to database"""
        print("\n📥 MIGRATING CSV DATA TO DATABASE")
        print("=" * 60)
        
        if not os.path.exists(self.csv_file):
            print(f"❌ CSV file not found: {self.csv_file}")
            return False
        
        try:
            # Read CSV data
            df = pd.read_csv(self.csv_file)
            print(f"📊 Found {len(df):,} records in CSV")
            
            # Connect to database
            conn = sqlite3.connect(self.current_db)
            cursor = conn.cursor()
            
            # Map CSV columns to database columns
            column_mapping = self._create_column_mapping(df.columns)
            
            # Insert data
            inserted_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                try:
                    # Map row data to database columns
                    mapped_data = self._map_row_data(row, column_mapping)
                    
                    # Insert into database
                    placeholders = ', '.join(['?' for _ in mapped_data.keys()])
                    columns = ', '.join(mapped_data.keys())
                    
                    cursor.execute(f'''
                        INSERT INTO doctors ({columns})
                        VALUES ({placeholders})
                    ''', list(mapped_data.values()))
                    
                    inserted_count += 1
                    
                    if inserted_count % 1000 == 0:
                        print(f"  Processed {inserted_count:,} records...")
                        
                except Exception as e:
                    error_count += 1
                    if error_count <= 10:  # Show first 10 errors
                        print(f"  ❌ Error inserting row {index}: {e}")
            
            conn.commit()
            conn.close()
            
            print(f"✅ Migration completed:")
            print(f"  - Inserted: {inserted_count:,} records")
            print(f"  - Errors: {error_count:,} records")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False
    
    def _create_column_mapping(self, csv_columns):
        """Create mapping between CSV columns and database columns"""
        mapping = {}
        
        # Common mappings (adjust based on actual CSV structure)
        column_map = {
            'name': ['name', 'doctor_name', 'physician_name'],
            'specialty': ['specialty', 'speciality', 'department'],
            'subspecialty': ['subspecialty', 'sub_specialty'],
            'languages': ['languages', 'language', 'spoken_languages'],
            'qualifications': ['qualifications', 'qualification', 'education'],
            'clinic_name': ['clinic_name', 'clinic', 'hospital_name'],
            'clinic_addresses': ['clinic_addresses', 'address', 'clinic_address'],
            'contact_numbers': ['contact_numbers', 'phone', 'telephone'],
            'email': ['email', 'email_address'],
            'website': ['website', 'url'],
            'district': ['district', 'area', 'location'],
            'region': ['region', 'territory']
        }
        
        # Find best matches
        for db_col, possible_names in column_map.items():
            for csv_col in csv_columns:
                if csv_col.lower() in [name.lower() for name in possible_names]:
                    mapping[db_col] = csv_col
                    break
        
        return mapping
    
    def _map_row_data(self, row, column_mapping):
        """Map CSV row data to database format"""
        mapped_data = {}
        
        for db_col, csv_col in column_mapping.items():
            if csv_col in row.index:
                value = row[csv_col]
                # Clean and format data
                if pd.isna(value):
                    mapped_data[db_col] = None
                else:
                    mapped_data[db_col] = str(value).strip()
        
        # Set default values
        mapped_data['data_source'] = 'csv_migration'
        mapped_data['created_at'] = datetime.now().isoformat()
        mapped_data['updated_at'] = datetime.now().isoformat()
        
        return mapped_data
    
    def update_app_integration(self):
        """Update app.py to use database instead of CSV"""
        print("\n🔄 UPDATING APPLICATION INTEGRATION")
        print("=" * 60)
        
        # Create new database loader function
        db_loader_code = '''
def load_doctors_from_database():
    """Load doctors data from SQLite database"""
    try:
        conn = sqlite3.connect('doctors.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM doctors ORDER BY name")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        doctors_data = []
        for row in rows:
            doctor_dict = dict(zip(columns, row))
            doctors_data.append(doctor_dict)
        
        conn.close()
        print(f"✅ Loaded {len(doctors_data):,} doctors from database")
        return doctors_data
        
    except Exception as e:
        print(f"❌ Error loading doctors from database: {e}")
        # Fallback to CSV if database fails
        return load_doctors_data_csv()

def load_doctors_data_csv():
    """Fallback: Load doctors data from CSV"""
    csv_path = os.path.join('assets', 'finddoc_doctors_detailed 2.csv')
    try:
        df = pd.read_csv(csv_path)
        return df.to_dict('records')
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return []
'''
        
        print("✅ Database integration code prepared")
        print("📝 Manual step required: Update app.py to use load_doctors_from_database()")
        
    def run_full_migration(self):
        """Run complete migration process"""
        print("🚀 STARTING FULL DATABASE MIGRATION")
        print("=" * 60)
        
        # Step 1: Analyze current structure
        self.analyze_current_structure()
        
        # Step 2: Create unified database
        self.create_unified_database()
        
        # Step 3: Migrate CSV data
        if self.migrate_csv_data():
            print("\n✅ MIGRATION COMPLETED SUCCESSFULLY")
            
            # Step 4: Update app integration
            self.update_app_integration()
            
            print("\n📋 NEXT STEPS:")
            print("1. Update app.py to use database instead of CSV")
            print("2. Test the application with new database")
            print("3. Monitor performance and data quality")
            
        else:
            print("\n❌ MIGRATION FAILED")
            print("Please check errors and retry")

if __name__ == "__main__":
    migrator = DatabaseMigrator()
    migrator.run_full_migration()
