# ✅ Time Slot Selection for Affiliated Doctors

## Feature Overview
When patients click "Contact Us" for **affiliated doctors**, they now see a time slot selection modal before contacting via WhatsApp. The system shows either the doctor's actual availability schedule or default time slots if no schedule is set.

## How It Works

### For Affiliated Doctors:
1. Patient clicks "Contact via WhatsApp"
2. **Time slot modal appears** with available times
3. Patient selects preferred time
4. Reservation created with selected time
5. WhatsApp opens with doctor's contact

### For Non-Affiliated Doctors:
- Works as before (immediate WhatsApp contact)
- No time selection required

## Changes Made

### 1. Backend - New Endpoint

**File: `app.py`** (lines 6632-6744)

Created `/api/doctor/<int:doctor_id>/available-slots-or-default`:

```python
@app.route('/api/doctor/<int:doctor_id>/available-slots-or-default')
def get_available_slots_or_default(doctor_id):
    """Get available time slots for doctor, or default times if no schedule set"""
    
    # Check if doctor has availability schedule
    if schedules:
        # Return actual available slots from doctor_availability table
        # Checks existing reservations to show only available times
        return jsonify({
            'success': True,
            'has_schedule': True,
            'slots': available_slots,
            'date': date
        })
    else:
        # Return default time slots
        default_slots = [
            {'time': '09:00', 'display': '09:00 AM'},
            {'time': '09:30', 'display': '09:30 AM'},
            # ... 14 default slots from 9 AM to 5:30 PM
        ]
        return jsonify({
            'success': True,
            'has_schedule': False,
            'slots': default_slots,
            'date': date,
            'message': '醫生尚未設置時間表，顯示預設時段'
        })
```

**Features:**
- Queries `doctor_availability` table for doctor's schedule
- Checks `reservations` table to exclude booked slots
- Returns default slots if no schedule exists
- Shows available count for each slot

### 2. Backend - Updated Reservation Endpoint

**File: `app.py`** (lines 6547-6638)

Updated `/api/contact-doctor-reservation` to accept date and time:

```python
reservation_date = data.get('reservation_date')  # NEW
reservation_time = data.get('reservation_time')  # NEW

# Insert with selected date/time
cursor.execute("""
    INSERT INTO reservations
    (..., reservation_date, reservation_time, ...)
    VALUES (..., ?, ?, ...)
""", (..., reservation_date, reservation_time, ...))
```

**Before:**
- Always used `date('now')` and `'00:00'`

**After:**
- Uses patient-selected date and time
- Falls back to defaults if not provided

### 3. Frontend - Time Slot Modal

**File: `static/script.js`** (lines 1818-1984)

Added three new functions:

#### A. `showTimeSlotModal()`
```javascript
window.showTimeSlotModal = async function(doctorId, doctorName, doctorSpecialty, doctorPhone) {
    // Fetch available slots from API
    const response = await fetch(`/api/doctor/${doctorId}/available-slots-or-default?date=${dateStr}`);
    
    // Create modal with time slot grid
    modalContent.innerHTML = `
        <div class="time-slot-header">...</div>
        <div class="time-slot-body">
            <div class="doctor-info-section">...</div>
            <div class="time-slots-grid">
                ${data.slots.map(slot => `
                    <button class="time-slot-btn" onclick="selectTimeSlot(...)">
                        ${slot.display}
                    </button>
                `).join('')}
            </div>
        </div>
    `;
};
```

#### B. `selectTimeSlot()`
```javascript
window.selectTimeSlot = async function(time, date, doctorId, doctorName, ...) {
    // Create reservation with selected time
    await fetch('/api/contact-doctor-reservation', {
        body: JSON.stringify({
            doctor_id: doctorId,
            doctor_name: doctorName,
            reservation_date: date,  // Selected date
            reservation_time: time   // Selected time
        })
    });
    
    // Open WhatsApp
    window.open(whatsappUrl, '_blank');
    
    // Close modals
    closeTimeSlotModal();
};
```

#### C. `closeTimeSlotModal()`
```javascript
window.closeTimeSlotModal = function() {
    const modal = document.getElementById('timeSlotModal');
    if (modal) {
        modal.style.display = 'none';
    }
};
```

### 4. Frontend - Updated Contact Flow

**File: `static/script.js`** (lines 1305-1314)

```javascript
window.contactDoctor = async function(event, doctorId, doctorName, ..., isAffiliated) {
    // For affiliated doctors, show time slot selection modal first
    if (isAffiliated) {
        showTimeSlotModal(doctorId, doctorName, doctorSpecialty, doctorPhone);
        return;
    }
    
    // For non-affiliated doctors, proceed with immediate contact
    // ... existing code ...
};
```

### 5. Frontend - CSS Styling

**File: `static/style.css`** (lines 3430-3687)

Added comprehensive styling:
- `.time-slot-modal` - Modal overlay
- `.time-slot-modal-content` - Modal container
- `.time-slot-header` - Purple gradient header
- `.time-slots-grid` - Responsive grid layout
- `.time-slot-btn` - Individual time slot buttons
- `.doctor-info-section` - Doctor information display
- `.info-message` - Warning for default slots
- Mobile responsive styles

## User Experience

### Scenario 1: Doctor with Schedule

**Patient clicks "Contact Us" on affiliated doctor:**

```
┌─────────────────────────────────────────────┐
│ 選擇預約時間                            [×] │
├─────────────────────────────────────────────┤
│ 👨‍⚕️ 陳海聰醫生                              │
│ 🩺 內科                                      │
│                                              │
│ 📅 日期: 2024-11-13                         │
│                                              │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐       │
│ │ 🕐   │ │ 🕐   │ │ 🕐   │ │ 🕐   │       │
│ │09:00 │ │09:30 │ │10:00 │ │10:30 │       │
│ │(2可用)│ │(1可用)│ │(3可用)│ │(2可用)│       │
│ └──────┘ └──────┘ └──────┘ └──────┘       │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐       │
│ │ 🕐   │ │ 🕐   │ │ 🕐   │ │ 🕐   │       │
│ │14:00 │ │14:30 │ │15:00 │ │15:30 │       │
│ └──────┘ └──────┘ └──────┘ └──────┘       │
│                                              │
│                              [取消]          │
└─────────────────────────────────────────────┘
```

### Scenario 2: Doctor without Schedule

**Shows default time slots with info message:**

```
┌─────────────────────────────────────────────┐
│ Select Appointment Time                 [×] │
├─────────────────────────────────────────────┤
│ 👨‍⚕️ Dr. Chan                                │
│ 🩺 Internal Medicine                         │
│                                              │
│ ⚠️ Doctor has not set schedule.             │
│    Showing default time slots.              │
│                                              │
│ 📅 Date: 2024-11-13                         │
│                                              │
│ [09:00 AM] [09:30 AM] [10:00 AM] [10:30 AM]│
│ [11:00 AM] [11:30 AM] [02:00 PM] [02:30 PM]│
│ [03:00 PM] [03:30 PM] [04:00 PM] [04:30 PM]│
│ [05:00 PM] [05:30 PM]                       │
│                                              │
│                              [Cancel]        │
└─────────────────────────────────────────────┘
```

## Default Time Slots

When doctor has no schedule, system shows:

**Morning Slots:**
- 09:00 AM
- 09:30 AM
- 10:00 AM
- 10:30 AM
- 11:00 AM
- 11:30 AM

**Afternoon Slots:**
- 02:00 PM
- 02:30 PM
- 03:00 PM
- 03:30 PM
- 04:00 PM
- 04:30 PM
- 05:00 PM
- 05:30 PM

**Total: 14 default slots**

## Database Records

### With Selected Time:

```sql
INSERT INTO reservations
- doctor_id: 123
- reservation_date: '2024-11-13'  ← Selected date
- reservation_time: '10:00'       ← Selected time
- status: 'contact_request'
- notes: 'Patient selected time slot via contact button'
```

### Without Selected Time (non-affiliated):

```sql
INSERT INTO reservations
- doctor_id: 456
- reservation_date: date('now')
- reservation_time: '00:00'
- status: 'contact_request'
- notes: 'Patient clicked contact button - awaiting response'
```

## Benefits

✅ **Better scheduling** - Patients select specific times  
✅ **Reduced conflicts** - Shows only available slots  
✅ **Flexible fallback** - Default slots if no schedule  
✅ **Doctor visibility** - Doctors see preferred times  
✅ **Professional UX** - Modern, intuitive interface  
✅ **Mobile friendly** - Responsive grid layout  
✅ **Bilingual** - English and Chinese support

## Testing

**Test the complete flow:**

1. **Restart the app**

2. **As Patient:**
   - Go to main page
   - Search for symptoms
   - Find an affiliated doctor
   - Click "Contact via WhatsApp"
   - **Should see:** Time slot selection modal
   - Select a time slot
   - **Should see:** WhatsApp opens
   - Console: `✅ Reservation created with time: ABC12XYZ`

3. **As Doctor:**
   - Login to doctor portal
   - Go to "預約管理"
   - **Should see:** Reservation with selected time
   - Status: "聯絡請求"
   - Date and time: Patient's selection

4. **Test Default Slots:**
   - Find a doctor without availability schedule
   - Click "Contact via WhatsApp"
   - **Should see:** Yellow info message
   - **Should see:** 14 default time slots
   - Select any slot
   - **Should work:** Creates reservation

## Files Modified

1. **app.py**
   - Lines 6632-6744: New endpoint `/api/doctor/<int:doctor_id>/available-slots-or-default`
   - Lines 6547-6638: Updated `/api/contact-doctor-reservation` to accept date/time

2. **static/script.js**
   - Lines 1305-1314: Updated `contactDoctor()` to check affiliation
   - Lines 1818-1984: Added time slot modal functions

3. **static/style.css**
   - Lines 3430-3687: Added time slot modal styling

## API Endpoints

### GET `/api/doctor/<doctor_id>/available-slots-or-default`

**Query Parameters:**
- `date` (optional): Date in YYYY-MM-DD format (defaults to tomorrow)

**Response:**
```json
{
    "success": true,
    "has_schedule": true,
    "slots": [
        {
            "time": "09:00",
            "display": "09:00 AM",
            "available": 2
        }
    ],
    "date": "2024-11-13",
    "message": "醫生尚未設置時間表，顯示預設時段"
}
```

### POST `/api/contact-doctor-reservation`

**Request Body:**
```json
{
    "doctor_id": 123,
    "doctor_name": "陳海聰醫生",
    "reservation_date": "2024-11-13",
    "reservation_time": "10:00"
}
```

**Response:**
```json
{
    "success": true,
    "reservation_id": 456,
    "confirmation_code": "ABC12XYZ",
    "message": "已記錄聯絡請求"
}
```

---

**Status**: ✅ Time slot selection feature fully implemented for affiliated doctors!
