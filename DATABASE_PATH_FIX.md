# 🔧 Database Path Fix Applied

## Issue: "no such table" Error Despite Tables Existing

### Problem
The database tables exist (verified by `check_and_migrate.py`), but the Flask app was still getting "no such table" errors.

### Root Cause
The blueprint files were using **relative paths** (`'doctors.db'`) to connect to databases. When Flask runs, it uses the current working directory, which might be different from where the database files are located.

**Example of the problem:**
```python
# ❌ This looks for doctors.db in the CURRENT WORKING DIRECTORY
conn = sqlite3.connect('doctors.db')
```

If you run Flask from a different directory (e.g., `/root/Doctor/` vs `/root/`), it will look for the database in the wrong place and create a new empty database file there.

## Solution Applied

Changed all three blueprint files to use **absolute paths**:

### Files Modified

#### 1. admin_affiliation_routes.py (Lines 13-20)
```python
import os

# Get absolute path to database files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCTORS_DB = os.path.join(BASE_DIR, 'doctors.db')
ADMIN_DB = os.path.join(BASE_DIR, 'admin_data.db')

def get_doctor_db():
    conn = sqlite3.connect(DOCTORS_DB)  # ✅ Uses absolute path
    conn.row_factory = sqlite3.Row
    return conn
```

#### 2. doctor_portal_routes.py (Lines 17-24)
```python
import os

# Get absolute path to database files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCTORS_DB = os.path.join(BASE_DIR, 'doctors.db')
ADMIN_DB = os.path.join(BASE_DIR, 'admin_data.db')
```

#### 3. reservation_routes.py (Lines 11-18)
```python
import os

# Get absolute path to database files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCTORS_DB = os.path.join(BASE_DIR, 'doctors.db')
ADMIN_DB = os.path.join(BASE_DIR, 'admin_data.db')
```

## How It Works

1. `__file__` - Gets the absolute path of the current Python file
2. `os.path.dirname()` - Gets the directory containing that file
3. `os.path.join()` - Joins the directory with the database filename

**Result**: Always connects to the database in the same directory as the blueprint file, regardless of where Flask is run from.

## ✅ Should Work Now

Restart your Flask app:
```bash
python app.py
```

The routes should now correctly find the database files:
- `/admin/affiliation/requests` ✅
- `/admin/affiliation/all-reservations` ✅
- `/admin/affiliation/doctor-accounts` ✅
- `/doctor/login` ✅

## Why This Happens

Common scenarios that cause this issue:
1. Running Flask from a parent directory: `python Doctor/app.py`
2. Using systemd/supervisor with different working directory
3. Running via IDE with different project root
4. Docker containers with mounted volumes

## Verification

To verify the fix is working, check the Flask console logs. You should see:
```
✅ Doctor affiliation system blueprints registered successfully
```

And no database errors when accessing the routes.

---

**Status**: ✅ Fixed - All blueprint files now use absolute database paths
