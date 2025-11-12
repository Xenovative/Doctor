"""
Patient Reservation Routes
Handles patient-facing reservation system for booking appointments with affiliated doctors
"""

from flask import Blueprint, render_template, request, jsonify, session
import sqlite3
from datetime import datetime, timedelta
import secrets
import json

reservation_system = Blueprint('reservation_system', __name__, url_prefix='/reservations')

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

def generate_confirmation_code() -> str:
    """Generate unique confirmation code"""
    return secrets.token_urlsafe(8).upper()

def get_available_slots(doctor_id: int, date: str) -> list:
    """Get available time slots for a doctor on a specific date"""
    conn_doctors = get_doctor_db()
    conn_admin = get_admin_db()
    
    cursor_doctors = conn_doctors.cursor()
    cursor_admin = conn_admin.cursor()
    
    # Get day of week (0 = Monday, 6 = Sunday)
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    day_of_week = date_obj.weekday()
    
    # Check if doctor has time off on this date
    cursor_doctors.execute("""
        SELECT * FROM doctor_time_off
        WHERE doctor_id = ? 
        AND ? BETWEEN start_date AND end_date
    """, (doctor_id, date))
    
    if cursor_doctors.fetchone():
        conn_doctors.close()
        conn_admin.close()
        return []
    
    # Get doctor's availability for this day
    cursor_doctors.execute("""
        SELECT * FROM doctor_availability
        WHERE doctor_id = ? AND day_of_week = ? AND is_active = 1
    """, (doctor_id, day_of_week))
    
    schedules = cursor_doctors.fetchall()
    
    if not schedules:
        conn_doctors.close()
        conn_admin.close()
        return []
    
    # Get existing reservations for this date
    cursor_admin.execute("""
        SELECT reservation_time, COUNT(*) as count
        FROM reservations
        WHERE doctor_id = ? 
        AND reservation_date = ?
        AND status IN ('pending', 'confirmed')
        GROUP BY reservation_time
    """, (doctor_id, date))
    
    existing_reservations = {row['reservation_time']: row['count'] for row in cursor_admin.fetchall()}
    
    # Generate available slots
    available_slots = []
    
    for schedule in schedules:
        start_time = datetime.strptime(schedule['start_time'], '%H:%M')
        end_time = datetime.strptime(schedule['end_time'], '%H:%M')
        slot_duration = schedule['slot_duration']
        max_patients = schedule['max_patients_per_slot']
        
        current_time = start_time
        while current_time < end_time:
            time_str = current_time.strftime('%H:%M')
            booked_count = existing_reservations.get(time_str, 0)
            
            if booked_count < max_patients:
                available_slots.append({
                    'time': time_str,
                    'available': max_patients - booked_count,
                    'location': schedule['location'],
                    'consultation_type': schedule['consultation_type']
                })
            
            current_time += timedelta(minutes=slot_duration)
    
    conn_doctors.close()
    conn_admin.close()
    
    return available_slots

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

def format_reservation_whatsapp_message(reservation_data: dict, doctor_data: dict) -> str:
    """Format WhatsApp message for reservation notification to doctor"""
    message = f"""🏥 新預約通知 - Doctor AI

尊敬的{doctor_data.get('name_zh', '醫生')}：

您有一個新的預約！

👤 患者資料：
• 姓名：{reservation_data['patient_name']}
• 電話：{reservation_data['patient_phone']}
• 年齡：{reservation_data.get('patient_age', 'N/A')}歲
• 性別：{reservation_data.get('patient_gender', 'N/A')}

📅 預約時間：
• 日期：{reservation_data['reservation_date']}
• 時間：{reservation_data['reservation_time']}
• 類型：{'線上諮詢' if reservation_data['consultation_type'] == 'online' else '診所面診'}

💬 症狀描述：
{reservation_data.get('symptoms', '無')}

{'🏥 長期病患：' + reservation_data.get('chronic_conditions', '') if reservation_data.get('chronic_conditions') else ''}

請登入醫生門戶確認預約：
https://doctor-ai.io/doctor/login

---
Doctor AI.io 醫療配對系統"""
    
    return message

# ==================== Public Routes ====================

@reservation_system.route('/available-doctors')
def available_doctors():
    """Get list of doctors accepting reservations"""
    try:
        specialty = request.args.get('specialty', '')
        location = request.args.get('location', '')
        consultation_type = request.args.get('consultation_type', '')
        
        conn = get_doctor_db()
        cursor = conn.cursor()
        
        query = """
            SELECT d.*, 
                   (SELECT AVG(rating) FROM doctor_reviews WHERE doctor_id = d.id AND is_visible = 1) as avg_rating,
                   (SELECT COUNT(*) FROM doctor_reviews WHERE doctor_id = d.id AND is_visible = 1) as review_count
            FROM doctors d
            WHERE d.is_affiliated = 1 
            AND d.affiliation_status = 'approved'
            AND d.accepts_reservations = 1
        """
        
        params = []
        
        if specialty:
            query += " AND (d.specialty_zh LIKE ? OR d.specialty_en LIKE ?)"
            params.extend([f'%{specialty}%', f'%{specialty}%'])
        
        if location:
            query += " AND d.clinic_addresses LIKE ?"
            params.append(f'%{location}%')
        
        if consultation_type == 'online':
            query += " AND d.online_consultation = 1"
        
        query += " ORDER BY d.priority_flag DESC, avg_rating DESC"
        
        cursor.execute(query, params)
        doctors = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({'success': True, 'doctors': doctors})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@reservation_system.route('/doctor/<int:doctor_id>/info')
def doctor_info(doctor_id):
    """Get detailed doctor information"""
    try:
        conn_doctors = get_doctor_db()
        conn_admin = get_admin_db()
        
        cursor_doctors = conn_doctors.cursor()
        cursor_admin = conn_admin.cursor()
        
        # Get doctor info
        cursor_doctors.execute("""
            SELECT * FROM doctors
            WHERE id = ? AND is_affiliated = 1 AND accepts_reservations = 1
        """, (doctor_id,))
        
        doctor = cursor_doctors.fetchone()
        
        if not doctor:
            conn_doctors.close()
            conn_admin.close()
            return jsonify({'success': False, 'message': '醫生不存在或不接受預約'}), 404
        
        doctor_dict = dict(doctor)
        
        # Get availability schedule
        cursor_doctors.execute("""
            SELECT * FROM doctor_availability
            WHERE doctor_id = ? AND is_active = 1
            ORDER BY day_of_week, start_time
        """, (doctor_id,))
        
        doctor_dict['availability'] = [dict(row) for row in cursor_doctors.fetchall()]
        
        # Get reviews
        cursor_admin.execute("""
            SELECT rating, review_text, patient_name, created_at
            FROM doctor_reviews
            WHERE doctor_id = ? AND is_visible = 1
            ORDER BY created_at DESC
            LIMIT 10
        """, (doctor_id,))
        
        doctor_dict['reviews'] = [dict(row) for row in cursor_admin.fetchall()]
        
        # Calculate rating stats
        cursor_admin.execute("""
            SELECT 
                AVG(rating) as avg_rating,
                COUNT(*) as review_count
            FROM doctor_reviews
            WHERE doctor_id = ? AND is_visible = 1
        """, (doctor_id,))
        
        rating_stats = cursor_admin.fetchone()
        doctor_dict['avg_rating'] = round(rating_stats['avg_rating'], 1) if rating_stats['avg_rating'] else 0
        doctor_dict['review_count'] = rating_stats['review_count']
        
        conn_doctors.close()
        conn_admin.close()
        
        return jsonify({'success': True, 'doctor': doctor_dict})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@reservation_system.route('/doctor/<int:doctor_id>/available-dates')
def available_dates(doctor_id):
    """Get available dates for a doctor (next 30 days)"""
    try:
        conn = get_doctor_db()
        cursor = conn.cursor()
        
        # Get doctor's availability days
        cursor.execute("""
            SELECT DISTINCT day_of_week
            FROM doctor_availability
            WHERE doctor_id = ? AND is_active = 1
        """, (doctor_id,))
        
        available_days = [row['day_of_week'] for row in cursor.fetchall()]
        
        if not available_days:
            conn.close()
            return jsonify({'success': True, 'dates': []})
        
        # Get time off periods
        cursor.execute("""
            SELECT start_date, end_date
            FROM doctor_time_off
            WHERE doctor_id = ?
            AND end_date >= date('now')
        """, (doctor_id,))
        
        time_off_periods = [(row['start_date'], row['end_date']) for row in cursor.fetchall()]
        
        conn.close()
        
        # Generate available dates for next 30 days
        available_dates_list = []
        today = datetime.now().date()
        
        for i in range(30):
            check_date = today + timedelta(days=i)
            day_of_week = check_date.weekday()
            
            # Check if this day is in doctor's schedule
            if day_of_week not in available_days:
                continue
            
            # Check if this date is in time off period
            date_str = check_date.strftime('%Y-%m-%d')
            is_time_off = False
            
            for start, end in time_off_periods:
                if start <= date_str <= end:
                    is_time_off = True
                    break
            
            if not is_time_off:
                available_dates_list.append(date_str)
        
        return jsonify({'success': True, 'dates': available_dates_list})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@reservation_system.route('/doctor/<int:doctor_id>/available-slots')
def available_slots(doctor_id):
    """Get available time slots for a specific date"""
    try:
        date = request.args.get('date')
        
        if not date:
            return jsonify({'success': False, 'message': '請提供日期'}), 400
        
        # Validate date format
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'success': False, 'message': '日期格式錯誤'}), 400
        
        slots = get_available_slots(doctor_id, date)
        
        return jsonify({'success': True, 'slots': slots})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@reservation_system.route('/book', methods=['POST'])
def book_reservation():
    """Book a reservation"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['doctor_id', 'patient_name', 'patient_phone', 
                          'reservation_date', 'reservation_time']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'缺少必填字段: {field}'}), 400
        
        doctor_id = data['doctor_id']
        reservation_date = data['reservation_date']
        reservation_time = data['reservation_time']
        
        # Check if slot is still available
        slots = get_available_slots(doctor_id, reservation_date)
        slot_available = any(s['time'] == reservation_time and s['available'] > 0 for s in slots)
        
        if not slot_available:
            return jsonify({'success': False, 'message': '該時段已被預約'}), 400
        
        # Create reservation
        conn = get_admin_db()
        cursor = conn.cursor()
        
        confirmation_code = generate_confirmation_code()
        
        cursor.execute("""
            INSERT INTO reservations
            (doctor_id, patient_name, patient_phone, patient_email, patient_age, 
             patient_gender, reservation_date, reservation_time, consultation_type,
             symptoms, chronic_conditions, query_id, confirmation_code, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        """, (
            doctor_id,
            data['patient_name'],
            data['patient_phone'],
            data.get('patient_email', ''),
            data.get('patient_age'),
            data.get('patient_gender', ''),
            reservation_date,
            reservation_time,
            data.get('consultation_type', 'in-person'),
            data.get('symptoms', ''),
            data.get('chronic_conditions', ''),
            data.get('query_id'),
            confirmation_code
        ))
        
        reservation_id = cursor.lastrowid
        
        # Add to history
        cursor.execute("""
            INSERT INTO reservation_history
            (reservation_id, action, new_status, performed_by, performed_by_type)
            VALUES (?, 'created', 'pending', ?, 'patient')
        """, (reservation_id, data['patient_name']))
        
        conn.commit()
        conn.close()
        
        # Send notification to doctor
        send_notification_to_doctor(
            doctor_id,
            'new_reservation',
            '新預約',
            f'{data["patient_name"]} 預約了 {reservation_date} {reservation_time}',
            reservation_id
        )
        
        # Get doctor info for WhatsApp notification
        conn_doctors = get_doctor_db()
        cursor_doctors = conn_doctors.cursor()
        cursor_doctors.execute("SELECT * FROM doctors WHERE id = ?", (doctor_id,))
        doctor_info = cursor_doctors.fetchone()
        
        # Send WhatsApp notification if doctor has contact number
        if doctor_info and doctor_info['contact_numbers']:
            try:
                from urllib.parse import quote
                reservation_dict = {
                    'patient_name': data['patient_name'],
                    'patient_phone': data['patient_phone'],
                    'patient_age': data.get('patient_age'),
                    'patient_gender': data.get('patient_gender'),
                    'reservation_date': reservation_date,
                    'reservation_time': reservation_time,
                    'consultation_type': data.get('consultation_type', 'in-person'),
                    'symptoms': data.get('symptoms', ''),
                    'chronic_conditions': data.get('chronic_conditions', '')
                }
                doctor_dict = dict(doctor_info)
                
                whatsapp_message = format_reservation_whatsapp_message(reservation_dict, doctor_dict)
                # Note: WhatsApp URL generation would be handled by frontend
                print(f"WhatsApp notification prepared for doctor {doctor_id}")
            except Exception as e:
                print(f"Error preparing WhatsApp notification: {e}")
        
        conn_doctors.close()
        
        return jsonify({
            'success': True,
            'message': '預約成功',
            'reservation_id': reservation_id,
            'confirmation_code': confirmation_code
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'預約失敗: {str(e)}'}), 500

@reservation_system.route('/check/<confirmation_code>')
def check_reservation(confirmation_code):
    """Check reservation status by confirmation code"""
    try:
        conn = get_admin_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT r.*, d.name_zh, d.specialty_zh, d.clinic_addresses, d.contact_numbers
            FROM reservations r
            JOIN doctors d ON r.doctor_id = d.id
            WHERE r.confirmation_code = ?
        """, (confirmation_code,))
        
        reservation = cursor.fetchone()
        
        if not reservation:
            conn.close()
            return jsonify({'success': False, 'message': '找不到預約記錄'}), 404
        
        reservation_dict = dict(reservation)
        
        # Get history
        cursor.execute("""
            SELECT * FROM reservation_history
            WHERE reservation_id = ?
            ORDER BY created_at DESC
        """, (reservation_dict['id'],))
        
        reservation_dict['history'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({'success': True, 'reservation': reservation_dict})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@reservation_system.route('/cancel/<confirmation_code>', methods=['POST'])
def cancel_reservation_by_code(confirmation_code):
    """Cancel reservation by confirmation code"""
    try:
        data = request.get_json()
        reason = data.get('reason', '患者取消')
        
        conn = get_admin_db()
        cursor = conn.cursor()
        
        # Get reservation
        cursor.execute("""
            SELECT * FROM reservations
            WHERE confirmation_code = ?
        """, (confirmation_code,))
        
        reservation = cursor.fetchone()
        
        if not reservation:
            conn.close()
            return jsonify({'success': False, 'message': '找不到預約記錄'}), 404
        
        if reservation['status'] == 'cancelled':
            conn.close()
            return jsonify({'success': False, 'message': '預約已被取消'}), 400
        
        if reservation['status'] == 'completed':
            conn.close()
            return jsonify({'success': False, 'message': '已完成的預約無法取消'}), 400
        
        # Update status
        cursor.execute("""
            UPDATE reservations
            SET status = 'cancelled',
                cancellation_reason = ?,
                cancelled_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (reason, reservation['id']))
        
        # Add to history
        cursor.execute("""
            INSERT INTO reservation_history
            (reservation_id, action, old_status, new_status, notes, performed_by, performed_by_type)
            VALUES (?, 'cancelled', ?, 'cancelled', ?, ?, 'patient')
        """, (reservation['id'], reservation['status'], reason, reservation['patient_name']))
        
        conn.commit()
        conn.close()
        
        # Notify doctor
        send_notification_to_doctor(
            reservation['doctor_id'],
            'reservation_cancelled',
            '預約取消',
            f'{reservation["patient_name"]} 取消了 {reservation["reservation_date"]} {reservation["reservation_time"]} 的預約',
            reservation['id']
        )
        
        return jsonify({'success': True, 'message': '預約已取消'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'取消失敗: {str(e)}'}), 500

@reservation_system.route('/review', methods=['POST'])
def submit_review():
    """Submit a review for a completed reservation"""
    try:
        data = request.get_json()
        
        required_fields = ['confirmation_code', 'rating']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'缺少必填字段: {field}'}), 400
        
        conn = get_admin_db()
        cursor = conn.cursor()
        
        # Get reservation
        cursor.execute("""
            SELECT * FROM reservations
            WHERE confirmation_code = ?
        """, (data['confirmation_code'],))
        
        reservation = cursor.fetchone()
        
        if not reservation:
            conn.close()
            return jsonify({'success': False, 'message': '找不到預約記錄'}), 404
        
        if reservation['status'] != 'completed':
            conn.close()
            return jsonify({'success': False, 'message': '只能評價已完成的預約'}), 400
        
        # Check if already reviewed
        cursor.execute("""
            SELECT * FROM doctor_reviews
            WHERE reservation_id = ?
        """, (reservation['id'],))
        
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': '您已經評價過此預約'}), 400
        
        # Create review
        cursor.execute("""
            INSERT INTO doctor_reviews
            (doctor_id, reservation_id, patient_name, rating, review_text, is_verified)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (
            reservation['doctor_id'],
            reservation['id'],
            reservation['patient_name'],
            data['rating'],
            data.get('review_text', '')
        ))
        
        conn.commit()
        conn.close()
        
        # Notify doctor
        send_notification_to_doctor(
            reservation['doctor_id'],
            'new_review',
            '新評價',
            f'{reservation["patient_name"]} 給了您 {data["rating"]} 星評價',
            None
        )
        
        return jsonify({'success': True, 'message': '評價已提交'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'提交失敗: {str(e)}'}), 500
