# ✅ Affiliation Badge Added to Table Listing

## What Was Added

A green **"✓ 已加盟"** badge now appears next to the doctor's name in the main table listing.

## Visual Display

### In Table View:
```
姓名                    專科        資格
陳鴻壽醫生 [✓ 已加盟]   Dentist    香港大學牙醫學士
陳河醫藍生              普通科醫生  香港中文大學內外全科醫學士
陳河醫中醫師 [✓ 已加盟]  中醫師     香港醫管理局註冊中醫師
```

## Implementation

### Frontend (templates/admin/doctors.html)

Added badge next to doctor name in table cell:
```html
<strong>{{ doctor.name_zh }}</strong>
{% if doctor.is_affiliated %}
<span class="badge bg-success ms-1" style="font-size: 0.7rem;">
    <i class="fas fa-check-circle me-1"></i>已加盟
</span>
{% endif %}
```

**Features:**
- Small font size (0.7rem) - doesn't overwhelm the name
- Green color (`bg-success`) - positive indicator
- Check circle icon - clear visual
- Margin left (ms-1) - proper spacing

### Backend (app.py)

Updated `admin_doctors_paginated()` query to include `is_affiliated`:
```python
COALESCE(is_affiliated, 0) as is_affiliated
```

## Badge Appears When:
- ✅ Doctor has a login account (`doctor_accounts` table entry)
- ✅ `is_affiliated = 1` in doctors table
- ✅ Affiliation status is 'approved'

## Badge Hidden When:
- ❌ Doctor has no account
- ❌ `is_affiliated = 0` or NULL
- ❌ Not yet affiliated

## Locations Where Badge Appears

### 1. Table Listing (Main View)
- Shows in doctor name column
- Visible in all rows
- Updates when page refreshes

### 2. Edit Modal Header
- Shows next to "編輯醫生資料" title
- Updates when modal opens
- Synced with create account button

## Benefits

1. **Quick Identification**: Instantly see which doctors are affiliated
2. **Visual Consistency**: Same badge style in table and modal
3. **Professional Look**: Clean, modern design
4. **Clear Status**: No confusion about affiliation status
5. **Scalable**: Works with any number of doctors

## Files Modified

1. **templates/admin/doctors.html**
   - Added badge to table name cell (lines 345-348, 355-358, 362-365)
   
2. **app.py**
   - Added `is_affiliated` to SELECT query (line 5789)

## Testing

1. Go to `/admin/doctors`
2. Look at doctor names in table
3. Doctors with accounts should show green "✓ 已加盟" badge
4. Doctors without accounts should have no badge
5. Click "編輯" on affiliated doctor - badge appears in modal too

## Design Consistency

**Badge Styling:**
- Font size: 0.7rem (smaller than name)
- Color: Green (#198754)
- Icon: Check circle
- Spacing: 4px left margin
- Display: Inline with name

**Matches:**
- Modal header badge
- Specialty badges
- Status indicators throughout admin panel

---

**Status**: ✅ Badge now appears in both table listing and edit modal!

**Restart app to see badges**: Affiliated doctors will show the green badge next to their names.
