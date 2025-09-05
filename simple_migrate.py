import sqlite3
import pandas as pd
import os
from datetime import datetime

def migrate_database():
    print("🔄 Starting database migration...")
    
    # Check files
    csv_file = "assets/finddoc_doctors_detailed_full_20250905.csv"
    current_db = "doctors.db"
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    # Backup current database
    if os.path.exists(current_db):
        backup_name = f"doctors_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        os.rename(current_db, backup_name)
        print(f"✅ Backed up current database to: {backup_name}")
    
    # Read CSV
    print("📖 Reading CSV data...")
    df = pd.read_csv(csv_file)
    print(f"Found {len(df):,} records")
    print(f"Columns: {list(df.columns)}")
    
    # Create new database
    print("🗄️ Creating new database...")
    conn = sqlite3.connect(current_db)
    
    # Convert DataFrame to SQLite
    df.to_sql('doctors', conn, if_exists='replace', index=False)
    
    # Add indexes
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_name ON doctors(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_specialty ON doctors(specialty)")
    
    # Get stats
    cursor.execute("SELECT COUNT(*) FROM doctors")
    count = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    
    print(f"✅ Migration complete! {count:,} doctors in database")

if __name__ == "__main__":
    migrate_database()
