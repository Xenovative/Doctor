"""
Multi-Device 2FA Core Functions
Core functionality for managing multiple 2FA devices per admin user.
These functions should be integrated into the main app.py file.
"""

import sqlite3
import json
import pyotp
import qrcode
import io
import base64
from datetime import datetime
from functools import wraps

class MultiDevice2FA:
    """Multi-Device 2FA Manager"""
    
    def __init__(self, db_path='admin_data.db'):
        self.db_path = db_path
    
    def get_user_id_by_username(self, username):
        """Get user ID by username"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM admin_users WHERE username = ?', (username,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def get_user_devices(self, user_id):
        """Get all 2FA devices for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, device_name, totp_secret, is_primary, is_active, 
                   created_at, last_used, device_info
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
                'totp_secret': device[2],
                'is_primary': bool(device[3]),
                'is_active': bool(device[4]),
                'created_at': device[5],
                'last_used': device[6],
                'device_info': json.loads(device[7]) if device[7] else {}
            }
            for device in devices
        ]
    
    def get_active_devices(self, user_id):
        """Get only active 2FA devices for a user"""
        devices = self.get_user_devices(user_id)
        return [device for device in devices if device['is_active']]
    
    def verify_token_multi_device(self, user_id, token):
        """Verify TOTP token against all active devices"""
        active_devices = self.get_active_devices(user_id)
        
        for device in active_devices:
            if self._verify_single_token(device['totp_secret'], token):
                # Update last_used timestamp
                self._update_device_last_used(device['id'])
                return True, device
        
        return False, None
    
    def _verify_single_token(self, secret, token):
        """Verify TOTP token against a single secret"""
        try:
            totp = pyotp.TOTP(secret)
            clean_token = str(token).replace('-', '').replace(' ', '').strip()
            return totp.verify(clean_token, valid_window=2)
        except Exception:
            return False
    
    def _update_device_last_used(self, device_id):
        """Update device last used timestamp"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE admin_2fa_devices SET last_used = ? WHERE id = ?', 
                      (datetime.now(), device_id))
        conn.commit()
        conn.close()
    
    def add_device(self, user_id, device_name, totp_secret, device_info=None):
        """Add a new 2FA device"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if this is the first device (make it primary)
        cursor.execute('SELECT COUNT(*) FROM admin_2fa_devices WHERE user_id = ?', (user_id,))
        is_first_device = cursor.fetchone()[0] == 0
        
        # Check device name uniqueness for this user
        cursor.execute('SELECT COUNT(*) FROM admin_2fa_devices WHERE user_id = ? AND device_name = ?', 
                      (user_id, device_name))
        if cursor.fetchone()[0] > 0:
            conn.close()
            raise ValueError("Device name already exists")
        
        # Insert new device
        cursor.execute('''
            INSERT INTO admin_2fa_devices 
            (user_id, device_name, totp_secret, is_primary, is_active, created_at, device_info)
            VALUES (?, ?, ?, ?, 1, ?, ?)
        ''', (user_id, device_name, totp_secret, is_first_device, datetime.now(), 
              json.dumps(device_info) if device_info else None))
        
        device_id = cursor.lastrowid
        
        # Enable multi-device 2FA for user if not already enabled
        cursor.execute('UPDATE admin_users SET multi_device_2fa_enabled = 1 WHERE id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        return device_id
    
    def remove_device(self, user_id, device_id):
        """Remove a 2FA device"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if device exists and belongs to user
        cursor.execute('SELECT is_primary FROM admin_2fa_devices WHERE id = ? AND user_id = ?', 
                      (device_id, user_id))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            raise ValueError("Device not found")
        
        is_primary = result[0]
        
        # Check if this is the last device
        cursor.execute('SELECT COUNT(*) FROM admin_2fa_devices WHERE user_id = ?', (user_id,))
        device_count = cursor.fetchone()[0]
        
        if device_count <= 1:
            conn.close()
            raise ValueError("Cannot remove the last device")
        
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
    
    def toggle_device_status(self, user_id, device_id):
        """Toggle device active status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current status
        cursor.execute('SELECT is_active FROM admin_2fa_devices WHERE id = ? AND user_id = ?', 
                      (device_id, user_id))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            raise ValueError("Device not found")
        
        current_status = result[0]
        
        # Don't allow disabling the last active device
        if current_status:
            cursor.execute('SELECT COUNT(*) FROM admin_2fa_devices WHERE user_id = ? AND is_active = 1', 
                          (user_id,))
            active_count = cursor.fetchone()[0]
            
            if active_count <= 1:
                conn.close()
                raise ValueError("Cannot disable the last active device")
        
        # Toggle status
        new_status = not current_status
        cursor.execute('UPDATE admin_2fa_devices SET is_active = ? WHERE id = ?', (new_status, device_id))
        conn.commit()
        conn.close()
        
        return new_status
    
    def rename_device(self, user_id, device_id, new_name):
        """Rename a 2FA device"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if device exists and belongs to user
        cursor.execute('SELECT device_name FROM admin_2fa_devices WHERE id = ? AND user_id = ?', 
                      (device_id, user_id))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            raise ValueError("Device not found")
        
        # Check if name already exists for this user
        cursor.execute('SELECT COUNT(*) FROM admin_2fa_devices WHERE user_id = ? AND device_name = ? AND id != ?', 
                      (user_id, new_name, device_id))
        if cursor.fetchone()[0] > 0:
            conn.close()
            raise ValueError("Device name already exists")
        
        # Update device name
        cursor.execute('UPDATE admin_2fa_devices SET device_name = ? WHERE id = ?', (new_name, device_id))
        conn.commit()
        conn.close()
    
    def can_add_device(self, user_id):
        """Check if user can add another device"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get max devices allowed
        cursor.execute('SELECT max_2fa_devices FROM admin_users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        max_devices = result[0] if result else 3
        
        # Get current device count
        cursor.execute('SELECT COUNT(*) FROM admin_2fa_devices WHERE user_id = ? AND is_active = 1', 
                      (user_id,))
        current_count = cursor.fetchone()[0]
        
        conn.close()
        return current_count < max_devices
    
    def is_multi_device_enabled(self, user_id):
        """Check if multi-device 2FA is enabled for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT multi_device_2fa_enabled FROM admin_users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return bool(result[0]) if result else False
    
    def generate_device_qr_code(self, username, device_name, secret, issuer="Doctor AI Admin"):
        """Generate QR code for device setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=f"{username}_{device_name}",
            issuer_name=issuer
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_base64}"

# Global instance
multi_device_2fa = MultiDevice2FA()

# Decorator for multi-device 2FA verification
def require_multi_device_2fa(f):
    """Decorator to require multi-device 2FA verification"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user has multi-device 2FA enabled
        username = session.get('admin_username')
        if not username:
            return redirect(url_for('admin_login'))
        
        user_id = multi_device_2fa.get_user_id_by_username(username)
        if not user_id:
            return redirect(url_for('admin_login'))
        
        if multi_device_2fa.is_multi_device_enabled(user_id):
            # Multi-device 2FA is enabled, check if verified
            if not session.get('2fa_verified'):
                return redirect(url_for('admin_login'))
        
        return f(*args, **kwargs)
    return decorated_function

# Helper functions for integration with existing code
def verify_multi_device_totp_token(username, token):
    """Verify TOTP token against all active devices for a user"""
    user_id = multi_device_2fa.get_user_id_by_username(username)
    if not user_id:
        return False
    
    verified, device = multi_device_2fa.verify_token_multi_device(user_id, token)
    return verified

def get_user_2fa_devices_list(username):
    """Get list of 2FA devices for a user"""
    user_id = multi_device_2fa.get_user_id_by_username(username)
    if not user_id:
        return []
    
    return multi_device_2fa.get_user_devices(user_id)

def is_user_multi_device_enabled(username):
    """Check if user has multi-device 2FA enabled"""
    user_id = multi_device_2fa.get_user_id_by_username(username)
    if not user_id:
        return False
    
    return multi_device_2fa.is_multi_device_enabled(user_id)
