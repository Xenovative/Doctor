# ✅ Contact Button Fix - Use Doctor's Account Phone

## Issue
The "Contact via WhatsApp" button was always using the hardcoded fallback number (85294974070) instead of the affiliated doctor's personal account phone number.

## Root Cause
1. Doctor data loaded from database didn't include `account_phone`
2. Frontend was passing `doctor.phone` (which didn't exist) instead of `doctor.account_phone`
3. Fallback logic always triggered because phone was empty

## Complete Fix

### 1. Backend - Load Account Phone

**File: `app.py` - `load_doctors_data()` function**

Added LEFT JOIN with `doctor_accounts` table:

```python
SELECT 
    d.id,
    ...
    COALESCE(d.is_affiliated, 0) as is_affiliated,
    da.phone as account_phone,  -- NEW: Account phone from doctor_accounts
    d.contact_numbers
FROM doctors d
LEFT JOIN doctor_accounts da ON d.id = da.doctor_id AND da.is_active = 1
```

Now every doctor object includes:
- `is_affiliated`: Boolean flag
- `account_phone`: Personal phone from their account (null if not affiliated)
- `contact_numbers`: Clinic phone numbers

### 2. Frontend - Pass Correct Phone

**File: `static/script.js`**

Updated contact button calls to pass the right phone number:

```javascript
// Doctor card button
onclick="contactDoctor(event, '${doctor.name}', '${doctor.specialty}', 
    '${doctor.account_phone || doctor.contact_numbers || ''}', 
    ${doctor.is_affiliated || false})"

// Modal button
onclick="contactDoctor(event, '${doctorName}', '${doctorSpecialty}', 
    '${doctor.account_phone || doctor.contact_numbers || ''}', 
    ${doctor.is_affiliated || false})"
```

Logic:
- **Affiliated doctors**: Use `account_phone` (personal number)
- **Non-affiliated**: Use `contact_numbers` (clinic number)
- **Fallback**: Empty string if neither exists

### 3. Frontend - Smart Fallback Logic

**File: `static/script.js` - `contactDoctor()` function**

Updated function signature and fallback logic:

```javascript
window.contactDoctor = async function(event, doctorName, doctorSpecialty, doctorPhone = '', isAffiliated = false) {
    // ... API call to /get_whatsapp_url ...
    
    if (data.success && data.whatsapp_url) {
        // Use backend-generated URL
        window.open(data.whatsapp_url, '_blank');
    } else {
        // Smart fallback based on affiliation
        if (isAffiliated && doctorPhone) {
            // For affiliated doctors, use their phone directly
            const cleanPhone = doctorPhone.replace(/[^0-9+]/g, '');
            const fallbackUrl = `https://wa.me/${cleanPhone}`;
            window.open(fallbackUrl, '_blank');
        } else {
            // For non-affiliated, use admin number
            const fallbackUrl = 'https://wa.me/85294974070';
            window.open(fallbackUrl, '_blank');
        }
    }
}
```

## How It Works Now

### For Affiliated Doctors (陳海聰醫生):

1. **Data loaded**: 
   ```json
   {
       "name": "陳海聰醫生",
       "is_affiliated": 1,
       "account_phone": "+852 9123 4567",
       "contact_numbers": "85223977731"
   }
   ```

2. **Button onclick**: 
   ```javascript
   contactDoctor(event, "陳海聰醫生", "內科", "+852 9123 4567", true)
   ```

3. **WhatsApp URL**: 
   ```
   https://wa.me/85291234567
   ```
   ✅ Opens WhatsApp with doctor's **personal account phone**

### For Non-Affiliated Doctors:

1. **Data loaded**:
   ```json
   {
       "name": "Dr. Smith",
       "is_affiliated": 0,
       "account_phone": null,
       "contact_numbers": "85223456789"
   }
   ```

2. **Button onclick**:
   ```javascript
   contactDoctor(event, "Dr. Smith", "General", "85223456789", false)
   ```

3. **WhatsApp URL**:
   ```
   https://wa.me/85294974070
   ```
   ✅ Falls back to **admin number** (as intended)

## Benefits

1. **Affiliated Doctors**: Direct contact via their personal WhatsApp
2. **Non-Affiliated**: Contact goes to admin for coordination
3. **Smart Fallback**: Even if API fails, affiliated doctors still get direct contact
4. **Consistent**: Works in both doctor cards and detail modal
5. **Debugging**: Console logs show exactly what's being passed

## Files Modified

1. **app.py** (line 1055-1085)
   - Updated `load_doctors_data()` query
   - Added LEFT JOIN with `doctor_accounts`
   - Included `is_affiliated` and `account_phone` fields

2. **static/script.js** (lines 1136, 1263, 1305-1362)
   - Updated contact button onclick calls
   - Modified `contactDoctor()` function signature
   - Added smart fallback logic based on affiliation

## Testing

**Restart app and:**

1. Go to main page
2. Search for a doctor
3. Find 陳海聰醫生 (affiliated)
4. Click "Contact via WhatsApp"
5. Console should show:
   ```
   Contact doctor: {
       doctorName: "陳海聰醫生",
       doctorPhone: "+852 9123 4567",
       isAffiliated: true
   }
   ```
6. WhatsApp opens with **+852 9123 4567** ✅

7. Try a non-affiliated doctor
8. WhatsApp opens with **85294974070** (admin) ✅

---

**Status**: ✅ Contact button now correctly uses doctor's account phone for affiliated doctors!
