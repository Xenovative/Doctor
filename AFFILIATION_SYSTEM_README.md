# Doctor Affiliation & Reservation System

## Overview

Complete system for managing affiliated doctors and patient reservations. Allows doctors to join the platform, manage their profiles, set availability, and handle patient bookings.

---

## 🏗️ Architecture

### Database Structure

#### **doctors.db**
- `doctors` - Extended with affiliation columns
- `doctor_accounts` - Authentication for affiliated doctors
- `doctor_availability` - Weekly schedule management
- `doctor_time_off` - Exception dates (holidays, vacations)
- `doctor_notifications` - In-app notifications for doctors

#### **admin_data.db**
- `reservations` - Patient booking records
- `reservation_history` - Audit trail for all reservation changes
- `doctor_reviews` - Patient reviews and ratings

---

## 📦 Installation

### 1. Run Database Migration

```bash
python create_affiliation_system.py
```

This creates all necessary tables and indexes.

### 2. Integrate Routes into app.py

Add to your `app.py`:

```python
# Import blueprints
from doctor_portal_routes import doctor_portal
from reservation_routes import reservation_system
from admin_affiliation_routes import admin_affiliation

# Register blueprints
app.register_blueprint(doctor_portal)
app.register_blueprint(reservation_system)
app.register_blueprint(admin_affiliation)
```

### 3. Create Required Templates

Create the following template directories:
- `templates/doctor/` - Doctor portal templates
- `templates/reservations/` - Patient reservation interface
- `templates/admin/` - Admin affiliation management

---

## 🎯 Features

### For Doctors

#### Authentication
- **Login/Logout** - Secure authentication with optional 2FA
- **Password Reset** - Admin-initiated password resets
- **Session Management** - Secure session handling

#### Profile Management
- Update contact information
- Set consultation fees
- Manage clinic addresses
- Toggle online consultation availability
- Control reservation acceptance

#### Availability Management
- Set weekly recurring schedules
- Define time slots and duration
- Set max patients per slot
- Add time-off periods (vacations, holidays)
- Multiple locations support

#### Reservation Management
- View all reservations (pending, confirmed, completed)
- Confirm/cancel reservations
- Add notes to completed appointments
- Filter by date and status

#### Reviews & Ratings
- View patient reviews
- Track average rating
- Rating distribution analytics

#### Dashboard
- Today's appointments count
- Pending reservations
- Monthly completion stats
- Average rating display

### For Patients

#### Doctor Discovery
- Browse affiliated doctors
- Filter by specialty, location, consultation type
- View doctor profiles with ratings
- See available dates and time slots

#### Booking System
- Select doctor and date
- Choose available time slot
- Provide symptoms and medical history
- Receive confirmation code

#### Reservation Management
- Check reservation status
- Cancel reservations
- Submit reviews after completion

### For Admins

#### Affiliation Management
- Review affiliation requests
- Approve/reject applications
- Suspend/reactivate affiliations
- Verify doctor credentials

#### Account Management
- Create doctor accounts
- Reset passwords
- Toggle account status
- Manage permissions

#### Reservation Oversight
- View all reservations
- Filter by doctor, date, status
- Access complete reservation history
- Monitor cancellation rates

#### Analytics
- Affiliation statistics
- Reservation trends
- Top-performing doctors
- Monthly revenue projections

---

## 🔐 Security Features

### Authentication
- SHA-256 password hashing
- TOTP-based 2FA support
- Backup codes for 2FA
- Session-based authentication
- Automatic session expiry

### Authorization
- Role-based access control
- Doctor-specific data isolation
- Admin permission levels
- Secure API endpoints

### Data Protection
- SQL injection prevention (parameterized queries)
- XSS protection
- CSRF token validation
- Secure password generation

---

## 📊 Database Schema Details

### doctors Table Extensions
```sql
is_affiliated INTEGER DEFAULT 0
affiliation_status TEXT DEFAULT 'none'  -- none/pending/approved/suspended
affiliation_date TEXT
accepts_reservations INTEGER DEFAULT 0
online_consultation INTEGER DEFAULT 0
verified_credentials INTEGER DEFAULT 0
```

### doctor_accounts
```sql
id INTEGER PRIMARY KEY
doctor_id INTEGER UNIQUE (FK to doctors)
username TEXT UNIQUE
password_hash TEXT
email TEXT UNIQUE
phone TEXT
totp_enabled INTEGER
totp_secret TEXT
backup_codes TEXT
is_active INTEGER
email_verified INTEGER
phone_verified INTEGER
last_login DATETIME
created_at DATETIME
```

### doctor_availability
```sql
id INTEGER PRIMARY KEY
doctor_id INTEGER (FK to doctors)
day_of_week INTEGER  -- 0=Monday, 6=Sunday
start_time TEXT      -- HH:MM format
end_time TEXT        -- HH:MM format
slot_duration INTEGER DEFAULT 30  -- minutes
max_patients_per_slot INTEGER DEFAULT 1
is_active INTEGER
location TEXT
consultation_type TEXT  -- in-person/online
```

### reservations
```sql
id INTEGER PRIMARY KEY
doctor_id INTEGER
patient_name TEXT
patient_phone TEXT
patient_email TEXT
patient_age INTEGER
patient_gender TEXT
reservation_date TEXT
reservation_time TEXT
consultation_type TEXT
symptoms TEXT
chronic_conditions TEXT
query_id INTEGER (FK to user_queries)
status TEXT  -- pending/confirmed/cancelled/completed
confirmation_code TEXT UNIQUE
doctor_notes TEXT
cancellation_reason TEXT
reminder_sent INTEGER
created_at DATETIME
confirmed_at DATETIME
cancelled_at DATETIME
completed_at DATETIME
```

### doctor_reviews
```sql
id INTEGER PRIMARY KEY
doctor_id INTEGER
reservation_id INTEGER (FK to reservations)
patient_name TEXT
rating INTEGER CHECK(1-5)
review_text TEXT
is_verified INTEGER
is_visible INTEGER
admin_response TEXT
created_at DATETIME
```

---

## 🔄 Workflows

### Doctor Affiliation Process

1. **Application Submission**
   - Doctor submits affiliation request
   - Status set to 'pending'
   - Admin receives notification

2. **Admin Review**
   - Verify credentials
   - Check qualifications
   - Approve or reject

3. **Account Creation**
   - System creates doctor account
   - Generates temporary password
   - Sends credentials via notification

4. **Doctor Onboarding**
   - First login with temp password
   - Update profile information
   - Set availability schedule
   - Enable reservations

### Reservation Process

1. **Patient Booking**
   - Browse available doctors
   - Select date and time slot
   - Provide medical information
   - Receive confirmation code

2. **Doctor Confirmation**
   - Doctor receives notification
   - Reviews patient information
   - Confirms or reschedules

3. **Appointment**
   - Reminder sent (optional)
   - Patient attends appointment
   - Doctor marks as completed

4. **Post-Appointment**
   - Patient can submit review
   - Doctor can add notes
   - Record archived

### Cancellation Process

1. **Initiation**
   - Patient or doctor initiates
   - Reason provided
   - Status updated

2. **Notification**
   - Other party notified
   - Slot becomes available
   - History recorded

3. **Follow-up**
   - Cancellation stats tracked
   - Patterns analyzed
   - Improvements suggested

---

## 🛠️ API Endpoints

### Doctor Portal (`/doctor`)

#### Authentication
- `POST /doctor/login` - Doctor login
- `POST /doctor/login/2fa` - 2FA verification
- `GET /doctor/logout` - Logout

#### Dashboard
- `GET /doctor/dashboard` - Main dashboard

#### Profile
- `GET /doctor/profile` - View profile
- `POST /doctor/profile/update` - Update profile

#### Availability
- `GET /doctor/availability` - View schedules
- `POST /doctor/availability/add` - Add schedule
- `DELETE /doctor/availability/<id>/delete` - Remove schedule
- `POST /doctor/time-off/add` - Add time off

#### Reservations
- `GET /doctor/reservations` - List reservations
- `POST /doctor/reservations/<id>/confirm` - Confirm
- `POST /doctor/reservations/<id>/cancel` - Cancel
- `POST /doctor/reservations/<id>/complete` - Mark complete

#### Reviews
- `GET /doctor/reviews` - View reviews

#### Statistics
- `GET /doctor/statistics` - Analytics

#### Notifications
- `GET /doctor/api/notifications` - Get notifications
- `POST /doctor/api/notifications/<id>/read` - Mark read

### Reservation System (`/reservations`)

#### Discovery
- `GET /reservations/available-doctors` - List doctors
- `GET /reservations/doctor/<id>/info` - Doctor details
- `GET /reservations/doctor/<id>/available-dates` - Available dates
- `GET /reservations/doctor/<id>/available-slots` - Time slots

#### Booking
- `POST /reservations/book` - Create reservation
- `GET /reservations/check/<code>` - Check status
- `POST /reservations/cancel/<code>` - Cancel reservation
- `POST /reservations/review` - Submit review

### Admin Affiliation (`/admin/affiliation`)

#### Management
- `GET /admin/affiliation/requests` - View requests
- `POST /admin/affiliation/approve/<id>` - Approve
- `POST /admin/affiliation/reject/<id>` - Reject
- `POST /admin/affiliation/suspend/<id>` - Suspend
- `POST /admin/affiliation/reactivate/<id>` - Reactivate

#### Reservations
- `GET /admin/affiliation/reservations` - All reservations
- `GET /admin/affiliation/reservations/<id>` - Details

#### Statistics
- `GET /admin/affiliation/statistics` - Analytics

#### Accounts
- `GET /admin/affiliation/doctor-accounts` - List accounts
- `POST /admin/affiliation/doctor-accounts/<id>/reset-password` - Reset
- `POST /admin/affiliation/doctor-accounts/<id>/toggle-active` - Toggle

---

## 🎨 Frontend Integration

### Update Doctor Listings

Modify existing doctor display to show affiliation status:

```javascript
// In script.js or relevant file
function displayDoctor(doctor) {
    let badges = '';
    
    if (doctor.is_affiliated) {
        badges += '<span class="badge bg-success">認證醫生</span> ';
    }
    
    if (doctor.accepts_reservations) {
        badges += '<span class="badge bg-primary">接受預約</span> ';
    }
    
    if (doctor.online_consultation) {
        badges += '<span class="badge bg-info">線上諮詢</span> ';
    }
    
    // Add booking button for affiliated doctors
    let bookingButton = '';
    if (doctor.is_affiliated && doctor.accepts_reservations) {
        bookingButton = `
            <button class="btn btn-primary btn-sm" 
                    onclick="openBookingModal(${doctor.id})">
                立即預約
            </button>
        `;
    }
    
    // ... rest of display logic
}
```

### Booking Modal

```html
<!-- Add to index.html or relevant template -->
<div class="modal fade" id="bookingModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">預約醫生</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div id="booking-step-1">
                    <!-- Doctor info and date selection -->
                </div>
                <div id="booking-step-2" style="display:none;">
                    <!-- Time slot selection -->
                </div>
                <div id="booking-step-3" style="display:none;">
                    <!-- Patient information form -->
                </div>
                <div id="booking-confirmation" style="display:none;">
                    <!-- Confirmation with code -->
                </div>
            </div>
        </div>
    </div>
</div>
```

---

## 📱 Responsive Design

All templates should be mobile-responsive:

```css
/* Add to style.css */
.doctor-card {
    transition: transform 0.2s;
}

.doctor-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.affiliation-badge {
    position: absolute;
    top: 10px;
    right: 10px;
}

@media (max-width: 768px) {
    .booking-modal {
        padding: 15px;
    }
    
    .time-slot-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}
```

---

## 🔔 Notification System

### Types of Notifications

1. **For Doctors**
   - New reservation
   - Reservation cancelled
   - New review
   - Affiliation status change
   - Password reset

2. **For Patients** (via email/SMS - to be implemented)
   - Booking confirmation
   - Appointment reminder
   - Cancellation notice
   - Review request

### Implementation

```python
# Example notification sender
def send_notification_to_doctor(doctor_id, type, title, message, related_id=None):
    conn = get_doctor_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO doctor_notifications
        (doctor_id, notification_type, title, message, related_id)
        VALUES (?, ?, ?, ?, ?)
    """, (doctor_id, type, title, message, related_id))
    
    conn.commit()
    conn.close()
```

---

## 📈 Analytics & Reporting

### Key Metrics

1. **Affiliation Metrics**
   - Total affiliated doctors
   - Pending applications
   - Approval rate
   - Active vs suspended

2. **Reservation Metrics**
   - Total bookings
   - Completion rate
   - Cancellation rate
   - Average rating

3. **Doctor Performance**
   - Bookings per doctor
   - Average rating
   - Response time
   - Cancellation rate

4. **Revenue Tracking** (future)
   - Consultation fees
   - Commission calculations
   - Payment processing

---

## 🚀 Future Enhancements

### Phase 2
- [ ] Email/SMS notifications
- [ ] Payment integration
- [ ] Video consultation support
- [ ] Prescription management
- [ ] Medical records integration

### Phase 3
- [ ] Mobile app (iOS/Android)
- [ ] AI-powered doctor matching
- [ ] Telemedicine features
- [ ] Insurance integration
- [ ] Multi-language support

### Phase 4
- [ ] Advanced analytics dashboard
- [ ] Revenue sharing system
- [ ] Referral program
- [ ] Patient loyalty program
- [ ] API for third-party integrations

---

## 🐛 Troubleshooting

### Common Issues

**Issue**: Doctor can't login after approval
- Check `is_active` in `doctor_accounts`
- Verify `affiliation_status` is 'approved'
- Check password hash generation

**Issue**: No available slots showing
- Verify `doctor_availability` has active schedules
- Check `day_of_week` matches (0=Monday)
- Ensure no overlapping `doctor_time_off`

**Issue**: Reservations not appearing
- Check database connection
- Verify `doctor_id` matches
- Check date format (YYYY-MM-DD)

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 📞 Support

For issues or questions:
1. Check this documentation
2. Review error logs
3. Check database integrity
4. Contact system administrator

---

## 📄 License

Proprietary - Doctor AI Application
© 2024 All Rights Reserved

---

## 🔄 Version History

### v1.0.0 (Current)
- Initial affiliation system
- Basic reservation management
- Doctor portal
- Admin management tools
- Review system

---

## ✅ Checklist for Deployment

- [ ] Run database migration
- [ ] Register blueprints in app.py
- [ ] Create template directories
- [ ] Update frontend doctor listings
- [ ] Add booking modal
- [ ] Configure email/SMS (optional)
- [ ] Test doctor registration flow
- [ ] Test booking flow
- [ ] Test admin approval process
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Update documentation
- [ ] Train admin users
- [ ] Soft launch with test doctors
- [ ] Monitor for issues
- [ ] Full production launch

---

**Last Updated**: 2024
**Maintained By**: Development Team
