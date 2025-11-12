# ✅ Doctor Portal - Contact Request Visibility

## Issue Fixed
Contact requests created when patients click "Contact via WhatsApp" were not showing up in the doctor's portal.

## Root Cause
The doctor portal was only querying for specific statuses (`pending`, `confirmed`, `completed`, `cancelled`) and didn't include the new `contact_request` status.

## Changes Made

### 1. Backend - Include Contact Requests in Queries

**File: `doctor_portal_routes.py`**

Updated all pending count queries to include `contact_request`:

```python
# Before:
WHERE doctor_id = ? AND status = 'pending'

# After:
WHERE doctor_id = ? AND status IN ('pending', 'contact_request')
```

**Locations updated:**
- `get_pending_count()` - Navigation badge count (line 83)
- `doctor_dashboard()` - Dashboard stats (line 272)
- `view_reservations()` - Reservations list badge (line 564)

### 2. Frontend - Display Contact Requests

**File: `templates/doctor/reservations.html`**

#### A. Status Badge
Added `contact_request` to status badge display:

```html
<!-- Before: Only showed pending/confirmed/completed/cancelled -->
<span class="badge bg-{{ 'warning' if reservation.status == 'pending' ... }}">

<!-- After: Added contact_request with primary color -->
<span class="badge bg-{{ 'primary' if reservation.status == 'contact_request' 
                        else 'warning' if reservation.status == 'pending' ... }}">
    {{ '聯絡請求' if reservation.status == 'contact_request' 
       else '待確認' if reservation.status == 'pending' ... }}
</span>
```

**Badge Colors:**
- `contact_request` → Blue (primary)
- `pending` → Yellow (warning)
- `confirmed` → Green (success)
- `completed` → Light blue (info)
- `cancelled` → Red (danger)

#### B. Action Buttons
Added specific actions for contact requests:

```html
{% if reservation.status == 'contact_request' %}
<button class="btn btn-success btn-sm" onclick="confirmReservation({{ reservation.id }})">
    <i class="fas fa-check me-1"></i>確認並安排預約
</button>
<button class="btn btn-outline-secondary btn-sm" onclick="cancelReservation({{ reservation.id }})">
    <i class="fas fa-times me-1"></i>忽略請求
</button>
{% elif reservation.status == 'pending' %}
...
```

**Actions for Contact Requests:**
- ✅ **確認並安排預約** - Confirms and schedules appointment
- ❌ **忽略請求** - Dismisses the contact request

#### C. Filter Button
Added filter button for contact requests:

```html
<button class="btn btn-sm btn-outline-primary" onclick="filterReservations('contact_request')">
    <i class="fas fa-phone me-1"></i>聯絡請求
</button>
```

## How It Works Now

### When Patient Clicks Contact Button:

1. **Creates reservation:**
   ```sql
   INSERT INTO reservations
   - status: 'contact_request'
   - patient symptoms captured
   - confirmation code generated
   ```

2. **Doctor sees in portal:**
   - **Dashboard:** Pending count includes contact requests
   - **Reservations page:** Shows with blue "聯絡請求" badge
   - **Filter:** Can filter by "聯絡請求" status
   - **Actions:** Can confirm or ignore

### Doctor Portal Display

**Reservation Card Example:**

```
┌─────────────────────────────────────────────────────────┐
│ Walk-in Patient                    [聯絡請求] (Blue)    │
│ 📅 2024-11-12  🕐 00:00                                 │
│                                                          │
│ 症狀: 頭痛, 發燒                                         │
│ 長期病患: 高血壓                                         │
│                                                          │
│ [✓ 確認並安排預約]  [✗ 忽略請求]  [💬 聯絡病人]         │
└─────────────────────────────────────────────────────────┘
```

### Dashboard Stats

**Before:**
```
待確認預約: 5
```

**After:**
```
待確認預約: 8  (includes 3 contact requests)
```

### Filter Options

```
[全部] [聯絡請求] [待確認] [已確認] [已完成] [已取消]
  ↑       ↑ NEW
```

## Status Flow

```
contact_request → pending → confirmed → completed
                     ↓
                 cancelled
```

1. **contact_request** - Patient clicked contact button
2. **pending** - Doctor confirmed, awaiting appointment
3. **confirmed** - Appointment scheduled and confirmed
4. **completed** - Consultation finished
5. **cancelled** - Cancelled by doctor/patient

## Benefits

✅ **Full visibility** - Doctors see all contact attempts  
✅ **Easy filtering** - Dedicated filter button  
✅ **Clear actions** - Specific buttons for contact requests  
✅ **Patient context** - Symptoms automatically shown  
✅ **Badge count** - Pending count includes contact requests

## Testing

**Test the complete flow:**

1. **As Patient:**
   - Go to main page
   - Search symptoms: "頭痛"
   - Click "Contact via WhatsApp" on any doctor
   - Console shows: `✅ Reservation request created: ABC12XYZ`

2. **As Doctor:**
   - Login to doctor portal: `/doctor/login`
   - Go to "預約管理" (Reservations)
   - Should see:
     - Blue badge "聯絡請求"
     - Patient symptoms displayed
     - "確認並安排預約" button
     - "忽略請求" button
   - Click filter "聯絡請求" to see only contact requests
   - Dashboard shows increased pending count

3. **Confirm Request:**
   - Click "確認並安排預約"
   - Status changes to `confirmed`
   - Badge changes to green "已確認"

## Files Modified

1. **doctor_portal_routes.py** (3 locations)
   - Line 83: `get_pending_count()` 
   - Line 272: `doctor_dashboard()`
   - Line 564: `view_reservations()`

2. **templates/doctor/reservations.html** (3 sections)
   - Line 166-167: Status badge display
   - Line 171-177: Contact request action buttons
   - Line 90-92: Filter button

---

**Status**: ✅ Contact requests now fully visible in doctor portal!
