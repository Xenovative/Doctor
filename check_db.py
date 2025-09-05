import sqlite3
import pandas as pd
import os

# Check what we have
print("📊 DATABASE ANALYSIS")
print("=" * 50)

# Check CSV files
csv_old = "assets/finddoc_doctors_detailed 2.csv"
csv_new = "assets/finddoc_doctors_detailed_full_20250905.csv"

if os.path.exists(csv_old):
    df_old = pd.read_csv(csv_old)
    print(f"📄 Old CSV: {len(df_old):,} records")
    print(f"   Columns: {list(df_old.columns)}")

if os.path.exists(csv_new):
    df_new = pd.read_csv(csv_new)
    print(f"📄 New CSV: {len(df_new):,} records")
    print(f"   Columns: {list(df_new.columns)}")
    print(f"   Sample: {df_new.iloc[0]['name'] if 'name' in df_new.columns else 'No name column'}")

# Check current database
if os.path.exists("doctors.db"):
    conn = sqlite3.connect("doctors.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"🗄️ Current DB tables: {[t[0] for t in tables]}")
    
    if ('doctors',) in tables:
        cursor.execute("SELECT COUNT(*) FROM doctors")
        count = cursor.fetchone()[0]
        print(f"   Doctors: {count:,} records")
    
    conn.close()

# Migration recommendation
print("\n🎯 RECOMMENDATION:")
if os.path.exists(csv_new):
    print(f"Use new CSV ({len(df_new):,} records) to replace current database")
else:
    print("New CSV not found - check file path")
