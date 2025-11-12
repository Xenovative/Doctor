# ✅ Edit Account Feature Added

## Feature Overview
The "創建醫生帳戶" button now dynamically changes to "編輯帳戶" when a doctor already has an account.

## Changes Made

### 1. Dynamic Button Text & Style

**When Doctor Has NO Account:**
- Button: Green "創建醫生帳戶" 
- Icon: User Plus (fa-user-plus)
- Color: Success (green)

**When Doctor HAS Account:**
- Button: Blue "編輯帳戶"
- Icon: User Edit (fa-user-edit)
- Color: Info (blue)
- Badge: Shows "✓ 已加盟" in modal header

### 2. Modal Behavior

**Create Mode (No Account):**
- Title: "創建醫生帳戶"
- Username: Empty, editable
- Password: Required, empty
- Action: Creates new account

**Edit Mode (Has Account):**
- Title: "編輯醫生帳戶"
- Username: Pre-filled, read-only (grayed out)
- Password: Optional, placeholder says "留空表示不更改密碼"
- Email/Phone: Editable
- Action: Updates existing account

### 3. Smart Validation

**Create Mode:**
- Username: Required
- Password: Required (min 6 characters)

**Edit Mode:**
- Username: Cannot change (read-only)
- Password: Optional - only validates if provided
- If password empty: Keeps existing password
- If password provided: Must be min 6 characters

## How It Works

### When Opening Edit Modal:
1. `checkDoctorAccount()` is called
2. Checks if doctor has account via API
3. If has account:
   - Button changes to blue "編輯帳戶"
   - Stores username in button data attribute
   - Shows affiliation badge
4. If no account:
   - Button stays green "創建醫生帳戶"
   - No badge shown

### When Clicking Button:
1. `openCreateAccountModal()` checks button mode
2. **Edit Mode**: 
   - Pre-fills username (read-only)
   - Password optional
   - Modal title: "編輯醫生帳戶"
3. **Create Mode**:
   - Empty username (editable)
   - Password required
   - Modal title: "創建醫生帳戶"

### When Submitting:
1. Detects mode by checking if username field is read-only
2. **Edit Mode**: Password optional, updates account
3. **Create Mode**: Password required, creates account

## Visual Indicators

### Button States:
```
No Account:  [🟢 ➕ 創建醫生帳戶]
Has Account: [🔵 ✏️ 編輯帳戶] + [✓ 已加盟] badge
```

### Modal States:
```
Create Mode:
  創建醫生帳戶
  Username: [________] (editable)
  Password: [________] (required)

Edit Mode:
  編輯醫生帳戶
  Username: [chanhoichung] (grayed out, read-only)
  Password: [________] (optional - 留空表示不更改密碼)
```

## Files Modified

**templates/admin/doctors.html**
1. Added `<span id="accountBtnText">` for dynamic text (line 652)
2. Updated `checkDoctorAccount()` to change button style (lines 1599-1649)
3. Updated `openCreateAccountModal()` to handle edit mode (lines 1551-1595)
4. Updated `submitCreateAccount()` validation (lines 1652-1676)

## Benefits

1. **Clear Visual Feedback**: Users instantly know if doctor has account
2. **Prevent Duplicates**: Can't accidentally create duplicate accounts
3. **Easy Updates**: Can update email/phone without recreating account
4. **Password Safety**: Can change password or leave unchanged
5. **Better UX**: One button that adapts to context

## Usage

### For Doctors Without Accounts:
1. Click "編輯" on doctor
2. See green "創建醫生帳戶" button
3. Click to create account
4. Fill username & password
5. Submit

### For Doctors With Accounts:
1. Click "編輯" on doctor
2. See blue "編輯帳戶" button + "✓ 已加盟" badge
3. Click to edit account
4. Username shown (can't change)
5. Update email/phone if needed
6. Change password (optional)
7. Submit

## Example Flow

**陳海聰醫生 (Has Account):**
1. Click "編輯" → Modal opens
2. Button shows: "🔵 ✏️ 編輯帳戶"
3. Badge shows: "✓ 已加盟"
4. Click button → Edit modal opens
5. Username: "chanhoichung" (read-only)
6. Can update email/phone
7. Can change password or leave empty
8. Submit → Account updated!

---

**Status**: ✅ Feature complete - button adapts to account status!
