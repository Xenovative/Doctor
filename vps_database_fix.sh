#!/bin/bash

# VPS Database Fix Script for Doctor AI System
# This script fixes doctor names being stored in specialty fields and sets NULL specialties to General Practitioner

set -e  # Exit on any error

echo "=== Doctor Database Fix Script for VPS ==="
echo "Starting database cleanup at $(date)"

# Check if we're in the correct directory
if [ ! -f "doctors.db" ]; then
    echo "Error: doctors.db not found in current directory"
    echo "Please run this script from your Doctor AI application directory"
    exit 1
fi

# Backup the database first
BACKUP_FILE="doctors.db.backup_$(date +%Y%m%d_%H%M%S)"
echo "Creating backup: $BACKUP_FILE"
cp doctors.db "$BACKUP_FILE"

# Check how many records need fixing
PROBLEMATIC_COUNT=$(sqlite3 doctors.db "SELECT COUNT(*) FROM doctors WHERE specialty LIKE 'Dr.%' OR specialty_zh LIKE 'Dr.%' OR specialty_en LIKE 'Dr.%';")
NULL_SPECIALTY_COUNT=$(sqlite3 doctors.db "SELECT COUNT(*) FROM doctors WHERE specialty IS NULL OR specialty = '' OR TRIM(specialty) = '' OR specialty_zh IS NULL OR specialty_zh = '' OR TRIM(specialty_zh) = '';")

echo "Found $PROBLEMATIC_COUNT records with doctor names in specialty fields"
echo "Found $NULL_SPECIALTY_COUNT records with NULL/empty specialties"

if [ "$PROBLEMATIC_COUNT" -eq 0 ] && [ "$NULL_SPECIALTY_COUNT" -eq 0 ]; then
    echo "No issues found in database. Exiting."
    exit 0
fi

# Fix 1: Clear doctor names from specialty fields
echo "Step 1: Clearing doctor names from specialty fields..."
sqlite3 doctors.db << 'EOF'
UPDATE doctors 
SET specialty = CASE 
    WHEN specialty LIKE 'Dr.%' THEN NULL 
    ELSE specialty 
END,
specialty_zh = CASE 
    WHEN specialty_zh LIKE 'Dr.%' THEN NULL 
    ELSE specialty_zh 
END,
specialty_en = CASE 
    WHEN specialty_en LIKE 'Dr.%' THEN NULL 
    ELSE specialty_en 
END
WHERE specialty LIKE 'Dr.%' OR specialty_zh LIKE 'Dr.%' OR specialty_en LIKE 'Dr.%';
EOF

# Fix 2: Infer specialties from name patterns
echo "Step 2: Inferring specialties from name patterns..."
sqlite3 doctors.db << 'EOF'
UPDATE doctors 
SET specialty_zh = '泌尿外科', specialty_en = 'Urology', specialty = '泌尿外科'
WHERE (specialty IS NULL OR specialty = '') 
AND (name_zh LIKE '%泌尿外科%' OR name LIKE '%泌尿外科%');

UPDATE doctors 
SET specialty_zh = '物理治療', specialty_en = 'Physiotherapy', specialty = '物理治療'
WHERE (specialty IS NULL OR specialty = '') 
AND (name_zh LIKE '%物理治療師%' OR name LIKE '%物理治療師%');

UPDATE doctors 
SET specialty_zh = '心理學', specialty_en = 'Psychology', specialty = '心理學'
WHERE (specialty IS NULL OR specialty = '') 
AND (name_zh LIKE '%心理學家%' OR name LIKE '%心理學家%');

UPDATE doctors 
SET specialty_zh = '營養學', specialty_en = 'Nutrition', specialty = '營養學'
WHERE (specialty IS NULL OR specialty = '') 
AND (name_zh LIKE '%營養師%' OR name LIKE '%營養師%');

UPDATE doctors 
SET specialty_zh = '牙科', specialty_en = 'Dentistry', specialty = '牙科'
WHERE (specialty IS NULL OR specialty = '') 
AND (name_zh LIKE '%牙醫%' OR name LIKE '%牙醫%');

UPDATE doctors 
SET specialty_zh = '中醫', specialty_en = 'Traditional Chinese Medicine', specialty = '中醫'
WHERE (specialty IS NULL OR specialty = '') 
AND (name_zh LIKE '%中醫%' OR name LIKE '%中醫%');
EOF

# Fix 3: Set remaining NULL specialties to General Practitioner
echo "Step 3: Setting NULL specialties to General Practitioner..."
sqlite3 doctors.db << 'EOF'
UPDATE doctors 
SET specialty = '全科醫生', specialty_zh = '全科醫生', specialty_en = 'General Practitioner' 
WHERE specialty IS NULL OR specialty = '' OR TRIM(specialty) = '';

UPDATE doctors 
SET specialty_zh = '全科醫生', specialty_en = 'General Practitioner' 
WHERE specialty_zh IS NULL OR specialty_zh = '' OR TRIM(specialty_zh) = '';
EOF

# Verify the fixes
FIXED_COUNT=$(sqlite3 doctors.db "SELECT COUNT(*) FROM doctors WHERE specialty = '全科醫生';")
REMAINING_ISSUES=$(sqlite3 doctors.db "SELECT COUNT(*) FROM doctors WHERE specialty LIKE 'Dr.%' OR specialty_zh LIKE 'Dr.%' OR specialty_en LIKE 'Dr.%';")
NULL_COUNT=$(sqlite3 doctors.db "SELECT COUNT(*) FROM doctors WHERE specialty IS NULL OR specialty = '' OR specialty_zh IS NULL OR specialty_zh = '';")

echo ""
echo "=== Fix Results ==="
echo "Records set to General Practitioner: $FIXED_COUNT"
echo "Remaining problematic records: $REMAINING_ISSUES"
echo "Remaining NULL records: $NULL_COUNT"

if [ "$REMAINING_ISSUES" -eq 0 ] && [ "$NULL_COUNT" -eq 0 ]; then
    echo "✅ Database cleanup completed successfully!"
else
    echo "⚠️  Some issues may remain. Please check manually."
fi

echo ""
echo "Backup created: $BACKUP_FILE"
echo "Database fix completed at $(date)"

# Optional: Restart the application (uncomment if using PM2)
# echo "Restarting application..."
# pm2 restart doctor-ai

echo "=== Script completed ==="
