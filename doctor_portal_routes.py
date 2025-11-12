"""
Doctor Portal Routes
Handles authentication, profile management, and reservation management for affiliated doctors
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from functools import wraps
import sqlite3
import hashlib
import secrets
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
import json
import os

doctor_portal = Blueprint('doctor_portal', __name__, url_prefix='/doctor')

# Get absolute path to database files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCTORS_DB = os.path.join(BASE_DIR, 'doctors.db')
ADMIN_DB = os.path.join(BASE_DIR, 'admin_data.db')

# ==================== Helper Functions ====================

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_confirmation_code() -> str:
    """Generate unique confirmation code for reservations"""
    return secrets.token_urlsafe(8).upper()

def get_doctor_db():
    """Get connection to doctors.db"""
    conn = sqlite3.connect(DOCTORS_DB)
    conn.row_factory = sqlite3.Row
    return conn

def get_admin_db():
    """Get connection to admin_data.db"""
    conn = sqlite3.connect(ADMIN_DB)
    conn.row_factory = sqlite3.Row
    return conn

def doctor_login_required(f):
    """Decorator to require doctor login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'doctor_id' not in session:
            return redirect(url_for('doctor_portal.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_doctor_info(doctor_id: int) -> dict:
    """Get doctor information"""
    conn = get_doctor_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT d.*, da.email, da.phone, da.email_verified, da.phone_verified
        FROM doctors d
        LEFT JOIN doctor_accounts da ON d.id = da.doctor_id
        WHERE d.id = ?
    """, (doctor_id,))
    
    doctor = cursor.fetchone()
    conn.close()
    
    if doctor:
        return dict(doctor)
    return None

# ==================== Authentication Routes ====================

@doctor_portal.route('/login', methods=['GET', 'POST'])
def login():
    """Doctor login page"""
    if request.method == 'GET':
        return render_template('doctor/login.html')
    
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': '請輸入用戶名和密碼'}), 400
        
        conn = get_doctor_db()
        cursor = conn.cursor()
        
        # Get doctor account
        cursor.execute("""
            SELECT da.*, d.is_affiliated, d.affiliation_status
            FROM doctor_accounts da
            JOIN doctors d ON da.doctor_id = d.id
            WHERE da.username = ? AND da.is_active = 1
        """, (username,))
        
        account = cursor.fetchone()
        
        if not account:
            conn.close()
            return jsonify({'success': False, 'message': '用戶名或密碼錯誤'}), 401
        
        # Verify password
        password_hash = hash_password(password)
        if account['password_hash'] != password_hash:
            conn.close()
            return jsonify({'success': False, 'message': '用戶名或密碼錯誤'}), 401
        
        # Check affiliation status
        if account['affiliation_status'] != 'approved':
            conn.close()
            return jsonify({'success': False, 'message': '您的帳戶尚未獲得批准或已被暫停'}), 403
        
        # Check if 2FA is enabled
        if account['totp_enabled']:
            # Store temporary session data for 2FA
            session['doctor_2fa_pending'] = account['doctor_id']
            conn.close()
            return jsonify({'success': True, 'requires_2fa': True})
        
        # Update last login
        cursor.execute("""
            UPDATE doctor_accounts 
            SET last_login = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (account['id'],))
        conn.commit()
        conn.close()
        
        # Set session
        session['doctor_id'] = account['doctor_id']
        session['doctor_username'] = account['username']
        session['doctor_email'] = account['email']
        
        return jsonify({'success': True, 'requires_2fa': False})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'登錄失敗: {str(e)}'}), 500

@doctor_portal.route('/login/2fa', methods=['POST'])
def login_2fa():
    """Verify 2FA token during login"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if 'doctor_2fa_pending' not in session:
            return jsonify({'success': False, 'message': '無效的會話'}), 400
        
        doctor_id = session['doctor_2fa_pending']
        
        conn = get_doctor_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT totp_secret, backup_codes, username, email
            FROM doctor_accounts
            WHERE doctor_id = ?
        """, (doctor_id,))
        
        account = cursor.fetchone()
        
        if not account:
            conn.close()
            return jsonify({'success': False, 'message': '帳戶不存在'}), 404
        
        # Verify TOTP token
        totp = pyotp.TOTP(account['totp_secret'])
        if totp.verify(token, valid_window=1):
            # Update last login
            cursor.execute("""
                UPDATE doctor_accounts 
                SET last_login = CURRENT_TIMESTAMP 
                WHERE doctor_id = ?
            """, (doctor_id,))
            conn.commit()
            conn.close()
            
            # Set session
            session.pop('doctor_2fa_pending', None)
            session['doctor_id'] = doctor_id
            session['doctor_username'] = account['username']
            session['doctor_email'] = account['email']
            
            return jsonify({'success': True})
        
        # Check backup codes
        backup_codes = json.loads(account['backup_codes']) if account['backup_codes'] else []
        if token in backup_codes:
            # Remove used backup code
            backup_codes.remove(token)
            cursor.execute("""
                UPDATE doctor_accounts 
                SET backup_codes = ?, last_login = CURRENT_TIMESTAMP 
                WHERE doctor_id = ?
            """, (json.dumps(backup_codes), doctor_id))
            conn.commit()
            conn.close()
            
            # Set session
            session.pop('doctor_2fa_pending', None)
            session['doctor_id'] = doctor_id
            session['doctor_username'] = account['username']
            session['doctor_email'] = account['email']
            
            return jsonify({'success': True, 'backup_code_used': True})
        
        conn.close()
        return jsonify({'success': False, 'message': '驗證碼錯誤'}), 401
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'驗證失敗: {str(e)}'}), 500

@doctor_portal.route('/logout')
@doctor_login_required
def logout():
    """Doctor logout"""
    session.pop('doctor_id', None)
    session.pop('doctor_username', None)
    session.pop('doctor_email', None)
    flash('您已成功登出', 'success')
    return redirect(url_for('doctor_portal.login'))

# ==================== Dashboard ====================

@doctor_portal.route('/dashboard')
@doctor_login_required
def dashboard():
    """Doctor dashboard"""
    doctor_id = session['doctor_id']
    doctor_info = get_doctor_info(doctor_id)
    
    # Get today's reservations
    conn = get_admin_db()
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM reservations
        WHERE doctor_id = ? AND reservation_date = ? AND status != 'cancelled'
    """, (doctor_id, today))
    
    today_count = cursor.fetchone()['count']
    
    # Get pending reservations
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM reservations
        WHERE doctor_id = ? AND status = 'pending'
    """, (doctor_id,))
    
    pending_count = cursor.fetchone()['count']
    
    # Get this month's stats
    this_month = datetime.now().strftime('%Y-%m')
    
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM reservations
        WHERE doctor_id = ? AND reservation_date LIKE ? AND status = 'completed'
    """, (doctor_id, f"{this_month}%"))
    
    completed_this_month = cursor.fetchone()['count']
    
    # Get average rating
    cursor.execute("""
        SELECT AVG(rating) as avg_rating, COUNT(*) as review_count
        FROM doctor_reviews
        WHERE doctor_id = ? AND is_visible = 1
    """, (doctor_id,))
    
    rating_data = cursor.fetchone()
    avg_rating = round(rating_data['avg_rating'], 1) if rating_data['avg_rating'] else 0
    review_count = rating_data['review_count']
    
    conn.close()
    
    return render_template('doctor/dashboard.html',
                         doctor=doctor_info,
                         today_count=today_count,
                         pending_count=pending_count,
                         completed_this_month=completed_this_month,
                         avg_rating=avg_rating,
                         review_count=review_count)

# ==================== Profile Management ====================

@doctor_portal.route('/profile')
@doctor_login_required
def profile():
    """Doctor profile page"""
    doctor_id = session['doctor_id']
    doctor_info = get_doctor_info(doctor_id)
    
    return render_template('doctor/profile.html', doctor=doctor_info)

@doctor_portal.route('/profile/update', methods=['POST'])
@doctor_login_required
def update_profile():
    """Update doctor profile"""
    try:
        doctor_id = session['doctor_id']
        data = request.get_json()
        
        conn = get_doctor_db()
        cursor = conn.cursor()
        
        # Update doctors table
        update_fields = []
        params = []
        
        if 'contact_numbers' in data:
            update_fields.append('contact_numbers = ?')
            params.append(data['contact_numbers'])
        
        if 'email' in data:
            update_fields.append('email = ?')
            params.append(data['email'])
        
        if 'consultation_hours' in data:
            update_fields.append('consultation_hours = ?')
            params.append(data['consultation_hours'])
        
        if 'consultation_fee' in data:
            update_fields.append('consultation_fee = ?')
            params.append(data['consultation_fee'])
        
        if 'clinic_addresses' in data:
            update_fields.append('clinic_addresses = ?')
            params.append(data['clinic_addresses'])
        
        if 'accepts_reservations' in data:
            update_fields.append('accepts_reservations = ?')
            params.append(1 if data['accepts_reservations'] else 0)
        
        if 'online_consultation' in data:
            update_fields.append('online_consultation = ?')
            params.append(1 if data['online_consultation'] else 0)
        
        if update_fields:
            params.append(doctor_id)
            cursor.execute(f"""
                UPDATE doctors 
                SET {', '.join(update_fields)}
                WHERE id = ?
            """, params)
        
        # Update doctor_accounts table
        account_fields = []
        account_params = []
        
        if 'phone' in data:
            account_fields.append('phone = ?')
            account_params.append(data['phone'])
        
        if account_fields:
            account_params.append(doctor_id)
            cursor.execute(f"""
                UPDATE doctor_accounts 
                SET {', '.join(account_fields)}
                WHERE doctor_id = ?
            """, account_params)
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '個人資料已更新'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新失敗: {str(e)}'}), 500

# ==================== Availability Management ====================

@doctor_portal.route('/availability')
@doctor_login_required
def availability():
    """Manage availability schedule"""
    doctor_id = session['doctor_id']
    
    conn = get_doctor_db()
    cursor = conn.cursor()
    
    # Get current availability
    cursor.execute("""
        SELECT * FROM doctor_availability
        WHERE doctor_id = ? AND is_active = 1
        ORDER BY day_of_week, start_time
    """, (doctor_id,))
    
    schedules = [dict(row) for row in cursor.fetchall()]
    
    # Get time off periods
    cursor.execute("""
        SELECT * FROM doctor_time_off
        WHERE doctor_id = ? AND end_date >= date('now')
        ORDER BY start_date
    """, (doctor_id,))
    
    time_off = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return render_template('doctor/availability.html', 
                         schedules=schedules, 
                         time_off=time_off)

@doctor_portal.route('/availability/add', methods=['POST'])
@doctor_login_required
def add_availability():
    """Add availability schedule"""
    try:
        doctor_id = session['doctor_id']
        data = request.get_json()
        
        conn = get_doctor_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO doctor_availability 
            (doctor_id, day_of_week, start_time, end_time, slot_duration, 
             max_patients_per_slot, location, consultation_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doctor_id,
            data['day_of_week'],
            data['start_time'],
            data['end_time'],
            data.get('slot_duration', 30),
            data.get('max_patients_per_slot', 1),
            data.get('location', ''),
            data.get('consultation_type', 'in-person')
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '時間表已添加'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'添加失敗: {str(e)}'}), 500

@doctor_portal.route('/availability/<int:schedule_id>/delete', methods=['DELETE'])
@doctor_login_required
def delete_availability(schedule_id):
    """Delete availability schedule"""
    try:
        doctor_id = session['doctor_id']
        
        conn = get_doctor_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE doctor_availability 
            SET is_active = 0 
            WHERE id = ? AND doctor_id = ?
        """, (schedule_id, doctor_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '時間表已刪除'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'刪除失敗: {str(e)}'}), 500

@doctor_portal.route('/time-off/add', methods=['POST'])
@doctor_login_required
def add_time_off():
    """Add time off period"""
    try:
        doctor_id = session['doctor_id']
        data = request.get_json()
        
        conn = get_doctor_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO doctor_time_off 
            (doctor_id, start_date, end_date, reason)
            VALUES (?, ?, ?, ?)
        """, (
            doctor_id,
            data['start_date'],
            data['end_date'],
            data.get('reason', '')
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '休假時間已添加'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'添加失敗: {str(e)}'}), 500

# ==================== Reservation Management ====================

@doctor_portal.route('/reservations')
@doctor_login_required
def reservations():
    """View and manage reservations"""
    doctor_id = session['doctor_id']
    
    # Get filter parameters
    status_filter = request.args.get('status', 'all')
    date_filter = request.args.get('date', 'all')
    
    conn = get_admin_db()
    cursor = conn.cursor()
    
    query = """
        SELECT * FROM reservations
        WHERE doctor_id = ?
    """
    params = [doctor_id]
    
    if status_filter != 'all':
        query += " AND status = ?"
        params.append(status_filter)
    
    if date_filter == 'today':
        today = datetime.now().strftime('%Y-%m-%d')
        query += " AND reservation_date = ?"
        params.append(today)
    elif date_filter == 'upcoming':
        today = datetime.now().strftime('%Y-%m-%d')
        query += " AND reservation_date >= ?"
        params.append(today)
    
    query += " ORDER BY reservation_date DESC, reservation_time DESC"
    
    cursor.execute(query, params)
    reservations_list = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return render_template('doctor/reservations.html', reservations=reservations_list)

@doctor_portal.route('/reservations/<int:reservation_id>/confirm', methods=['POST'])
@doctor_login_required
def confirm_reservation(reservation_id):
    """Confirm a reservation"""
    try:
        doctor_id = session['doctor_id']
        
        conn = get_admin_db()
        cursor = conn.cursor()
        
        # Verify reservation belongs to this doctor
        cursor.execute("""
            SELECT * FROM reservations
            WHERE id = ? AND doctor_id = ?
        """, (reservation_id, doctor_id))
        
        reservation = cursor.fetchone()
        
        if not reservation:
            conn.close()
            return jsonify({'success': False, 'message': '預約不存在'}), 404
        
        # Update status
        cursor.execute("""
            UPDATE reservations
            SET status = 'confirmed', confirmed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (reservation_id,))
        
        # Add to history
        cursor.execute("""
            INSERT INTO reservation_history
            (reservation_id, action, old_status, new_status, performed_by, performed_by_type)
            VALUES (?, 'confirmed', ?, 'confirmed', ?, 'doctor')
        """, (reservation_id, reservation['status'], session['doctor_username']))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '預約已確認'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'確認失敗: {str(e)}'}), 500

@doctor_portal.route('/reservations/<int:reservation_id>/cancel', methods=['POST'])
@doctor_login_required
def cancel_reservation(reservation_id):
    """Cancel a reservation"""
    try:
        doctor_id = session['doctor_id']
        data = request.get_json()
        reason = data.get('reason', '')
        
        conn = get_admin_db()
        cursor = conn.cursor()
        
        # Verify reservation belongs to this doctor
        cursor.execute("""
            SELECT * FROM reservations
            WHERE id = ? AND doctor_id = ?
        """, (reservation_id, doctor_id))
        
        reservation = cursor.fetchone()
        
        if not reservation:
            conn.close()
            return jsonify({'success': False, 'message': '預約不存在'}), 404
        
        # Update status
        cursor.execute("""
            UPDATE reservations
            SET status = 'cancelled', 
                cancellation_reason = ?,
                cancelled_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (reason, reservation_id))
        
        # Add to history
        cursor.execute("""
            INSERT INTO reservation_history
            (reservation_id, action, old_status, new_status, notes, performed_by, performed_by_type)
            VALUES (?, 'cancelled', ?, 'cancelled', ?, ?, 'doctor')
        """, (reservation_id, reservation['status'], reason, session['doctor_username']))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '預約已取消'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'取消失敗: {str(e)}'}), 500

@doctor_portal.route('/reservations/<int:reservation_id>/complete', methods=['POST'])
@doctor_login_required
def complete_reservation(reservation_id):
    """Mark reservation as completed"""
    try:
        doctor_id = session['doctor_id']
        data = request.get_json()
        notes = data.get('notes', '')
        
        conn = get_admin_db()
        cursor = conn.cursor()
        
        # Verify reservation belongs to this doctor
        cursor.execute("""
            SELECT * FROM reservations
            WHERE id = ? AND doctor_id = ?
        """, (reservation_id, doctor_id))
        
        reservation = cursor.fetchone()
        
        if not reservation:
            conn.close()
            return jsonify({'success': False, 'message': '預約不存在'}), 404
        
        # Update status
        cursor.execute("""
            UPDATE reservations
            SET status = 'completed',
                doctor_notes = ?,
                completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (notes, reservation_id))
        
        # Add to history
        cursor.execute("""
            INSERT INTO reservation_history
            (reservation_id, action, old_status, new_status, notes, performed_by, performed_by_type)
            VALUES (?, 'completed', ?, 'completed', ?, ?, 'doctor')
        """, (reservation_id, reservation['status'], notes, session['doctor_username']))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '預約已完成'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'完成失敗: {str(e)}'}), 500

# ==================== Reviews ====================

@doctor_portal.route('/reviews')
@doctor_login_required
def reviews():
    """View doctor reviews"""
    doctor_id = session['doctor_id']
    
    conn = get_admin_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM doctor_reviews
        WHERE doctor_id = ?
        ORDER BY created_at DESC
    """, (doctor_id,))
    
    reviews_list = [dict(row) for row in cursor.fetchall()]
    
    # Calculate stats
    if reviews_list:
        avg_rating = sum(r['rating'] for r in reviews_list) / len(reviews_list)
        rating_distribution = {i: 0 for i in range(1, 6)}
        for review in reviews_list:
            rating_distribution[review['rating']] += 1
    else:
        avg_rating = 0
        rating_distribution = {i: 0 for i in range(1, 6)}
    
    conn.close()
    
    return render_template('doctor/reviews.html',
                         reviews=reviews_list,
                         avg_rating=round(avg_rating, 1),
                         rating_distribution=rating_distribution)

# ==================== Statistics ====================

@doctor_portal.route('/statistics')
@doctor_login_required
def statistics():
    """View statistics and analytics"""
    doctor_id = session['doctor_id']
    
    conn = get_admin_db()
    cursor = conn.cursor()
    
    # Get monthly reservation stats for the past 6 months
    monthly_stats = []
    for i in range(6):
        month_date = (datetime.now() - timedelta(days=30*i)).strftime('%Y-%m')
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
            FROM reservations
            WHERE doctor_id = ? AND reservation_date LIKE ?
        """, (doctor_id, f"{month_date}%"))
        
        stats = cursor.fetchone()
        monthly_stats.append({
            'month': month_date,
            'total': stats['total'],
            'completed': stats['completed'],
            'cancelled': stats['cancelled']
        })
    
    monthly_stats.reverse()
    
    conn.close()
    
    return render_template('doctor/statistics.html', monthly_stats=monthly_stats)

# ==================== API Endpoints ====================

@doctor_portal.route('/api/notifications')
@doctor_login_required
def get_notifications():
    """Get doctor notifications"""
    doctor_id = session['doctor_id']
    
    conn = get_doctor_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM doctor_notifications
        WHERE doctor_id = ?
        ORDER BY created_at DESC
        LIMIT 50
    """, (doctor_id,))
    
    notifications = [dict(row) for row in cursor.fetchall()]
    
    # Count unread
    unread_count = sum(1 for n in notifications if not n['is_read'])
    
    conn.close()
    
    return jsonify({
        'success': True,
        'notifications': notifications,
        'unread_count': unread_count
    })

@doctor_portal.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@doctor_login_required
def mark_notification_read(notification_id):
    """Mark notification as read"""
    try:
        doctor_id = session['doctor_id']
        
        conn = get_doctor_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE doctor_notifications
            SET is_read = 1, read_at = CURRENT_TIMESTAMP
            WHERE id = ? AND doctor_id = ?
        """, (notification_id, doctor_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
