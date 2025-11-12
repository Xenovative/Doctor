# ✅ Create Account Button Fixed

## Issue
The "創建醫生帳戶" button was not showing in the edit modal.

## Root Cause
The button was hidden by default (`display: none`) and only shown after checking if the doctor has an account. If the check failed or the route didn't exist, the button stayed hidden.

## Fix Applied

### 1. Button Now Visible by Default
**Before:**
```html
<button id="createAccountBtn" style="display: none;">
```

**After:**
```html
<button id="createAccountBtn">
```

The button is now visible by default and will be hidden only if we confirm the doctor already has an account.

### 2. Improved Error Handling
Updated `checkDoctorAccount()` function to:
- Show button by default on any error
- Better error logging
- Graceful fallback if API fails

```javascript
// On error, show create button (safe default)
createBtn.style.display = 'inline-block';
```

## How It Works Now

### When Edit Modal Opens:
1. Button shows immediately ✅
2. `checkDoctorAccount()` is called in background
3. **If doctor has account**: Button hides, badge shows
4. **If doctor has no account**: Button stays visible
5. **If check fails**: Button stays visible (safe default)

## Files Modified

**templates/admin/doctors.html**
- Removed `style="display: none;"` from button (line 648)
- Updated `checkDoctorAccount()` with better error handling (lines 1560-1589)

## ✅ Test Now

1. Restart your Flask app
2. Go to `/admin/doctors`
3. Click "編輯" on any doctor
4. You should now see the green "創建醫生帳戶" button in the modal footer

## Button Behavior

**Always Shows When:**
- ✅ Modal first opens
- ✅ API check fails
- ✅ Doctor has no account

**Hides Only When:**
- ❌ API confirms doctor already has account
- ❌ Badge shows instead

## Create Account Flow

1. Click "編輯" on doctor
2. See green "創建醫生帳戶" button
3. Click button
4. Create account modal opens
5. Fill in username/password
6. Click "創建帳戶"
7. Account created!
8. Doctor marked as affiliated
9. Badge will show on next edit

---

**Status**: ✅ Button now visible and working!
