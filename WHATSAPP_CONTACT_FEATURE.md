# ✅ WhatsApp Contact for Affiliated Doctors

## Feature Overview
Affiliated doctors now have a WhatsApp button in the contact column that uses their account phone number instead of the general clinic contact.

## Changes Made

### 1. Backend - Include Account Phone

**File: `app.py`**

Updated the doctor query to LEFT JOIN with `doctor_accounts` table:

```python
SELECT d.id,
       d.name_zh,
       ...
       d.contact_numbers,
       COALESCE(d.is_affiliated, 0) as is_affiliated,
       da.phone as account_phone  -- NEW: Account phone for WhatsApp
FROM doctors d
LEFT JOIN doctor_accounts da ON d.id = da.doctor_id AND da.is_active = 1
```

This ensures every doctor record includes:
- `is_affiliated`: Whether they have an account
- `account_phone`: Their personal account phone number (null if not affiliated)

### 2. Frontend - WhatsApp Button

**File: `templates/admin/doctors.html`**

Updated the contact column render function in DataTables:

```javascript
"render": function(data, type, row) {
    if (type === 'display') {
        let html = '';
        // For affiliated doctors, use account phone and add WhatsApp button
        if (row.is_affiliated == 1 && row.account_phone) {
            const phone = row.account_phone.replace(/[^0-9+]/g, '');
            html = `<small><i class="fas fa-phone me-1"></i>${row.account_phone}</small>`;
            html += `<br><a href="https://wa.me/${phone}" target="_blank" class="btn btn-success btn-sm mt-1">
                <i class="fab fa-whatsapp me-1"></i>WhatsApp
            </a>`;
        } else if (data) {
            // For non-affiliated, show regular contact
            html = `<small><i class="fas fa-phone me-1"></i>${data.split(',')[0]}</small>`;
        }
        return html || '';
    }
    return data || '';
}
```

## How It Works

### For Affiliated Doctors (has account):
1. Shows their **account phone number** (from `doctor_accounts.phone`)
2. Displays a green **WhatsApp button**
3. Clicking opens WhatsApp with their account phone
4. Opens in new tab

### For Non-Affiliated Doctors (no account):
1. Shows their **clinic contact number** (from `doctors.contact_numbers`)
2. No WhatsApp button
3. Just displays the phone number

## Visual Display

### Affiliated Doctor (陳海聰醫生):
```
📞 +852 9123 4567
[💬 WhatsApp]  ← Green button, clickable
```

### Non-Affiliated Doctor:
```
📞 85223977731
```

## WhatsApp Link Format

The WhatsApp link uses the international format:
```
https://wa.me/85291234567
```

Phone number is cleaned to remove:
- Spaces
- Dashes
- Parentheses
- Only keeps: digits and `+`

## Benefits

1. **Direct Contact**: Patients/admin can contact affiliated doctors directly
2. **Personal Number**: Uses doctor's personal account phone, not clinic number
3. **Verified**: Only shows for doctors with active accounts
4. **Convenient**: One-click WhatsApp messaging
5. **Professional**: Clear distinction between affiliated and non-affiliated

## Example Use Cases

### Admin Needs to Contact Doctor:
1. Go to `/admin/doctors`
2. Find affiliated doctor (has "✓ 已加盟" badge)
3. See WhatsApp button in contact column
4. Click to message directly

### Patient Inquiry:
1. Admin checks doctor availability
2. Sees affiliated doctor with WhatsApp
3. Can quickly message for confirmation
4. Direct communication channel

## Files Modified

1. **app.py** (lines 5860-5883, 5890-5931)
   - Added LEFT JOIN with `doctor_accounts`
   - Included `account_phone` in SELECT
   - Updated WHERE clauses with table aliases

2. **templates/admin/doctors.html** (lines 721-743)
   - Added render function for contact column
   - WhatsApp button for affiliated doctors
   - Conditional display logic

## Testing

**Restart app and:**

1. Go to `/admin/doctors`
2. Find 陳海聰醫生 (ID: 3769)
3. Look at contact column
4. Should see:
   - Their account phone number
   - Green WhatsApp button
   - Badge shows "✓ 已加盟"
5. Click WhatsApp button
6. Opens WhatsApp with their number

---

**Status**: ✅ WhatsApp contact feature complete for affiliated doctors!
