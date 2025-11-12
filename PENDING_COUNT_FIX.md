# 🔧 Pending Count Fix

## Issue: UndefinedError in Base Template

### Error
```
jinja2.exceptions.UndefinedError: 'pending_count' is undefined
File "/root/Doctor/templates/doctor/base.html", line 334
```

### Root Cause
The `doctor/base.html` template uses `pending_count` in the navigation sidebar to show a badge:

```html
{% if pending_count > 0 %}
<span class="badge bg-warning ms-2">{{ pending_count }}</span>
{% endif %}
```

But the routes weren't passing this variable to the template context.

## Solution Applied

### 1. Created Helper Function
Added a reusable function to get pending count:

```python
def get_pending_count(doctor_id: int) -> int:
    """Get count of pending reservations for navigation badge"""
    try:
        conn = get_admin_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count FROM reservations
            WHERE doctor_id = ? AND status = 'pending'
        """, (doctor_id,))
        result = cursor.fetchone()
        conn.close()
        return result['count'] if result else 0
    except:
        return 0
```

### 2. Updated All Routes
Added `pending_count` to all routes that use `doctor/base.html`:

#### Routes Fixed:
1. ✅ `/doctor/dashboard` - Already had it
2. ✅ `/doctor/profile` - Added
3. ✅ `/doctor/availability` - Added
4. ✅ `/doctor/reservations` - Added
5. ✅ `/doctor/reviews` - Added
6. ✅ `/doctor/statistics` - Added

### Example Fix:
**Before:**
```python
return render_template('doctor/profile.html', doctor=doctor_info)
```

**After:**
```python
pending_count = get_pending_count(doctor_id)
return render_template('doctor/profile.html', 
                     doctor=doctor_info, 
                     pending_count=pending_count)
```

## Why This Matters

The navigation sidebar shows a badge with the number of pending reservations:

```
預約管理 [3]  ← Shows pending count
```

This helps doctors see at a glance how many reservations need their attention.

## File Modified

**doctor_portal_routes.py**
- Added `get_pending_count()` helper function (lines 76-89)
- Updated 5 routes to include `pending_count` in template context

## ✅ Should Work Now

Restart your Flask app:
```bash
python app.py
```

All doctor portal pages should now load without the UndefinedError!

## Benefits

1. **Consistent Navigation**: Badge shows on all pages
2. **Real-time Updates**: Count is fetched fresh on each page load
3. **Error Handling**: Returns 0 if database query fails
4. **Reusable**: Single function used by all routes

---

**Status**: ✅ Fixed - All doctor portal routes now pass `pending_count` to templates
