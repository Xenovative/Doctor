# 🚀 Quick Start Guide - Doctor Affiliation System

## ✅ What's Already Done

1. **Blueprints registered in app.py** ✅
   - `doctor_portal` - Doctor login, dashboard, reservations
   - `reservation_system` - Patient booking system
   - `admin_affiliation` - Admin management

2. **Admin navigation updated** ✅
   - Added "醫生加盟" link
   - Added "預約管理" link

3. **Templates created** ✅
   - Doctor portal templates (login, dashboard, reservations, base)
   - Admin affiliation template

4. **WhatsApp integration** ✅
   - Contact patients from reservations page
   - Automatic notifications to doctors

## 🎯 Next Steps (3 minutes)

### Step 1: Run Database Migration
```bash
python setup_affiliation_system.py
```

This will:
- Create 8 new database tables
- Add test doctor account (username: `testdoctor`, password: `test123`)
- Set up sample availability
- Create test reservation

### Step 2: Start the App
```bash
python app.py
```

You should see:
```
✅ Doctor affiliation system blueprints registered successfully
```

### Step 3: Test Doctor Portal
1. Open: http://localhost:5000/doctor/login
2. Login with:
   - Username: `testdoctor`
   - Password: `test123`
3. Explore dashboard and reservations

### Step 4: Test Admin Panel
1. Open: http://localhost:5000/admin
2. Login with your admin credentials
3. Click "醫生加盟" to manage affiliations
4. Click "預約管理" to view all reservations

## 📋 Available Routes

### Doctor Portal
- `/doctor/login` - Doctor login
- `/doctor/dashboard` - Dashboard with stats
- `/doctor/reservations` - Manage reservations
- `/doctor/profile` - Edit profile
- `/doctor/availability` - Manage schedule
- `/doctor/reviews` - View reviews
- `/doctor/statistics` - View analytics

### Patient Booking
- `/available-doctors` - Browse affiliated doctors
- `/doctor/<id>/info` - Doctor details
- `/doctor/<id>/available-dates` - Check availability
- `/book-reservation` - Book appointment
- `/reservation/<id>/status` - Check reservation status

### Admin Management
- `/admin/affiliation/requests` - Manage affiliation requests
- `/admin/affiliation/all-reservations` - View all reservations
- `/admin/affiliation/statistics` - View statistics
- `/admin/affiliation/doctor-accounts` - Manage doctor accounts

## 🔧 Troubleshooting

### Issue: Import Error
**Error**: `Could not import affiliation blueprints`

**Solution**: Make sure these files exist:
- `doctor_portal_routes.py`
- `reservation_routes.py`
- `admin_affiliation_routes.py`

### Issue: Database Error
**Error**: `no such table: doctor_accounts`

**Solution**: Run the migration:
```bash
python setup_affiliation_system.py
```

### Issue: 404 on Routes
**Error**: Routes return 404

**Solution**: Check console for blueprint registration message:
```
✅ Doctor affiliation system blueprints registered successfully
```

If not shown, check for import errors.

## 📱 WhatsApp Features

### From Doctor Portal
When viewing reservations, doctors can:
1. Click "聯絡病人" button
2. WhatsApp opens with patient's number
3. Pre-filled professional message

### Automatic Notifications
When patient books:
1. Reservation saved to database
2. In-app notification sent to doctor
3. WhatsApp message prepared (if doctor has contact number)

## 🎨 Customization

### Change Colors
Edit `templates/doctor/base.html`:
```css
--primary-color: #805ad5;  /* Your brand color */
--primary-dark: #6b46c1;
```

### Modify Messages
Edit `reservation_routes.py`:
```python
def format_reservation_whatsapp_message(reservation_data, doctor_data):
    message = f"""🏥 新預約通知 - Doctor AI
    
    尊敬的{doctor_data.get('name_zh', '醫生')}：
    
    您有一個新的預約！
    ...
    """
```

## 📊 Test Data Created

After running `setup_affiliation_system.py`:

**Test Doctor:**
- ID: (varies, check console output)
- Username: `testdoctor`
- Password: `test123`
- Name: 測試醫生
- Specialty: 全科

**Test Availability:**
- Monday-Friday: 09:00-17:00
- Consultation fee: HK$500

**Test Reservation:**
- Patient: 測試病人
- Date: Tomorrow
- Time: 10:00
- Status: Pending

## 🔐 Security Notes

- All passwords are SHA-256 hashed
- Session-based authentication
- SQL injection prevention
- CSRF protection (Flask built-in)
- Optional 2FA support for doctors

## 📚 Documentation

- **AFFILIATION_SYSTEM_README.md** - Complete system documentation
- **INTEGRATION_GUIDE.md** - Detailed integration steps
- **TEMPLATES_CREATED.md** - Template documentation
- **IMPLEMENTATION_SUMMARY.md** - Feature overview

## ✨ Features Included

### Doctor Portal
- ✅ Secure login with 2FA support
- ✅ Dashboard with real-time stats
- ✅ Reservation management
- ✅ WhatsApp patient contact
- ✅ Availability scheduling
- ✅ Profile management
- ✅ Reviews and ratings
- ✅ Analytics and statistics

### Patient Booking
- ✅ Browse affiliated doctors
- ✅ Check real-time availability
- ✅ Book appointments online
- ✅ Receive confirmation codes
- ✅ Cancel reservations
- ✅ Submit reviews

### Admin Management
- ✅ Approve/reject affiliations
- ✅ Manage doctor accounts
- ✅ View all reservations
- ✅ Monitor statistics
- ✅ Suspend/reactivate doctors

## 🎉 You're Ready!

The system is now fully integrated and ready to use. Just run the setup script and start the app!

```bash
python setup_affiliation_system.py
python app.py
```

Then visit:
- Doctor Portal: http://localhost:5000/doctor/login
- Admin Panel: http://localhost:5000/admin

---

**Need Help?** Check the detailed documentation in:
- AFFILIATION_SYSTEM_README.md
- INTEGRATION_GUIDE.md
