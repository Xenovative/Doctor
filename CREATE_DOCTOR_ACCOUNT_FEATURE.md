# ✅ Create Doctor Account Feature Added

## Feature Overview
Admins can now create doctor login accounts directly from the existing doctor database panel, converting regular doctor entries into affiliated doctors with portal access.

## What Was Added

### 1. Frontend (templates/admin/doctors.html)

#### "創建帳戶" Button
Added to each doctor row in the operations column:
```html
<button class="btn btn-sm btn-primary mt-1 w-100" 
        onclick="createDoctorAccount(doctorId, doctorName, doctorEmail)">
    <i class="fas fa-user-plus"></i> 創建帳戶
</button>
```

#### Create Account Modal
Complete modal form with:
- **Username field** (required) - Suggests using doctor name or registration number
- **Password field** (required) - With random password generator button
- **Email field** (optional) - Pre-filled from doctor data
- **Phone field** (optional)
- **Security warning** - Reminds admin to securely share credentials

#### JavaScript Functions
```javascript
createDoctorAccount(doctorId, doctorName, doctorEmail)
- Opens modal with doctor info pre-filled

submitCreateAccount()
- Validates input (username, password min 6 chars)
- Sends POST request to backend
- Shows success message with credentials
- Reloads page to show updated status

generatePassword()
- Generates secure 12-character random password
- Includes letters, numbers, and special characters
```

### 2. Backend (app.py)

#### New Route: `/admin/create-doctor-account`
```python
@app.route('/admin/create-doctor-account', methods=['POST'])
@tab_permission_required('doctors')
def create_doctor_account():
```

**Features:**
- ✅ Validates doctor exists
- ✅ Checks if account already exists (prevents duplicates)
- ✅ Checks if username is taken
- ✅ Hashes password with SHA-256
- ✅ Creates `doctor_accounts` entry
- ✅ Updates doctor affiliation status to 'approved'
- ✅ Sets `is_affiliated = 1`
- ✅ Logs admin action
- ✅ Returns success with username

**Security:**
- Password hashing (SHA-256)
- Duplicate prevention
- Admin permission required
- Action logging

## Workflow

### Admin Side:
1. Admin goes to `/admin/doctors`
2. Finds doctor in database
3. Clicks "創建帳戶" button
4. Modal opens with doctor info
5. Admin enters username (or uses suggestion)
6. Admin generates or enters password
7. Optionally adds email/phone
8. Clicks "創建帳戶"
9. Success message shows credentials
10. Admin securely shares credentials with doctor

### What Happens in Database:
1. New row in `doctor_accounts` table:
   - `doctor_id` → Links to doctors table
   - `username` → Login username
   - `password_hash` → SHA-256 hashed password
   - `email`, `phone` → Contact info
   - `is_active` → Set to 1 (active)
   - `created_at` → Timestamp

2. Updates in `doctors` table:
   - `is_affiliated` → 1
   - `affiliation_status` → 'approved'
   - `affiliation_date` → Current timestamp

### Doctor Side:
1. Receives credentials from admin
2. Goes to `/doctor/login`
3. Logs in with provided username/password
4. Can change password in profile
5. Access to full doctor portal

## Features

### Password Generator
- **Length**: 12 characters
- **Charset**: Letters (upper/lower), numbers, special chars
- **Security**: Cryptographically random
- **One-click**: Generates and fills password field

### Validation
- ✅ Username required
- ✅ Password required (min 6 chars)
- ✅ Duplicate username check
- ✅ Duplicate account check
- ✅ Doctor existence check

### User Experience
- Pre-filled email from doctor data
- Clear success message with credentials
- Warning to share securely
- Auto-reload after creation
- Error messages for all failure cases

## Security Features

1. **Password Hashing**: SHA-256 (same as existing system)
2. **Permission Check**: Requires 'doctors' tab permission
3. **Duplicate Prevention**: Checks username and doctor_id
4. **Action Logging**: Logs which admin created which account
5. **Secure Display**: Shows credentials only once in alert

## Integration

### Works With Existing System:
- ✅ Uses same `doctor_accounts` table structure
- ✅ Compatible with doctor portal login
- ✅ Integrates with affiliation system
- ✅ Follows existing permission model
- ✅ Uses same password hashing method

### Automatic Affiliation:
When account is created:
- Doctor becomes "affiliated"
- Status set to "approved"
- Appears in affiliation management
- Can access doctor portal immediately

## Usage Example

**Scenario**: Admin wants to onboard Dr. Wong

1. Admin searches for "Dr. Wong" in doctor database
2. Clicks "創建帳戶" on Dr. Wong's row
3. Modal shows: "為 Dr. Wong 創建登入帳戶"
4. Admin enters username: `drwong`
5. Admin clicks "生成" to generate password: `aB3$xY9#mK2p`
6. Admin clicks "創建帳戶"
7. Success message: "醫生帳戶創建成功！用戶名: drwong 密碼: aB3$xY9#mK2p"
8. Admin sends credentials to Dr. Wong via secure channel
9. Dr. Wong can now login at `/doctor/login`

## Files Modified

1. **templates/admin/doctors.html**
   - Added "創建帳戶" button (line 393-395)
   - Added create account modal (lines 1580-1636)
   - Added JavaScript functions (lines 1512-1577)

2. **app.py**
   - Added `/admin/create-doctor-account` route (lines 5633-5709)

## Benefits

1. **Streamlined Onboarding**: Convert existing doctors to affiliated in seconds
2. **No Manual Database Work**: All done through UI
3. **Secure**: Password hashing, validation, logging
4. **User-Friendly**: Clear workflow with helpful suggestions
5. **Integrated**: Works seamlessly with existing affiliation system

## Future Enhancements

Possible additions:
- Email notification to doctor with credentials
- Bulk account creation for multiple doctors
- Password reset link generation
- Account activation workflow
- Welcome email template

---

**Status**: ✅ Feature complete and ready to use!

**Test**: Go to `/admin/doctors`, find a doctor, click "創建帳戶"
