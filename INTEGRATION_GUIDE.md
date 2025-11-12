# Quick Integration Guide

## Step-by-Step Integration

### 1. Run Database Migration

```bash
cd c:\AIapps\Doctor
python create_affiliation_system.py
```

Expected output:
```
Creating affiliation system tables...
✓ Added is_affiliated column
✓ Added affiliation_status column
...
✅ Migration completed successfully!
```

### 2. Update app.py

Add these imports at the top of `app.py` (after existing imports):

```python
# Doctor Affiliation System
from doctor_portal_routes import doctor_portal
from reservation_routes import reservation_system
from admin_affiliation_routes import admin_affiliation
```

Add blueprint registration (after `app = Flask(__name__)` and before routes):

```python
# Register affiliation system blueprints
app.register_blueprint(doctor_portal)
app.register_blueprint(reservation_system)
app.register_blueprint(admin_affiliation)
```

### 3. Update Admin Navigation

Add to `templates/admin/dashboard.html` (or your admin base template):

```html
<!-- Add to navigation menu -->
<li class="nav-item">
    <a class="nav-link" href="{{ url_for('admin_affiliation.affiliation_requests') }}">
        <i class="fas fa-user-md me-2"></i>醫生加盟
    </a>
</li>
<li class="nav-item">
    <a class="nav-link" href="{{ url_for('admin_affiliation.all_reservations') }}">
        <i class="fas fa-calendar-check me-2"></i>預約管理
    </a>
</li>
<li class="nav-item">
    <a class="nav-link" href="{{ url_for('admin_affiliation.affiliation_statistics') }}">
        <i class="fas fa-chart-line me-2"></i>加盟統計
    </a>
</li>
```

### 4. Update Doctor Display (Frontend)

In `static/script.js` or wherever you display doctors, add affiliation badges:

```javascript
function displayDoctorCard(doctor) {
    // Existing doctor card HTML
    let html = `
        <div class="doctor-card">
            <div class="doctor-info">
                <h4>${doctor.name_zh || doctor.name}</h4>
                <p class="specialty">${doctor.specialty_zh || doctor.specialty}</p>
                
                <!-- NEW: Add affiliation badges -->
                <div class="doctor-badges">
                    ${doctor.is_affiliated ? '<span class="badge bg-success"><i class="fas fa-check-circle"></i> 認證醫生</span>' : ''}
                    ${doctor.accepts_reservations ? '<span class="badge bg-primary"><i class="fas fa-calendar"></i> 接受預約</span>' : ''}
                    ${doctor.online_consultation ? '<span class="badge bg-info"><i class="fas fa-video"></i> 線上諮詢</span>' : ''}
                </div>
                
                <!-- Existing info -->
                <p>${doctor.qualifications_zh || doctor.qualifications}</p>
                
                <!-- NEW: Add booking button for affiliated doctors -->
                ${doctor.is_affiliated && doctor.accepts_reservations ? 
                    `<button class="btn btn-primary btn-sm mt-2" onclick="openBookingModal(${doctor.id})">
                        <i class="fas fa-calendar-plus"></i> 立即預約
                    </button>` : 
                    `<a href="${doctor.profile_url}" class="btn btn-outline-primary btn-sm mt-2" target="_blank">
                        查看資料
                    </a>`
                }
            </div>
        </div>
    `;
    
    return html;
}

// NEW: Booking modal function
function openBookingModal(doctorId) {
    // Fetch doctor info and available dates
    fetch(`/reservations/doctor/${doctorId}/info`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showBookingModal(data.doctor);
            }
        });
}

function showBookingModal(doctor) {
    // Create and show booking modal
    // Implementation depends on your modal library (Bootstrap, custom, etc.)
    const modal = `
        <div class="modal fade" id="bookingModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">預約 ${doctor.name_zh}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div id="booking-calendar"></div>
                        <!-- Add calendar and time slot selection here -->
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Show modal (using Bootstrap or your modal system)
    $('#bookingModal').modal('show');
}
```

### 5. Add CSS Styles

In `static/style.css`:

```css
/* Doctor Affiliation Badges */
.doctor-badges {
    margin: 10px 0;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.doctor-badges .badge {
    padding: 6px 12px;
    font-size: 0.85rem;
    font-weight: 500;
}

.doctor-card {
    position: relative;
    transition: all 0.3s ease;
}

.doctor-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 16px rgba(0,0,0,0.1);
}

/* Affiliation indicator */
.doctor-card.affiliated::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: linear-gradient(180deg, #28a745, #20c997);
}

/* Booking button */
.btn-booking {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    color: white;
    padding: 8px 20px;
    border-radius: 20px;
    transition: all 0.3s ease;
}

.btn-booking:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

/* Booking modal */
.booking-calendar {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 10px;
    margin: 20px 0;
}

.calendar-day {
    padding: 15px;
    text-align: center;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
}

.calendar-day:hover {
    border-color: #667eea;
    background: #f8f9ff;
}

.calendar-day.selected {
    background: #667eea;
    color: white;
    border-color: #667eea;
}

.calendar-day.disabled {
    opacity: 0.3;
    cursor: not-allowed;
}

.time-slot-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin: 20px 0;
}

.time-slot {
    padding: 12px;
    text-align: center;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
}

.time-slot:hover {
    border-color: #667eea;
    background: #f8f9ff;
}

.time-slot.selected {
    background: #667eea;
    color: white;
    border-color: #667eea;
}

.time-slot.booked {
    opacity: 0.3;
    cursor: not-allowed;
}

/* Responsive */
@media (max-width: 768px) {
    .time-slot-grid {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .calendar-day {
        padding: 10px;
        font-size: 0.9rem;
    }
}
```

### 6. Create Admin Templates

Create these template files:

#### `templates/admin/affiliation_requests.html`
```html
{% extends "admin/base.html" %}

{% block content %}
<div class="container-fluid">
    <h2>醫生加盟管理</h2>
    
    <!-- Tabs for different statuses -->
    <ul class="nav nav-tabs" role="tablist">
        <li class="nav-item">
            <a class="nav-link active" data-bs-toggle="tab" href="#pending">
                待審核 <span class="badge bg-warning">{{ pending_requests|length }}</span>
            </a>
        </li>
        <li class="nav-item">
            <a class="nav-link" data-bs-toggle="tab" href="#approved">
                已批准 <span class="badge bg-success">{{ approved_affiliations|length }}</span>
            </a>
        </li>
        <li class="nav-item">
            <a class="nav-link" data-bs-toggle="tab" href="#suspended">
                已暫停 <span class="badge bg-danger">{{ suspended_affiliations|length }}</span>
            </a>
        </li>
    </ul>
    
    <div class="tab-content mt-3">
        <!-- Pending requests -->
        <div id="pending" class="tab-pane fade show active">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>醫生姓名</th>
                        <th>專科</th>
                        <th>電郵</th>
                        <th>電話</th>
                        <th>申請日期</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    {% for doctor in pending_requests %}
                    <tr>
                        <td>{{ doctor.name_zh }}</td>
                        <td>{{ doctor.specialty_zh }}</td>
                        <td>{{ doctor.email }}</td>
                        <td>{{ doctor.phone }}</td>
                        <td>{{ doctor.created_at }}</td>
                        <td>
                            <button class="btn btn-success btn-sm" onclick="approveAffiliation({{ doctor.id }})">
                                批准
                            </button>
                            <button class="btn btn-danger btn-sm" onclick="rejectAffiliation({{ doctor.id }})">
                                拒絕
                            </button>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <!-- Similar tables for approved and suspended -->
    </div>
</div>

<script>
function approveAffiliation(doctorId) {
    if (confirm('確定批准此醫生的加盟申請？')) {
        fetch(`/admin/affiliation/approve/${doctorId}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('已批准');
                location.reload();
            } else {
                alert('操作失敗: ' + data.message);
            }
        });
    }
}

function rejectAffiliation(doctorId) {
    const reason = prompt('請輸入拒絕原因：');
    if (reason) {
        fetch(`/admin/affiliation/reject/${doctorId}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({reason: reason})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('已拒絕');
                location.reload();
            } else {
                alert('操作失敗: ' + data.message);
            }
        });
    }
}
</script>
{% endblock %}
```

### 7. Create Doctor Portal Templates

#### `templates/doctor/login.html`
```html
<!DOCTYPE html>
<html lang="zh-HK">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>醫生登入 - Doctor AI</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <div class="container">
        <div class="row justify-content-center mt-5">
            <div class="col-md-6">
                <div class="card shadow">
                    <div class="card-body p-5">
                        <h2 class="text-center mb-4">
                            <i class="fas fa-user-md text-primary"></i>
                            醫生登入
                        </h2>
                        
                        <form id="loginForm">
                            <div class="mb-3">
                                <label class="form-label">用戶名</label>
                                <input type="text" class="form-control" id="username" required>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label">密碼</label>
                                <input type="password" class="form-control" id="password" required>
                            </div>
                            
                            <button type="submit" class="btn btn-primary w-100">
                                <i class="fas fa-sign-in-alt"></i> 登入
                            </button>
                        </form>
                        
                        <div class="text-center mt-3">
                            <a href="/">返回主頁</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const response = await fetch('/doctor/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                username: document.getElementById('username').value,
                password: document.getElementById('password').value
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            if (data.requires_2fa) {
                window.location.href = '/doctor/login/2fa';
            } else {
                window.location.href = '/doctor/dashboard';
            }
        } else {
            alert(data.message);
        }
    });
    </script>
</body>
</html>
```

#### `templates/doctor/dashboard.html`
```html
{% extends "doctor/base.html" %}

{% block content %}
<div class="container-fluid">
    <h2>歡迎, Dr. {{ doctor.name_zh }}</h2>
    
    <div class="row mt-4">
        <!-- Today's appointments -->
        <div class="col-md-3">
            <div class="card text-center">
                <div class="card-body">
                    <h1 class="text-primary">{{ today_count }}</h1>
                    <p>今日預約</p>
                </div>
            </div>
        </div>
        
        <!-- Pending -->
        <div class="col-md-3">
            <div class="card text-center">
                <div class="card-body">
                    <h1 class="text-warning">{{ pending_count }}</h1>
                    <p>待確認</p>
                </div>
            </div>
        </div>
        
        <!-- This month -->
        <div class="col-md-3">
            <div class="card text-center">
                <div class="card-body">
                    <h1 class="text-success">{{ completed_this_month }}</h1>
                    <p>本月完成</p>
                </div>
            </div>
        </div>
        
        <!-- Rating -->
        <div class="col-md-3">
            <div class="card text-center">
                <div class="card-body">
                    <h1 class="text-info">{{ avg_rating }}</h1>
                    <p>平均評分 ({{ review_count }} 評價)</p>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Quick actions -->
    <div class="row mt-4">
        <div class="col-md-12">
            <div class="card">
                <div class="card-body">
                    <h5>快速操作</h5>
                    <div class="btn-group">
                        <a href="{{ url_for('doctor_portal.reservations') }}" class="btn btn-primary">
                            <i class="fas fa-calendar"></i> 查看預約
                        </a>
                        <a href="{{ url_for('doctor_portal.availability') }}" class="btn btn-info">
                            <i class="fas fa-clock"></i> 管理時間表
                        </a>
                        <a href="{{ url_for('doctor_portal.profile') }}" class="btn btn-secondary">
                            <i class="fas fa-user"></i> 編輯資料
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### 8. Test the System

1. **Run migration**:
   ```bash
   python create_affiliation_system.py
   ```

2. **Start the app**:
   ```bash
   python app.py
   ```

3. **Test flows**:
   - Create a test doctor account via admin
   - Login as doctor at `/doctor/login`
   - Set availability schedule
   - Enable reservations
   - Test booking from patient side
   - Confirm reservation as doctor
   - Submit review as patient

### 9. Production Checklist

- [ ] Database migration completed
- [ ] All blueprints registered
- [ ] Templates created
- [ ] CSS styles added
- [ ] JavaScript functions implemented
- [ ] Admin navigation updated
- [ ] Doctor login tested
- [ ] Booking flow tested
- [ ] Email notifications configured (optional)
- [ ] Backup system in place
- [ ] Monitoring enabled

### 10. Common Issues & Solutions

**Issue**: `ModuleNotFoundError: No module named 'doctor_portal_routes'`
- **Solution**: Ensure all route files are in the same directory as `app.py`

**Issue**: Templates not found
- **Solution**: Create `templates/doctor/` and `templates/admin/` directories

**Issue**: Database locked error
- **Solution**: Close all database connections, restart app

**Issue**: Booking button not showing
- **Solution**: Check `is_affiliated` and `accepts_reservations` columns in database

---

## Quick Commands

```bash
# Run migration
python create_affiliation_system.py

# Check database structure
python check_db_structure.py

# Start application
python app.py

# Access doctor portal
http://localhost:5000/doctor/login

# Access admin affiliation
http://localhost:5000/admin/affiliation/requests
```

---

That's it! Your affiliation system is now integrated. 🎉
