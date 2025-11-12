"""
Admin Affiliation Management Routes
Handles admin panel routes for managing doctor affiliations and reservations
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import hashlib
import secrets
import json
from datetime import datetime
from functools import wraps

admin_affiliation = Blueprint('admin_affiliation', __name__, url_prefix='/admin/affiliation')

# ==================== Helper Functions ====================

def get_doctor_db():
    """Get connection to doctors.db"""
    conn = sqlite3.connect('doctors.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_admin_db():
    """Get connection to admin_data.db"""
    conn = sqlite3.connect('admin_data.db')
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_random_password(length: int = 12) -> str:
    """Generate random password"""
    return secrets.token_urlsafe(length)

def require_admin(f):
    """Decorator to require admin login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== Affiliation Management ====================

@admin_affiliation.route('/requests')
@require_admin
def affiliation_requests():
    """View pending affiliation requests"""
    try:
        conn = get_doctor_db()
        cursor = conn.cursor()
        
        # Get pending requests
        cursor.execute("""
            SELECT d.*, da.email, da.phone, da.created_at
            FROM doctors d
            LEFT JOIN doctor_accounts da ON d.id = da.doctor_id
            WHERE d.affiliation_status = 'pending'
            ORDER BY da.created_at DESC
        """)
        
        pending_requests = [dict(row) for row in cursor.fetchall()]
        
        # Get approved affiliations
        cursor.execute("""
            SELECT d.*, da.email, da.phone, d.affiliation_date
            FROM doctors d
            LEFT JOIN doctor_accounts da ON d.id = da.doctor_id
            WHERE d.affiliation_status = 'approved'
            ORDER BY d.affiliation_date DESC
        """)
        
        approved_affiliations = [dict(row) for row in cursor.fetchall()]
        
        # Get suspended affiliations
        cursor.execute("""
            SELECT d.*, da.email, da.phone
            FROM doctors d
            LEFT JOIN doctor_accounts da ON d.id = da.doctor_id
            WHERE d.affiliation_status = 'suspended'
            ORDER BY d.name_zh
        """)
        
        suspended_affiliations = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return render_template('admin/affiliation_requests.html',
                             pending_requests=pending_requests,
                             approved_affiliations=approved_affiliations,
                             suspended_affiliations=suspended_affiliations)
        
    except Exception as e:
        return f"Error: {str(e)}", 500

@admin_affiliation.route('/approve/<int:doctor_id>', methods=['POST'])
@require_admin
def approve_affiliation(doctor_id):
    """Approve doctor affiliation"""
    try:
        conn = get_doctor_db()
        cursor = conn.cursor()
        
        # Update doctor status
        cursor.execute("""
            UPDATE doctors
            SET is_affiliated = 1,
                affiliation_status = 'approved',
                affiliation_date = CURRENT_TIMESTAMP,
                verified_credentials = 1
            WHERE id = ?
        """, (doctor_id,))
        
        # Check if account exists
        cursor.execute("""
            SELECT * FROM doctor_accounts WHERE doctor_id = ?
        """, (doctor_id,))
        
        account = cursor.fetchone()
        
        if not account:
            # Create account if doesn't exist
            cursor.execute("""
                SELECT email, contact_numbers FROM doctors WHERE id = ?
            """, (doctor_id,))
            
            doctor = cursor.fetchone()
            
            if doctor and doctor['email']:
                # Generate temporary password
                temp_password = generate_random_password()
                password_hash = hash_password(temp_password)
                
                # Create username from email
                username = doctor['email'].split('@')[0]
                
                cursor.execute("""
                    INSERT INTO doctor_accounts
                    (doctor_id, username, password_hash, email, phone, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (doctor_id, username, password_hash, doctor['email'], doctor['contact_numbers']))
                
                # Send notification
                send_notification_to_doctor(
                    doctor_id,
                    'affiliation_approved',
                    '加盟申請已批准',
                    f'您的加盟申請已獲批准。臨時密碼: {temp_password}',
                    None
                )
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '加盟申請已批准'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'批准失敗: {str(e)}'}), 500

@admin_affiliation.route('/reject/<int:doctor_id>', methods=['POST'])
@require_admin
def reject_affiliation(doctor_id):
    """Reject doctor affiliation"""
    try:
        data = request.get_json()
        reason = data.get('reason', '')
        
        conn = get_doctor_db()
        cursor = conn.cursor()
        
        # Update doctor status
        cursor.execute("""
            UPDATE doctors
            SET affiliation_status = 'none'
            WHERE id = ?
        """, (doctor_id,))
        
        # Send notification
        send_notification_to_doctor(
            doctor_id,
            'affiliation_rejected',
            '加盟申請被拒絕',
            f'您的加盟申請未獲批准。原因: {reason}',
            None
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '加盟申請已拒絕'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'拒絕失敗: {str(e)}'}), 500

@admin_affiliation.route('/suspend/<int:doctor_id>', methods=['POST'])
@require_admin
def suspend_affiliation(doctor_id):
    """Suspend doctor affiliation"""
    try:
        data = request.get_json()
        reason = data.get('reason', '')
        
        conn = get_doctor_db()
        cursor = conn.cursor()
        
        # Update doctor status
        cursor.execute("""
            UPDATE doctors
            SET affiliation_status = 'suspended',
                accepts_reservations = 0
            WHERE id = ?
        """, (doctor_id,))
        
        # Deactivate account
        cursor.execute("""
            UPDATE doctor_accounts
            SET is_active = 0
            WHERE doctor_id = ?
        """, (doctor_id,))
        
        # Send notification
        send_notification_to_doctor(
            doctor_id,
            'affiliation_suspended',
            '加盟已暫停',
            f'您的加盟已被暫停。原因: {reason}',
            None
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '加盟已暫停'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'暫停失敗: {str(e)}'}), 500

@admin_affiliation.route('/reactivate/<int:doctor_id>', methods=['POST'])
@require_admin
def reactivate_affiliation(doctor_id):
    """Reactivate suspended affiliation"""
    try:
        conn = get_doctor_db()
        cursor = conn.cursor()
        
        # Update doctor status
        cursor.execute("""
            UPDATE doctors
            SET affiliation_status = 'approved'
            WHERE id = ?
        """, (doctor_id,))
        
        # Reactivate account
        cursor.execute("""
            UPDATE doctor_accounts
            SET is_active = 1
            WHERE doctor_id = ?
        """, (doctor_id,))
        
        # Send notification
        send_notification_to_doctor(
            doctor_id,
            'affiliation_reactivated',
            '加盟已恢復',
            '您的加盟已恢復正常狀態',
            None
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '加盟已恢復'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'恢復失敗: {str(e)}'}), 500

# ==================== Reservation Management ====================

@admin_affiliation.route('/reservations')
@require_admin
def all_reservations():
    """View all reservations"""
    try:
        status_filter = request.args.get('status', 'all')
        doctor_filter = request.args.get('doctor_id', '')
        date_filter = request.args.get('date', '')
        
        conn_admin = get_admin_db()
        conn_doctors = get_doctor_db()
        
        cursor_admin = conn_admin.cursor()
        cursor_doctors = conn_doctors.cursor()
        
        # Build query
        query = """
            SELECT r.*, d.name_zh as doctor_name, d.specialty_zh as doctor_specialty
            FROM reservations r
            LEFT JOIN doctors d ON r.doctor_id = d.id
            WHERE 1=1
        """
        params = []
        
        if status_filter != 'all':
            query += " AND r.status = ?"
            params.append(status_filter)
        
        if doctor_filter:
            query += " AND r.doctor_id = ?"
            params.append(doctor_filter)
        
        if date_filter:
            query += " AND r.reservation_date = ?"
            params.append(date_filter)
        
        query += " ORDER BY r.reservation_date DESC, r.reservation_time DESC LIMIT 1000"
        
        cursor_admin.execute(query, params)
        reservations = [dict(row) for row in cursor_admin.fetchall()]
        
        # Get doctor list for filter
        cursor_doctors.execute("""
            SELECT id, name_zh, specialty_zh
            FROM doctors
            WHERE is_affiliated = 1
            ORDER BY name_zh
        """)
        doctors = [dict(row) for row in cursor_doctors.fetchall()]
        
        # Get statistics
        cursor_admin.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'confirmed' THEN 1 ELSE 0 END) as confirmed,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
            FROM reservations
        """)
        
        stats = dict(cursor_admin.fetchone())
        
        conn_admin.close()
        conn_doctors.close()
        
        return render_template('admin/all_reservations.html',
                             reservations=reservations,
                             doctors=doctors,
                             stats=stats)
        
    except Exception as e:
        return f"Error: {str(e)}", 500

@admin_affiliation.route('/reservations/<int:reservation_id>')
@require_admin
def reservation_details(reservation_id):
    """View reservation details"""
    try:
        conn = get_admin_db()
        cursor = conn.cursor()
        
        # Get reservation
        cursor.execute("""
            SELECT r.*, d.name_zh as doctor_name, d.specialty_zh as doctor_specialty,
                   d.contact_numbers as doctor_phone, d.email as doctor_email
            FROM reservations r
            LEFT JOIN doctors d ON r.doctor_id = d.id
            WHERE r.id = ?
        """, (reservation_id,))
        
        reservation = cursor.fetchone()
        
        if not reservation:
            conn.close()
            return "Reservation not found", 404
        
        reservation_dict = dict(reservation)
        
        # Get history
        cursor.execute("""
            SELECT * FROM reservation_history
            WHERE reservation_id = ?
            ORDER BY created_at DESC
        """, (reservation_id,))
        
        reservation_dict['history'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({'success': True, 'reservation': reservation_dict})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_affiliation.route('/statistics')
@require_admin
def affiliation_statistics():
    """View affiliation and reservation statistics"""
    try:
        conn_doctors = get_doctor_db()
        conn_admin = get_admin_db()
        
        cursor_doctors = conn_doctors.cursor()
        cursor_admin = conn_admin.cursor()
        
        # Affiliation stats
        cursor_doctors.execute("""
            SELECT 
                COUNT(*) as total_affiliated,
                SUM(CASE WHEN affiliation_status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN affiliation_status = 'approved' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN affiliation_status = 'suspended' THEN 1 ELSE 0 END) as suspended,
                SUM(CASE WHEN accepts_reservations = 1 THEN 1 ELSE 0 END) as accepting_reservations
            FROM doctors
            WHERE is_affiliated = 1 OR affiliation_status != 'none'
        """)
        
        affiliation_stats = dict(cursor_doctors.fetchone())
        
        # Reservation stats
        cursor_admin.execute("""
            SELECT 
                COUNT(*) as total_reservations,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'confirmed' THEN 1 ELSE 0 END) as confirmed,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
            FROM reservations
        """)
        
        reservation_stats = dict(cursor_admin.fetchone())
        
        # Monthly reservation trends (last 6 months)
        cursor_admin.execute("""
            SELECT 
                strftime('%Y-%m', reservation_date) as month,
                COUNT(*) as count,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM reservations
            WHERE reservation_date >= date('now', '-6 months')
            GROUP BY month
            ORDER BY month
        """)
        
        monthly_trends = [dict(row) for row in cursor_admin.fetchall()]
        
        # Top doctors by reservations
        cursor_admin.execute("""
            SELECT 
                d.name_zh,
                d.specialty_zh,
                COUNT(r.id) as reservation_count,
                AVG(dr.rating) as avg_rating
            FROM doctors d
            LEFT JOIN reservations r ON d.id = r.doctor_id
            LEFT JOIN doctor_reviews dr ON d.id = dr.doctor_id AND dr.is_visible = 1
            WHERE d.is_affiliated = 1
            GROUP BY d.id
            ORDER BY reservation_count DESC
            LIMIT 10
        """)
        
        top_doctors = [dict(row) for row in cursor_admin.fetchall()]
        
        conn_doctors.close()
        conn_admin.close()
        
        return render_template('admin/affiliation_statistics.html',
                             affiliation_stats=affiliation_stats,
                             reservation_stats=reservation_stats,
                             monthly_trends=monthly_trends,
                             top_doctors=top_doctors)
        
    except Exception as e:
        return f"Error: {str(e)}", 500

# ==================== Doctor Account Management ====================

@admin_affiliation.route('/doctor-accounts')
@require_admin
def doctor_accounts():
    """Manage doctor accounts"""
    try:
        conn = get_doctor_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT da.*, d.name_zh, d.specialty_zh, d.affiliation_status
            FROM doctor_accounts da
            LEFT JOIN doctors d ON da.doctor_id = d.id
            ORDER BY da.created_at DESC
        """)
        
        accounts = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return render_template('admin/doctor_accounts.html', accounts=accounts)
        
    except Exception as e:
        return f"Error: {str(e)}", 500

@admin_affiliation.route('/doctor-accounts/<int:account_id>/reset-password', methods=['POST'])
@require_admin
def reset_doctor_password(account_id):
    """Reset doctor account password"""
    try:
        new_password = generate_random_password()
        password_hash = hash_password(new_password)
        
        conn = get_doctor_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE doctor_accounts
            SET password_hash = ?
            WHERE id = ?
        """, (password_hash, account_id))
        
        # Get doctor info for notification
        cursor.execute("""
            SELECT doctor_id FROM doctor_accounts WHERE id = ?
        """, (account_id,))
        
        account = cursor.fetchone()
        
        if account:
            send_notification_to_doctor(
                account['doctor_id'],
                'password_reset',
                '密碼已重置',
                f'您的密碼已被管理員重置。新密碼: {new_password}',
                None
            )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '密碼已重置',
            'new_password': new_password
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'重置失敗: {str(e)}'}), 500

@admin_affiliation.route('/doctor-accounts/<int:account_id>/toggle-active', methods=['POST'])
@require_admin
def toggle_doctor_account(account_id):
    """Toggle doctor account active status"""
    try:
        conn = get_doctor_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE doctor_accounts
            SET is_active = NOT is_active
            WHERE id = ?
        """, (account_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '帳戶狀態已更新'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新失敗: {str(e)}'}), 500

# ==================== Helper Functions ====================

def send_notification_to_doctor(doctor_id: int, notification_type: str, title: str, message: str, related_id: int = None):
    """Send notification to doctor"""
    try:
        conn = get_doctor_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO doctor_notifications
            (doctor_id, notification_type, title, message, related_id)
            VALUES (?, ?, ?, ?, ?)
        """, (doctor_id, notification_type, title, message, related_id))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error sending notification: {e}")
