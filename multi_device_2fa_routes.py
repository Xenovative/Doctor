"""
Multi-Device 2FA Routes
Routes for managing multiple 2FA devices per admin user.
These routes should be integrated into the main app.py file.
"""

import sqlite3
import json
import pyotp
import qrcode
import io
import base64
from datetime import datetime
from flask import request, jsonify, session, render_template, redirect, url_for, flash

# Multi-Device 2FA Helper Functions
def get_user_2fa_devices(user_id):
    """Get all 2FA devices for a user"""
    conn = sqlite3.connect('admin_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, device_name, is_primary, is_active, created_at, last_used, device_info
        FROM admin_2fa_devices 
        WHERE user_id = ? 
        ORDER BY is_primary DESC, created_at ASC
    ''', (user_id,))
    devices = cursor.fetchall()
    conn.close()
    
    return [
        {
            'id': device[0],
            'device_name': device[1],
            'is_primary': bool(device[2]),
            'is_active': bool(device[3]),
            'created_at': device[4],
            'last_used': device[5],
            'device_info': json.loads(device[6]) if device[6] else {}
        }
        for device in devices
    ]

def get_active_2fa_secrets(user_id):
    """Get all active TOTP secrets for a user"""
    conn = sqlite3.connect('admin_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT totp_secret FROM admin_2fa_devices 
        WHERE user_id = ? AND is_active = 1
    ''', (user_id,))
    secrets = [row[0] for row in cursor.fetchall()]
    conn.close()
    return secrets

def verify_multi_device_totp(user_id, token):
    """Verify TOTP token against all active devices"""
    secrets = get_active_2fa_secrets(user_id)
    
    for secret in secrets:
        if verify_totp_token(secret, token):
            # Update last_used timestamp for the device
            conn = sqlite3.connect('admin_data.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE admin_2fa_devices 
                SET last_used = ? 
                WHERE user_id = ? AND totp_secret = ?
            ''', (datetime.now(), user_id, secret))
            conn.commit()
            conn.close()
            return True
    
    return False

def can_add_device(user_id):
    """Check if user can add another device"""
    conn = sqlite3.connect('admin_data.db')
    cursor = conn.cursor()
    
    # Get max devices allowed
    cursor.execute('SELECT max_2fa_devices FROM admin_users WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    max_devices = result[0] if result else 3
    
    # Get current device count
    cursor.execute('SELECT COUNT(*) FROM admin_2fa_devices WHERE user_id = ? AND is_active = 1', (user_id,))
    current_count = cursor.fetchone()[0]
    
    conn.close()
    return current_count < max_devices

# Routes to be integrated into app.py

def setup_multi_device_2fa_routes(app):
    """Setup multi-device 2FA routes"""
    
    @app.route('/admin/2fa/devices')
    @require_admin
    def manage_2fa_devices():
        """Manage 2FA devices page"""
        if session.get('admin_username') != ADMIN_USERNAME:
            flash('只有超級管理員可以管理雙重認證設備', 'error')
            return redirect(url_for('admin_config'))
        
        # Get user ID
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM admin_users WHERE username = ?', (ADMIN_USERNAME,))
        user_result = cursor.fetchone()
        conn.close()
        
        if not user_result:
            flash('用戶不存在', 'error')
            return redirect(url_for('admin_config'))
        
        user_id = user_result[0]
        devices = get_user_2fa_devices(user_id)
        can_add = can_add_device(user_id)
        
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
        
        # Get user ID
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM admin_users WHERE username = ?', (ADMIN_USERNAME,))
        user_result = cursor.fetchone()
        conn.close()
        
        if not user_result:
            flash('用戶不存在', 'error')
            return redirect(url_for('admin_config'))
        
        user_id = user_result[0]
        
        if not can_add_device(user_id):
            flash('已達到最大設備數量限制', 'error')
            return redirect(url_for('manage_2fa_devices'))
        
        if request.method == 'GET':
            # Generate new secret and QR code
            secret = generate_totp_secret()
            device_name = request.args.get('device_name', f'Device {datetime.now().strftime("%Y%m%d_%H%M%S")}')
            qr_code = generate_qr_code(f"{ADMIN_USERNAME}_{device_name}", secret)
            
            # Store in session temporarily
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
            
            # Verify the token
            if verify_totp_token(secret, token):
                # Save device to database
                conn = sqlite3.connect('admin_data.db')
                cursor = conn.cursor()
                
                # Check if this is the first device (make it primary)
                cursor.execute('SELECT COUNT(*) FROM admin_2fa_devices WHERE user_id = ?', (user_id,))
                is_first_device = cursor.fetchone()[0] == 0
                
                device_info = {
                    'user_agent': request.user_agent.string,
                    'ip_address': request.remote_addr,
                    'setup_time': datetime.now().isoformat()
                }
                
                cursor.execute('''
                    INSERT INTO admin_2fa_devices 
                    (user_id, device_name, totp_secret, is_primary, is_active, created_at, device_info)
                    VALUES (?, ?, ?, ?, 1, ?, ?)
                ''', (user_id, device_name, secret, is_first_device, datetime.now(), json.dumps(device_info)))
                
                # Enable multi-device 2FA for user
                cursor.execute('UPDATE admin_users SET multi_device_2fa_enabled = 1 WHERE id = ?', (user_id,))
                
                conn.commit()
                conn.close()
                
                # Clear temp data
                session.pop('temp_device_secret', None)
                session.pop('temp_device_name', None)
                
                # Log the setup
                log_analytics('2fa_device_added', {
                    'username': ADMIN_USERNAME,
                    'device_name': device_name,
                    'is_primary': is_first_device
                }, get_real_ip(), request.user_agent.string)
                
                flash(f'設備 "{device_name}" 添加成功！', 'success')
                return redirect(url_for('manage_2fa_devices'))
            else:
                flash('驗證碼錯誤，請重試', 'error')
                return redirect(url_for('add_2fa_device'))
    
    @app.route('/admin/2fa/device/<int:device_id>/toggle', methods=['POST'])
    @require_admin
    def toggle_2fa_device(device_id):
        """Toggle device active status"""
        if session.get('admin_username') != ADMIN_USERNAME:
            return jsonify({'success': False, 'error': '權限不足'}), 403
        
        # Get user ID
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM admin_users WHERE username = ?', (ADMIN_USERNAME,))
        user_result = cursor.fetchone()
        
        if not user_result:
            conn.close()
            return jsonify({'success': False, 'error': '用戶不存在'}), 404
        
        user_id = user_result[0]
        
        # Get device info
        cursor.execute('''
            SELECT device_name, is_primary, is_active 
            FROM admin_2fa_devices 
            WHERE id = ? AND user_id = ?
        ''', (device_id, user_id))
        device_result = cursor.fetchone()
        
        if not device_result:
            conn.close()
            return jsonify({'success': False, 'error': '設備不存在'}), 404
        
        device_name, is_primary, is_active = device_result
        
        # Don't allow disabling the last active device
        if is_active:
            cursor.execute('SELECT COUNT(*) FROM admin_2fa_devices WHERE user_id = ? AND is_active = 1', (user_id,))
            active_count = cursor.fetchone()[0]
            
            if active_count <= 1:
                conn.close()
                return jsonify({'success': False, 'error': '不能停用最後一個活躍設備'}), 400
        
        # Toggle status
        new_status = not is_active
        cursor.execute('UPDATE admin_2fa_devices SET is_active = ? WHERE id = ?', (new_status, device_id))
        conn.commit()
        conn.close()
        
        # Log the action
        log_analytics('2fa_device_toggled', {
            'username': ADMIN_USERNAME,
            'device_name': device_name,
            'device_id': device_id,
            'new_status': new_status
        }, get_real_ip(), request.user_agent.string)
        
        status_text = '啟用' if new_status else '停用'
        return jsonify({
            'success': True, 
            'message': f'設備 "{device_name}" 已{status_text}',
            'new_status': new_status
        })
    
    @app.route('/admin/2fa/device/<int:device_id>/delete', methods=['POST'])
    @require_admin
    def delete_2fa_device(device_id):
        """Delete 2FA device"""
        if session.get('admin_username') != ADMIN_USERNAME:
            return jsonify({'success': False, 'error': '權限不足'}), 403
        
        # Get user ID
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM admin_users WHERE username = ?', (ADMIN_USERNAME,))
        user_result = cursor.fetchone()
        
        if not user_result:
            conn.close()
            return jsonify({'success': False, 'error': '用戶不存在'}), 404
        
        user_id = user_result[0]
        
        # Get device info
        cursor.execute('''
            SELECT device_name, is_primary 
            FROM admin_2fa_devices 
            WHERE id = ? AND user_id = ?
        ''', (device_id, user_id))
        device_result = cursor.fetchone()
        
        if not device_result:
            conn.close()
            return jsonify({'success': False, 'error': '設備不存在'}), 404
        
        device_name, is_primary = device_result
        
        # Check if this is the last device
        cursor.execute('SELECT COUNT(*) FROM admin_2fa_devices WHERE user_id = ?', (user_id,))
        device_count = cursor.fetchone()[0]
        
        if device_count <= 1:
            conn.close()
            return jsonify({'success': False, 'error': '不能刪除最後一個設備'}), 400
        
        # Delete device
        cursor.execute('DELETE FROM admin_2fa_devices WHERE id = ?', (device_id,))
        
        # If this was the primary device, make another device primary
        if is_primary:
            cursor.execute('''
                UPDATE admin_2fa_devices 
                SET is_primary = 1 
                WHERE user_id = ? AND id = (
                    SELECT id FROM admin_2fa_devices 
                    WHERE user_id = ? 
                    ORDER BY created_at ASC 
                    LIMIT 1
                )
            ''', (user_id, user_id))
        
        conn.commit()
        conn.close()
        
        # Log the action
        log_analytics('2fa_device_deleted', {
            'username': ADMIN_USERNAME,
            'device_name': device_name,
            'device_id': device_id,
            'was_primary': is_primary
        }, get_real_ip(), request.user_agent.string)
        
        return jsonify({
            'success': True, 
            'message': f'設備 "{device_name}" 已刪除'
        })
    
    @app.route('/admin/2fa/device/<int:device_id>/rename', methods=['POST'])
    @require_admin
    def rename_2fa_device(device_id):
        """Rename 2FA device"""
        if session.get('admin_username') != ADMIN_USERNAME:
            return jsonify({'success': False, 'error': '權限不足'}), 403
        
        new_name = request.json.get('name', '').strip()
        if not new_name:
            return jsonify({'success': False, 'error': '設備名稱不能為空'}), 400
        
        # Get user ID
        conn = sqlite3.connect('admin_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM admin_users WHERE username = ?', (ADMIN_USERNAME,))
        user_result = cursor.fetchone()
        
        if not user_result:
            conn.close()
            return jsonify({'success': False, 'error': '用戶不存在'}), 404
        
        user_id = user_result[0]
        
        # Check if device exists and belongs to user
        cursor.execute('SELECT device_name FROM admin_2fa_devices WHERE id = ? AND user_id = ?', (device_id, user_id))
        device_result = cursor.fetchone()
        
        if not device_result:
            conn.close()
            return jsonify({'success': False, 'error': '設備不存在'}), 404
        
        old_name = device_result[0]
        
        # Check if name already exists for this user
        cursor.execute('SELECT COUNT(*) FROM admin_2fa_devices WHERE user_id = ? AND device_name = ? AND id != ?', 
                      (user_id, new_name, device_id))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return jsonify({'success': False, 'error': '設備名稱已存在'}), 400
        
        # Update device name
        cursor.execute('UPDATE admin_2fa_devices SET device_name = ? WHERE id = ?', (new_name, device_id))
        conn.commit()
        conn.close()
        
        # Log the action
        log_analytics('2fa_device_renamed', {
            'username': ADMIN_USERNAME,
            'device_id': device_id,
            'old_name': old_name,
            'new_name': new_name
        }, get_real_ip(), request.user_agent.string)
        
        return jsonify({
            'success': True, 
            'message': f'設備已重命名為 "{new_name}"'
        })
