# ✅ Create Account Button Moved to Edit Modal

## Changes Made

### 1. Button Location Changed
**Before**: Button in table row (hard to see, cluttered)
**After**: Button in edit doctor modal footer (clean, contextual)

### 2. Smart Button Display
The "創建醫生帳戶" button now:
- ✅ Only shows when doctor **doesn't** have an account
- ✅ Hides automatically if account already exists
- ✅ Appears in modal footer next to "儲存變更"

### 3. Workflow Improved

**New Flow:**
1. Admin clicks "編輯" on any doctor
2. Edit modal opens with doctor details
3. **If doctor has no account**: Green "創建醫生帳戶" button appears
4. **If doctor has account**: Button hidden (no duplicate accounts)
5. Admin clicks "創建醫生帳戶"
6. Edit modal closes, Create Account modal opens
7. Doctor info pre-filled (name, email, phone)
8. Admin creates account
9. Success! Doctor can now login

## Technical Implementation

### Frontend (templates/admin/doctors.html)

#### Button in Modal Footer
```html
<div class="modal-footer">
    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
    <button type="button" class="btn btn-success" id="createAccountBtn" 
            style="display: none;" onclick="openCreateAccountModal()">
        <i class="fas fa-user-plus me-2"></i>創建醫生帳戶
    </button>
    <button type="button" class="btn btn-primary" onclick="saveDoctorChanges()">儲存變更</button>
</div>
```

#### JavaScript Functions

**checkDoctorAccount(doctorId)**
- Calls `/admin/check-doctor-account/{doctorId}`
- Shows button if no account exists
- Hides button if account exists

**openCreateAccountModal()**
- Gets doctor info from edit form
- Closes edit modal
- Opens create account modal
- Pre-fills doctor data (name, email, phone)

**Updated editDoctor()**
- Calls `checkDoctorAccount()` after loading doctor data
- Automatically shows/hides button

### Backend (app.py)

#### New Route: `/admin/check-doctor-account/<doctor_id>`
```python
@app.route('/admin/check-doctor-account/<int:doctor_id>')
@tab_permission_required('doctors')
def check_doctor_account(doctor_id):
    # Checks if doctor_accounts table has entry for this doctor
    # Returns: {'success': True, 'has_account': bool}
```

## Benefits

### 1. **Better UX**
- Button only appears when relevant
- Clear context (in edit modal)
- No clutter in table view

### 2. **Prevents Errors**
- Can't create duplicate accounts
- Button hidden if account exists
- Clear visual feedback

### 3. **Streamlined Workflow**
- Edit doctor → See if account needed → Create account
- All in one flow
- Pre-filled data from doctor record

### 4. **Clean Interface**
- Table view stays clean
- Button appears contextually
- Professional appearance

## User Experience

### Scenario 1: Doctor Without Account
1. Admin clicks "編輯" on Dr. Wong
2. Modal opens, shows doctor details
3. **Green "創建醫生帳戶" button appears** ✅
4. Admin clicks button
5. Create account modal opens with Dr. Wong's info
6. Admin creates account
7. Dr. Wong can now login

### Scenario 2: Doctor With Account
1. Admin clicks "編輯" on Dr. Lee
2. Modal opens, shows doctor details
3. **No create account button** (already has account) ✅
4. Admin edits details if needed
5. Saves changes

## Visual Design

**Button Style:**
- Color: Green (`btn-success`)
- Icon: User plus icon
- Text: "創建醫生帳戶"
- Position: Between "取消" and "儲存變更"

**Button States:**
- Hidden by default (`display: none`)
- Shows when doctor has no account
- Smooth appearance (no jarring changes)

## Files Modified

1. **templates/admin/doctors.html**
   - Removed button from table row (line 393-395)
   - Added button to modal footer (line 628-630)
   - Added `checkDoctorAccount()` function (lines 1537-1552)
   - Updated `openCreateAccountModal()` function (lines 1513-1534)
   - Added check in `editDoctor()` (line 1163)

2. **app.py**
   - Added `/admin/check-doctor-account/<doctor_id>` route (lines 5633-5650)

## Security

- ✅ Admin permission required (`@tab_permission_required('doctors')`)
- ✅ Checks for existing accounts (prevents duplicates)
- ✅ Validates doctor exists before showing button
- ✅ All existing security features maintained

## Testing

**Test Case 1**: Doctor without account
1. Go to `/admin/doctors`
2. Find doctor without account
3. Click "編輯"
4. Verify green "創建醫生帳戶" button appears
5. Click button
6. Verify create account modal opens with pre-filled data

**Test Case 2**: Doctor with account
1. Go to `/admin/doctors`
2. Find doctor with account
3. Click "編輯"
4. Verify no "創建醫生帳戶" button appears

**Test Case 3**: Create account flow
1. Click "創建醫生帳戶" in edit modal
2. Verify edit modal closes
3. Verify create account modal opens
4. Verify doctor name, email, phone pre-filled
5. Create account
6. Verify success message
7. Verify button no longer appears for that doctor

## Future Enhancements

Possible additions:
- Show account status badge in edit modal
- Link to manage existing account
- Show account creation date
- Quick password reset from edit modal

---

**Status**: ✅ Feature complete and improved!

**Restart app and test**: Go to `/admin/doctors`, click "編輯" on any doctor
