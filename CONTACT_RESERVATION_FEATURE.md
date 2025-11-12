# ✅ Contact Button Creates Reservation Request

## Feature Overview
When a patient clicks the "Contact via WhatsApp" button, the system now **automatically creates a reservation request** in the database while opening WhatsApp. This allows doctors and admins to track all contact attempts.

## How It Works

### 1. Backend - New API Endpoint

**File: `app.py` - `/api/contact-doctor-reservation`**

Creates a reservation record with special status `contact_request`:

```python
@app.route('/api/contact-doctor-reservation', methods=['POST'])
def contact_doctor_reservation():
    """Create a reservation request when contact button is clicked"""
    
    # Get patient info from session (if available from symptom search)
    query_id = session.get('last_query_id')
    
    # Create reservation with status 'contact_request'
    cursor.execute("""
        INSERT INTO reservations
        (doctor_id, patient_name, patient_phone, patient_age, 
         patient_gender, reservation_date, reservation_time, consultation_type,
         symptoms, chronic_conditions, query_id, confirmation_code, status, notes)
        VALUES (?, ?, ?, ?, ?, date('now'), '00:00', 'contact', ?, ?, ?, ?, 'contact_request', 
                'Patient clicked contact button - awaiting response')
    """)
    
    # Add to history
    cursor.execute("""
        INSERT INTO reservation_history
        (reservation_id, action, new_status, performed_by, performed_by_type, notes)
        VALUES (?, 'contact_initiated', 'contact_request', ?, 'patient', 'Contact button clicked')
    """)
```

**Returns:**
```json
{
    "success": true,
    "reservation_id": 123,
    "confirmation_code": "ABC12XYZ",
    "message": "已記錄聯絡請求"
}
```

### 2. Frontend - Parallel Requests

**File: `static/script.js` - `contactDoctor()` function**

Updated to make **two parallel API calls**:

```javascript
window.contactDoctor = async function(event, doctorId, doctorName, doctorSpecialty, doctorPhone, isAffiliated) {
    
    // 1. Create reservation request
    const reservationPromise = fetch('/api/contact-doctor-reservation', {
        method: 'POST',
        body: JSON.stringify({
            doctor_id: doctorId,
            doctor_name: doctorName
        })
    });
    
    // 2. Get WhatsApp URL
    const whatsappPromise = fetch('/get_whatsapp_url', {
        method: 'POST',
        body: JSON.stringify({
            doctor_name: doctorName,
            doctor_specialty: doctorSpecialty,
            doctor_phone: doctorPhone,
            is_affiliated: isAffiliated
        })
    });
    
    // Wait for both (parallel execution)
    const [reservationResponse, whatsappResponse] = await Promise.all([
        reservationPromise, 
        whatsappPromise
    ]);
    
    // Handle reservation
    if (reservationResponse.ok) {
        const data = await reservationResponse.json();
        console.log('✅ Reservation created:', data.confirmation_code);
    }
    
    // Open WhatsApp
    window.open(whatsappUrl, '_blank');
}
```

**Updated button onclick:**
```javascript
// Before: contactDoctor(event, name, specialty, phone, isAffiliated)
// After:  contactDoctor(event, doctorId, name, specialty, phone, isAffiliated)

onclick="contactDoctor(event, ${doctor.id}, '${doctor.name}', ...)"
```

## Database Records

### Reservations Table

When contact button is clicked, creates record:

| Field | Value | Notes |
|-------|-------|-------|
| `doctor_id` | 123 | Doctor being contacted |
| `patient_name` | "Walk-in Patient" | Default if no search done |
| `patient_age` | 35 | From symptom search (if available) |
| `patient_gender` | "Male" | From symptom search (if available) |
| `symptoms` | "頭痛, 發燒" | From symptom search (if available) |
| `chronic_conditions` | "高血壓" | From symptom search (if available) |
| `reservation_date` | 2024-11-12 | Today's date |
| `reservation_time` | "00:00" | Placeholder (not scheduled yet) |
| `consultation_type` | "contact" | Special type for contact requests |
| `status` | **"contact_request"** | Special status |
| `confirmation_code` | "ABC12XYZ" | Unique tracking code |
| `notes` | "Patient clicked contact button - awaiting response" | |
| `query_id` | 456 | Links to original symptom search |

### Reservation History Table

| Field | Value |
|-------|-------|
| `reservation_id` | 123 |
| `action` | "contact_initiated" |
| `new_status` | "contact_request" |
| `performed_by` | "Walk-in Patient" |
| `performed_by_type` | "patient" |
| `notes` | "Contact button clicked" |

## Benefits

### 1. **Complete Tracking**
Every contact attempt is logged with:
- Which doctor was contacted
- Patient symptoms (if available)
- Timestamp
- Unique confirmation code

### 2. **Doctor Portal Integration**
Doctors can see contact requests in their portal:
- View all contact attempts
- See patient symptoms
- Follow up appropriately

### 3. **Admin Visibility**
Admins can track:
- Which doctors are being contacted most
- Conversion from search to contact
- Patient engagement metrics

### 4. **Patient Context**
If patient searched symptoms first:
- Symptoms automatically included
- Age/gender captured
- Links back to original diagnosis

### 5. **Non-Blocking**
Reservation creation happens in parallel:
- WhatsApp opens immediately
- No delay for user
- Fails gracefully if reservation fails

## Example Flow

### Scenario: Patient with Headache

1. **Patient searches symptoms:**
   ```
   Age: 35
   Symptoms: "頭痛, 發燒"
   → Creates query_id: 456
   ```

2. **System recommends doctors:**
   ```
   陳海聰醫生 (內科)
   ```

3. **Patient clicks "Contact via WhatsApp":**
   
   **Backend creates:**
   ```sql
   INSERT INTO reservations
   (doctor_id=123, patient_age=35, symptoms='頭痛, 發燒', 
    status='contact_request', query_id=456, ...)
   ```
   
   **Frontend opens:**
   ```
   https://wa.me/85291234567?text=...
   ```

4. **Console shows:**
   ```
   Contact doctor: {doctorId: 123, doctorName: "陳海聰醫生", ...}
   ✅ Reservation request created: ABC12XYZ
   Opening WhatsApp URL: https://wa.me/85291234567
   ```

5. **Doctor portal shows:**
   ```
   New Contact Request
   Patient: Walk-in Patient (Age: 35)
   Symptoms: 頭痛, 發燒
   Code: ABC12XYZ
   Status: contact_request
   ```

## Status Types

| Status | Meaning | When Used |
|--------|---------|-----------|
| `contact_request` | Patient clicked contact button | Initial state |
| `pending` | Formal reservation made | After scheduling |
| `confirmed` | Doctor confirmed appointment | Doctor action |
| `completed` | Consultation finished | After visit |
| `cancelled` | Cancelled by patient/doctor | Cancellation |

## Admin View

Admins can filter reservations by status:
- View all `contact_request` entries
- See which doctors get most contacts
- Track conversion to actual appointments
- Follow up on unresponded contacts

## Testing

**Test the feature:**

1. Go to main page
2. Search for symptoms (e.g., "頭痛")
3. Click "Contact via WhatsApp" on any doctor
4. Open browser console (F12)
5. Should see:
   ```
   Contact doctor: {doctorId: 123, ...}
   ✅ Reservation request created: ABC12XYZ
   Opening WhatsApp URL: ...
   ```
6. Check database:
   ```sql
   SELECT * FROM reservations 
   WHERE status = 'contact_request' 
   ORDER BY created_at DESC LIMIT 1;
   ```
7. Should see new record with today's date

## Files Modified

1. **app.py** (lines 6540-6630)
   - Added `/api/contact-doctor-reservation` endpoint
   - Creates reservation with `contact_request` status
   - Captures patient info from session

2. **static/script.js** (lines 1136, 1263, 1305-1384)
   - Updated `contactDoctor()` signature to accept `doctorId`
   - Added parallel reservation request
   - Updated button onclick calls

---

**Status**: ✅ Contact button now creates reservation requests in the database!
