# ⚠️ Database Setup Required

## Error: "no such table: doctors"

This error means the affiliation system database tables haven't been created yet.

## Quick Fix (Choose One)

### Option 1: Run Setup Script (Recommended)
Creates tables + test data:
```bash
python setup_affiliation_system.py
```

This will:
- ✅ Create all 8 required tables
- ✅ Add test doctor account (username: `testdoctor`, password: `test123`)
- ✅ Set up sample availability
- ✅ Create test reservation

### Option 2: Run Migration Only
Creates tables without test data:
```bash
python create_affiliation_system.py
```

This will:
- ✅ Create all 8 required tables
- ✅ Add affiliation columns to existing doctors table
- ❌ No test data

### Option 3: Check First
Check what's missing:
```bash
python check_and_migrate.py
```

## Required Tables

### In doctors.db:
1. `doctor_accounts` - Doctor login credentials
2. `doctor_availability` - Weekly schedules
3. `doctor_time_off` - Holidays/exceptions
4. `doctor_notifications` - In-app notifications

### In admin_data.db:
5. `reservations` - Patient bookings
6. `reservation_history` - Audit trail
7. `doctor_reviews` - Ratings and feedback

### Modified:
8. `doctors` table - Added affiliation columns

## Why This Happened

The affiliation system needs new database tables that don't exist in your current database. The blueprint routes are trying to query these tables, causing the error.

## After Running Setup

You should see:
```
✅ Database migration completed successfully!
✅ Test doctor account created
✅ Sample availability created
✅ Test reservation created

Test Doctor Credentials:
Username: testdoctor
Password: test123
```

Then restart your app:
```bash
python app.py
```

## Verify Setup

After migration, check tables exist:
```bash
python check_and_migrate.py
```

Should show:
```
✅ Table exists: doctor_accounts
✅ Table exists: doctor_availability
✅ Table exists: doctor_time_off
✅ Table exists: doctor_notifications
✅ Table exists: reservations
✅ Table exists: reservation_history
✅ Table exists: doctor_reviews
```

## Routes Will Work After Setup

Once tables are created, these routes will work:
- `/doctor/login` - Doctor portal login
- `/admin/affiliation/requests` - Manage affiliations
- `/admin/affiliation/all-reservations` - View reservations
- `/admin/affiliation/doctor-accounts` - Manage accounts
- `/admin/affiliation/statistics` - View stats

## Troubleshooting

### If setup script fails:
1. Check Python version (needs 3.8-3.11)
2. Check file permissions
3. Make sure databases aren't locked by another process
4. Try running migration only: `python create_affiliation_system.py`

### If tables already exist:
The scripts are safe to run multiple times - they check for existing tables before creating.

---

**Bottom line**: Run `python setup_affiliation_system.py` to create the database tables!
