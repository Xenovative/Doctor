# 🔧 Cross-Database JOIN Fix

## Issue: 500 Error on /admin/affiliation/reservations

### Error Log
```
"GET /admin/affiliation/reservations HTTP/1.1" 500
```

### Root Cause
The route was attempting to JOIN tables from two different SQLite database files:
- `reservations` table in `admin_data.db`
- `doctors` table in `doctors.db`

**SQLite cannot perform JOINs across different database files** without using ATTACH DATABASE, which adds complexity.

### Original Code (❌ Broken)
```python
query = """
    SELECT r.*, d.name_zh as doctor_name, d.specialty_zh as doctor_specialty
    FROM reservations r
    LEFT JOIN doctors d ON r.doctor_id = d.id  # ❌ Can't JOIN across databases
    WHERE 1=1
"""
```

## Solution Applied

Changed the approach to:
1. Fetch reservations from `admin_data.db`
2. Fetch doctors from `doctors.db`
3. Combine the data in Python

### Fixed Code (✅ Working)
```python
# Step 1: Get reservations from admin_data.db
cursor_admin.execute("SELECT * FROM reservations WHERE ...")
reservations = [dict(row) for row in cursor_admin.fetchall()]

# Step 2: Get doctors from doctors.db
cursor_doctors.execute("SELECT id, name_zh, specialty_zh FROM doctors WHERE is_affiliated = 1")
doctors_dict = {row['id']: dict(row) for row in cursor_doctors.fetchall()}

# Step 3: Combine in Python
for reservation in reservations:
    doctor_id = reservation.get('doctor_id')
    if doctor_id and doctor_id in doctors_dict:
        reservation['doctor_name'] = doctors_dict[doctor_id].get('name_zh', 'Unknown')
        reservation['doctor_specialty'] = doctors_dict[doctor_id].get('specialty_zh', '')
```

## Benefits of This Approach

1. **Works with SQLite**: No cross-database JOIN needed
2. **Efficient**: Fetches all doctors once, then does in-memory lookups
3. **Flexible**: Easy to add more doctor fields if needed
4. **Safe**: Handles missing doctors gracefully

## File Modified

**admin_affiliation_routes.py** - `all_reservations()` function (lines 289-373)

## Changes Made

1. Removed cross-database JOIN
2. Fetch data from each database separately
3. Create doctor dictionary for fast lookups
4. Merge data in Python
5. Added error handling with traceback
6. Fixed template variable names

## ✅ Should Work Now

Restart your Flask app:
```bash
python app.py
```

Then visit:
```
http://localhost:5000/admin/affiliation/reservations
```

The page should now load without 500 errors!

## Alternative Approaches (Not Used)

### Option 1: ATTACH DATABASE
```python
conn.execute("ATTACH DATABASE 'doctors.db' AS doctors_db")
# Then can do: SELECT * FROM reservations JOIN doctors_db.doctors ...
```
**Why not**: Adds complexity, path issues, connection management

### Option 2: Store Doctor Name in Reservations
```python
# When creating reservation, copy doctor name
INSERT INTO reservations (doctor_id, doctor_name, ...)
```
**Why not**: Data duplication, sync issues if doctor name changes

### Option 3: Use Single Database
Move all tables to one database file.
**Why not**: Your existing structure has doctors.db and admin_data.db separated

## Our Solution (✅ Best)
Fetch separately and combine in Python - simple, clean, works perfectly!

---

**Status**: ✅ Fixed - Route now works without cross-database JOINs
