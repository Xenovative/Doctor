# Multi-Device 2FA Integration Guide

This guide shows how to integrate multi-device 2FA support into the existing Doctor AI admin system.

## Overview

The multi-device 2FA system allows super admin to have multiple authenticator devices (phones, tablets, etc.) for enhanced security and convenience.

## Files Created

1. `setup_multi_device_2fa.py` - Database migration script
2. `multi_device_2fa.py` - Core multi-device 2FA functions
3. `multi_device_2fa_routes.py` - Route handlers for device management
4. `templates/admin/manage-2fa-devices.html` - Device management interface
5. `templates/admin/add-2fa-device.html` - Add new device interface

## Integration Steps

### Step 1: Run Database Migration

```bash
python setup_multi_device_2fa.py
```

This creates the `admin_2fa_devices` table and migrates existing 2FA data.

### Step 2: Add Imports to app.py

Add these imports at the top of `app.py`:

```python
# Add after existing imports
from multi_device_2fa import (
    MultiDevice2FA, multi_device_2fa, verify_multi_device_totp_token,
    get_user_2fa_devices_list, is_user_multi_device_enabled
)
```

### Step 3: Update 2FA Verification Functions

Replace the existing `verify_totp_token` calls in login functions with multi-device support:

#### In admin_login() function (around line 3384):

**REPLACE:**
```python
if verify_totp_token(secret, totp_token):
    token_valid = True
    print(f"DEBUG - TOTP token valid")
```

**WITH:**
```python
# Check if user has multi-device 2FA enabled
user_id = multi_device_2fa.get_user_id_by_username(username)
if user_id and multi_device_2fa.is_multi_device_enabled(user_id):
    # Use multi-device verification
    token_valid, used_device = multi_device_2fa.verify_token_multi_device(user_id, totp_token)
    if token_valid:
        print(f"DEBUG - Multi-device TOTP token valid from device: {used_device['device_name']}")
else:
    # Fall back to single-device verification
    if verify_totp_token(secret, totp_token):
        token_valid = True
        print(f"DEBUG - TOTP token valid")
```

#### In super admin login section (around line 3606):

**REPLACE:**
```python
if verify_totp_token(secret, totp_token):
    token_valid = True
```

**WITH:**
```python
# Check if super admin has multi-device 2FA enabled
user_id = multi_device_2fa.get_user_id_by_username(ADMIN_USERNAME)
if user_id and multi_device_2fa.is_multi_device_enabled(user_id):
    # Use multi-device verification
    token_valid, used_device = multi_device_2fa.verify_token_multi_device(user_id, totp_token)
    if token_valid:
        print(f"DEBUG - Super admin multi-device TOTP valid from: {used_device['device_name']}")
else:
    # Fall back to single-device verification
    if verify_totp_token(secret, totp_token):
        token_valid = True
```

### Step 4: Add Multi-Device Routes

Add these routes to `app.py` (copy from `multi_device_2fa_routes.py`):

```python
# Multi-Device 2FA Routes
@app.route('/admin/2fa/devices')
@require_admin
def manage_2fa_devices():
    """Manage 2FA devices page"""
    if session.get('admin_username') != ADMIN_USERNAME:
        flash('只有超級管理員可以管理雙重認證設備', 'error')
        return redirect(url_for('admin_config'))
    
    user_id = multi_device_2fa.get_user_id_by_username(ADMIN_USERNAME)
    if not user_id:
        flash('用戶不存在', 'error')
        return redirect(url_for('admin_config'))
    
    devices = multi_device_2fa.get_user_devices(user_id)
    can_add = multi_device_2fa.can_add_device(user_id)
    
    return render_template('admin/manage-2fa-devices.html', 
                         devices=devices, 
                         can_add_device=can_add,
                         username=ADMIN_USERNAME)

@app.route('/admin/2fa/add-device', methods=['GET', 'POST'])
@require_admin
def add_2fa_device():
    """Add new 2FA device"""
    if session.get('admin_username') != ADMIN_USERNAME:
        flash('只有超級管理員可以添加雙重認證設備', 'error')
        return redirect(url_for('admin_config'))
    
    user_id = multi_device_2fa.get_user_id_by_username(ADMIN_USERNAME)
    if not user_id:
        flash('用戶不存在', 'error')
        return redirect(url_for('admin_config'))
    
    if not multi_device_2fa.can_add_device(user_id):
        flash('已達到最大設備數量限制', 'error')
        return redirect(url_for('manage_2fa_devices'))
    
    if request.method == 'GET':
        secret = generate_totp_secret()
        device_name = request.args.get('device_name', f'Device {datetime.now().strftime("%Y%m%d_%H%M%S")}')
        qr_code = multi_device_2fa.generate_device_qr_code(ADMIN_USERNAME, device_name, secret)
        
        session['temp_device_secret'] = secret
        session['temp_device_name'] = device_name
        
        return render_template('admin/add-2fa-device.html',
                             qr_code=qr_code,
                             secret=secret,
                             device_name=device_name,
                             username=ADMIN_USERNAME)
    
    elif request.method == 'POST':
        token = request.form.get('token')
        device_name = request.form.get('device_name') or session.get('temp_device_name')
        secret = session.get('temp_device_secret')
        
        if not secret or not token or not device_name:
            flash('無效的請求', 'error')
            return redirect(url_for('add_2fa_device'))
        
        if verify_totp_token(secret, token):
            try:
                device_info = {
                    'user_agent': request.user_agent.string,
                    'ip_address': get_real_ip(),
                    'setup_time': datetime.now().isoformat()
                }
                
                multi_device_2fa.add_device(user_id, device_name, secret, device_info)
                
                session.pop('temp_device_secret', None)
                session.pop('temp_device_name', None)
                
                log_analytics('2fa_device_added', {
                    'username': ADMIN_USERNAME,
                    'device_name': device_name
                }, get_real_ip(), request.user_agent.string)
                
                flash(f'設備 "{device_name}" 添加成功！', 'success')
                return redirect(url_for('manage_2fa_devices'))
                
            except ValueError as e:
                flash(str(e), 'error')
                return redirect(url_for('add_2fa_device'))
        else:
            flash('驗證碼錯誤，請重試', 'error')
            return redirect(url_for('add_2fa_device'))

@app.route('/admin/2fa/device/<int:device_id>/toggle', methods=['POST'])
@require_admin
def toggle_2fa_device(device_id):
    """Toggle device active status"""
    if session.get('admin_username') != ADMIN_USERNAME:
        return jsonify({'success': False, 'error': '權限不足'}), 403
    
    user_id = multi_device_2fa.get_user_id_by_username(ADMIN_USERNAME)
    if not user_id:
        return jsonify({'success': False, 'error': '用戶不存在'}), 404
    
    try:
        new_status = multi_device_2fa.toggle_device_status(user_id, device_id)
        status_text = '啟用' if new_status else '停用'
        
        return jsonify({
            'success': True, 
            'message': f'設備已{status_text}',
            'new_status': new_status
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/admin/2fa/device/<int:device_id>/delete', methods=['POST'])
@require_admin
def delete_2fa_device(device_id):
    """Delete 2FA device"""
    if session.get('admin_username') != ADMIN_USERNAME:
        return jsonify({'success': False, 'error': '權限不足'}), 403
    
    user_id = multi_device_2fa.get_user_id_by_username(ADMIN_USERNAME)
    if not user_id:
        return jsonify({'success': False, 'error': '用戶不存在'}), 404
    
    try:
        multi_device_2fa.remove_device(user_id, device_id)
        return jsonify({'success': True, 'message': '設備已刪除'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/admin/2fa/device/<int:device_id>/rename', methods=['POST'])
@require_admin
def rename_2fa_device(device_id):
    """Rename 2FA device"""
    if session.get('admin_username') != ADMIN_USERNAME:
        return jsonify({'success': False, 'error': '權限不足'}), 403
    
    new_name = request.json.get('name', '').strip()
    if not new_name:
        return jsonify({'success': False, 'error': '設備名稱不能為空'}), 400
    
    user_id = multi_device_2fa.get_user_id_by_username(ADMIN_USERNAME)
    if not user_id:
        return jsonify({'success': False, 'error': '用戶不存在'}), 404
    
    try:
        multi_device_2fa.rename_device(user_id, device_id, new_name)
        return jsonify({'success': True, 'message': f'設備已重命名為 "{new_name}"'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
```

### Step 5: Update Admin Config Template

Add multi-device 2FA management link to `templates/admin/config.html`:

Find the 2FA section and add:

```html
<!-- Multi-Device 2FA Management -->
<div class="card mb-4">
    <div class="card-header">
        <h5 class="card-title mb-0">
            <i class="fas fa-mobile-alt me-2"></i>多設備雙重認證
        </h5>
    </div>
    <div class="card-body">
        {% if session.admin_username == 'admin' %}
            <p class="text-muted mb-3">管理您的雙重認證設備，支持多個手機或平板電腦。</p>
            <a href="{{ url_for('manage_2fa_devices') }}" class="btn btn-primary">
                <i class="fas fa-cog me-2"></i>管理設備
            </a>
        {% else %}
            <p class="text-muted">只有超級管理員可以管理多設備雙重認證。</p>
        {% endif %}
    </div>
</div>
```

## Features

### Multi-Device Support
- Super admin can have up to 3 2FA devices by default
- Each device has a unique name for easy identification
- Primary device designation for main device
- Active/inactive status for temporary device disabling

### Device Management
- Add new devices with QR code setup
- Rename devices for better organization
- Toggle device active status
- Delete devices (with protection against removing last device)
- View device usage history

### Security Features
- Each device has its own TOTP secret
- Device usage tracking (last used timestamp)
- Device information logging (IP, user agent)
- Analytics logging for all device operations
- Backward compatibility with existing single-device 2FA

### User Experience
- Modern, responsive UI for device management
- Step-by-step device setup wizard
- QR code generation for easy mobile setup
- Manual key entry option for devices that can't scan QR codes
- Comprehensive help documentation

## Database Schema

### New Table: admin_2fa_devices
```sql
CREATE TABLE admin_2fa_devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    device_name TEXT NOT NULL,
    totp_secret TEXT NOT NULL,
    is_primary BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_used DATETIME,
    device_info TEXT,
    FOREIGN KEY (user_id) REFERENCES admin_users (id),
    UNIQUE(user_id, device_name)
);
```

### New Columns in admin_users
- `multi_device_2fa_enabled` BOOLEAN DEFAULT 0
- `max_2fa_devices` INTEGER DEFAULT 3

## Migration Process

1. Existing single-device 2FA data is automatically migrated to the new multi-device structure
2. The original device becomes the "Primary Device"
3. Users can continue using their existing authenticator app
4. New devices can be added through the management interface

## Backward Compatibility

The system maintains full backward compatibility:
- Existing 2FA setups continue to work
- Single-device users can upgrade to multi-device gradually
- Legacy verification methods are preserved as fallback

## Security Considerations

- Each device has a unique TOTP secret
- Device management requires super admin privileges
- All device operations are logged for audit purposes
- Cannot disable/delete the last active device
- Device information is tracked for security monitoring

## Usage Instructions

1. **Run Migration**: Execute `python setup_multi_device_2fa.py`
2. **Update app.py**: Follow the integration steps above
3. **Access Management**: Go to Admin Config → Multi-Device 2FA → Manage Devices
4. **Add Device**: Click "Add Device", scan QR code with authenticator app
5. **Manage Devices**: Rename, toggle, or delete devices as needed

The super admin can now use any of their registered devices for 2FA authentication, providing better security and convenience.
