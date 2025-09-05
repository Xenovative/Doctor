#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Structure Analysis Tool
Analyzes current and backup databases to understand schema differences
"""

import sqlite3
import os
from datetime import datetime

def analyze_database_structure(db_path, db_name):
    """Analyze database structure and return schema info"""
    if not os.path.exists(db_path):
        return f"❌ Database not found: {db_path}"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"\n📊 Analyzing {db_name} ({os.path.getsize(db_path)} bytes)")
        print("=" * 60)
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("❌ No tables found")
            return
            
        for table in tables:
            table_name = table[0]
            print(f"\n🗂️  Table: {table_name}")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print("   Columns:")
            for col in columns:
                col_id, name, data_type, not_null, default, pk = col
                pk_marker = " (PK)" if pk else ""
                null_marker = " NOT NULL" if not_null else ""
                default_marker = f" DEFAULT {default}" if default else ""
                print(f"     - {name}: {data_type}{pk_marker}{null_marker}{default_marker}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            row_count = cursor.fetchone()[0]
            print(f"   Rows: {row_count:,}")
            
            # Sample data for doctors table
            if table_name.lower() == 'doctors' and row_count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                sample_rows = cursor.fetchall()
                print("   Sample data:")
                for i, row in enumerate(sample_rows, 1):
                    print(f"     Row {i}: {row[:5]}..." if len(row) > 5 else f"     Row {i}: {row}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing {db_name}: {e}")
        return False

def compare_databases():
    """Compare current database with backup databases"""
    
    # Database files to analyze
    databases = [
        ("doctors.db", "Current Database"),
        ("doctors.db.backup_20250905_154857", "Backup 1 (4.3MB)"),
        ("doctors.db.backup_20250905_154930", "Backup 2 (9.4MB)"),
        ("doctors.db.backup_20250905_155008", "Backup 3 (9.4MB)"),
        ("doctors_old_backup_20250905_155615.db", "Old Backup 1 (5.3MB)"),
        ("doctors_old_backup_20250905_155713.db", "Old Backup 2 (8.9MB)")
    ]
    
    print("🔍 DATABASE STRUCTURE ANALYSIS")
    print("=" * 60)
    
    results = {}
    
    for db_file, description in databases:
        db_path = f"c:/AIapps/Doctor/{db_file}"
        if os.path.exists(db_path):
            results[db_file] = analyze_database_structure(db_path, description)
        else:
            print(f"❌ Not found: {db_file}")
    
    # Summary
    print("\n📋 SUMMARY")
    print("=" * 60)
    
    largest_db = None
    largest_size = 0
    
    for db_file, _ in databases:
        db_path = f"c:/AIapps/Doctor/{db_file}"
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            if size > largest_size:
                largest_size = size
                largest_db = db_file
            print(f"📁 {db_file}: {size:,} bytes ({size/1024/1024:.1f} MB)")
    
    if largest_db:
        print(f"\n🎯 Recommended source for migration: {largest_db} ({largest_size/1024/1024:.1f} MB)")
    
    return results

def get_detailed_doctor_info(db_path, limit=5):
    """Get detailed information about doctors in the database"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if doctors table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='doctors';")
        if not cursor.fetchone():
            print("❌ No 'doctors' table found")
            return
        
        # Get column names
        cursor.execute("PRAGMA table_info(doctors);")
        columns = [col[1] for col in cursor.fetchall()]
        
        print(f"\n📋 Doctor Records Sample (Columns: {', '.join(columns)})")
        print("-" * 80)
        
        # Get sample records
        cursor.execute(f"SELECT * FROM doctors LIMIT {limit};")
        records = cursor.fetchall()
        
        for i, record in enumerate(records, 1):
            print(f"\nDoctor {i}:")
            for col_name, value in zip(columns, record):
                if value:  # Only show non-empty values
                    print(f"  {col_name}: {value}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error getting doctor info: {e}")

if __name__ == "__main__":
    # Run analysis
    results = compare_databases()
    
    # Get detailed info from largest database
    largest_files = [
        "doctors.db.backup_20250905_154930",
        "doctors.db.backup_20250905_155008", 
        "doctors_old_backup_20250905_155713.db"
    ]
    
    for db_file in largest_files:
        db_path = f"c:/AIapps/Doctor/{db_file}"
        if os.path.exists(db_path):
            print(f"\n🔍 DETAILED ANALYSIS: {db_file}")
            get_detailed_doctor_info(db_path)
            break
