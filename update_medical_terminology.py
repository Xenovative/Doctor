#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Migration Script: Update Medical Terminology
Updates database column names to use safer, non-medical-advice language

Changes:
- ai_diagnosis -> ai_analysis
- recommended_specialty -> related_specialty  
- diagnosis_report -> analysis_report

This script is safe to run multiple times (idempotent).
"""

import sqlite3
import os
import shutil
from datetime import datetime

def backup_database(db_path):
    """Create a backup of the database before migration"""
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(db_path, backup_path)
        print(f"✅ Created backup: {backup_path}")
        return backup_path
    return None

def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def migrate_user_queries_table(cursor):
    """Migrate user_queries table column names"""
    print("🔄 Migrating user_queries table...")
    
    # Check current column structure
    has_old_ai_diagnosis = column_exists(cursor, 'user_queries', 'ai_diagnosis')
    has_old_recommended = column_exists(cursor, 'user_queries', 'recommended_specialty')
    has_old_diagnosis_report = column_exists(cursor, 'user_queries', 'diagnosis_report')
    
    has_new_ai_analysis = column_exists(cursor, 'user_queries', 'ai_analysis')
    has_new_related = column_exists(cursor, 'user_queries', 'related_specialty')
    has_new_analysis_report = column_exists(cursor, 'user_queries', 'analysis_report')
    
    changes_made = False
    
    # Migrate ai_diagnosis -> ai_analysis
    if has_old_ai_diagnosis and not has_new_ai_analysis:
        print("  📝 Adding ai_analysis column...")
        cursor.execute('ALTER TABLE user_queries ADD COLUMN ai_analysis TEXT')
        print("  📋 Copying data from ai_diagnosis to ai_analysis...")
        cursor.execute('UPDATE user_queries SET ai_analysis = ai_diagnosis WHERE ai_diagnosis IS NOT NULL')
        changes_made = True
    
    # Migrate recommended_specialty -> related_specialty
    if has_old_recommended and not has_new_related:
        print("  📝 Adding related_specialty column...")
        cursor.execute('ALTER TABLE user_queries ADD COLUMN related_specialty TEXT')
        print("  📋 Copying data from recommended_specialty to related_specialty...")
        cursor.execute('UPDATE user_queries SET related_specialty = recommended_specialty WHERE recommended_specialty IS NOT NULL')
        changes_made = True
    
    # Migrate diagnosis_report -> analysis_report
    if has_old_diagnosis_report and not has_new_analysis_report:
        print("  📝 Adding analysis_report column...")
        cursor.execute('ALTER TABLE user_queries ADD COLUMN analysis_report TEXT')
        print("  📋 Copying data from diagnosis_report to analysis_report...")
        cursor.execute('UPDATE user_queries SET analysis_report = diagnosis_report WHERE diagnosis_report IS NOT NULL')
        changes_made = True
    
    if changes_made:
        print("  ✅ user_queries table migration completed")
    else:
        print("  ℹ️  user_queries table already up to date")
    
    return changes_made

def verify_migration(cursor):
    """Verify the migration was successful"""
    print("🔍 Verifying migration...")
    
    # Check new columns exist
    new_columns = ['ai_analysis', 'related_specialty', 'analysis_report']
    missing_columns = []
    
    for column in new_columns:
        if not column_exists(cursor, 'user_queries', column):
            missing_columns.append(column)
    
    if missing_columns:
        print(f"  ❌ Missing columns: {missing_columns}")
        return False
    
    # Check data was copied correctly
    cursor.execute('SELECT COUNT(*) FROM user_queries WHERE ai_analysis IS NOT NULL')
    ai_analysis_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM user_queries WHERE related_specialty IS NOT NULL')
    related_specialty_count = cursor.fetchone()[0]
    
    print(f"  ✅ Records with ai_analysis: {ai_analysis_count}")
    print(f"  ✅ Records with related_specialty: {related_specialty_count}")
    print("  ✅ Migration verification completed")
    
    return True

def main():
    """Main migration function"""
    print("🚀 Starting Medical Terminology Migration")
    print("=" * 50)
    
    db_path = 'admin_data.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    # Create backup
    backup_path = backup_database(db_path)
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Perform migration
        changes_made = migrate_user_queries_table(cursor)
        
        # Commit changes
        if changes_made:
            conn.commit()
            print("💾 Changes committed to database")
        
        # Verify migration
        if verify_migration(cursor):
            print("✅ Migration completed successfully!")
            
            if changes_made:
                print("\n📋 Summary of changes:")
                print("  • ai_diagnosis → ai_analysis")
                print("  • recommended_specialty → related_specialty")
                print("  • diagnosis_report → analysis_report")
                print("\n⚠️  Note: Old columns are preserved for backward compatibility")
                print("   You can safely remove them after confirming everything works correctly.")
            else:
                print("ℹ️  No changes were needed - database already up to date")
            
            return True
        else:
            print("❌ Migration verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if backup_path:
            print(f"💡 You can restore from backup: {backup_path}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    success = main()
    if not success:
        exit(1)
    
    print("\n🎉 Medical terminology migration completed!")
    print("Your application now uses safer, non-medical-advice language.")
