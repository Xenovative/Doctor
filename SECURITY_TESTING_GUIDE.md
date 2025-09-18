# Security Testing Guide
## Doctor AI Medical Matching System

### Overview
This guide covers how to test our healthcare app's security defenses. Since we handle medical data, we need to be extra paranoid about security vulnerabilities.

---

## 1. Automated Security Scanning

### **OWASP ZAP (Free & Effective)**
```bash
# Install OWASP ZAP
# Download from: https://www.zaproxy.org/download/

# Basic automated scan
zap-baseline.py -t http://localhost:5000 -r zap_report.html

# Full scan (more thorough)
zap-full-scan.py -t http://localhost:5000 -r full_scan_report.html
```

### **Bandit (Python Security Linter)**
```bash
# Install bandit
pip install bandit

# Scan our Python code for security issues
bandit -r . -f json -o security_report.json

# Focus on high-severity issues
bandit -r . -ll -i
```

### **Safety (Check Dependencies)**
```bash
# Install safety
pip install safety

# Check for known vulnerabilities in our dependencies
safety check --json --output safety_report.json

# Check requirements.txt specifically
safety check -r requirements.txt
```

---

## 2. Manual Security Testing

### **Authentication & Session Testing**

#### **Test 2FA Bypass**
```python
# Test script: test_2fa_bypass.py
import requests

def test_2fa_bypass():
    session = requests.Session()
    
    # Try to access admin panel without 2FA
    response = session.get('http://localhost:5000/admin/dashboard')
    
    # Should redirect to login or 2FA
    assert response.status_code in [302, 401, 403]
    
    # Try session fixation
    session.cookies.set('session', 'fake_session_id')
    response = session.get('http://localhost:5000/admin/dashboard')
    assert response.status_code in [302, 401, 403]

if __name__ == "__main__":
    test_2fa_bypass()
    print("✅ 2FA bypass tests passed")
```

#### **Session Security Tests**
```python
# Test script: test_session_security.py
import requests
import time

def test_session_timeout():
    """Test if sessions expire properly"""
    session = requests.Session()
    
    # Login first (you'll need to adapt this to your login flow)
    login_data = {'username': 'test_admin', 'password': 'test_password'}
    session.post('http://localhost:5000/admin/login', data=login_data)
    
    # Wait for session timeout (adjust based on your settings)
    time.sleep(1800)  # 30 minutes
    
    # Try to access protected resource
    response = session.get('http://localhost:5000/admin/dashboard')
    assert response.status_code in [302, 401, 403]

def test_session_fixation():
    """Test session fixation vulnerability"""
    session = requests.Session()
    
    # Get initial session
    response = session.get('http://localhost:5000/admin/login')
    initial_session = session.cookies.get('session')
    
    # Login
    login_data = {'username': 'test_admin', 'password': 'test_password'}
    session.post('http://localhost:5000/admin/login', data=login_data)
    
    # Session should change after login
    new_session = session.cookies.get('session')
    assert initial_session != new_session

if __name__ == "__main__":
    test_session_timeout()
    test_session_fixation()
    print("✅ Session security tests passed")
```

### **SQL Injection Testing**

#### **Automated SQL Injection Tests**
```python
# Test script: test_sql_injection.py
import requests

def test_sql_injection_payloads():
    """Test common SQL injection payloads"""
    
    payloads = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "' UNION SELECT * FROM admin_users --",
        "1' OR 1=1 --",
        "admin'--",
        "' OR 1=1#"
    ]
    
    # Test login form
    for payload in payloads:
        data = {
            'username': payload,
            'password': 'test'
        }
        response = requests.post('http://localhost:5000/admin/login', data=data)
        
        # Should not result in successful login
        assert 'dashboard' not in response.url.lower()
        assert response.status_code != 200 or 'error' in response.text.lower()
    
    # Test search functionality
    for payload in payloads:
        params = {'search': payload}
        response = requests.get('http://localhost:5000/search', params=params)
        
        # Should not expose database errors
        assert 'sqlite' not in response.text.lower()
        assert 'database' not in response.text.lower()
        assert 'sql' not in response.text.lower()

if __name__ == "__main__":
    test_sql_injection_payloads()
    print("✅ SQL injection tests passed")
```

### **Cross-Site Scripting (XSS) Testing**

#### **XSS Payload Tests**
```python
# Test script: test_xss.py
import requests
from bs4 import BeautifulSoup

def test_xss_payloads():
    """Test XSS vulnerabilities"""
    
    payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "<svg onload=alert('XSS')>",
        "';alert('XSS');//"
    ]
    
    # Test forms that accept user input
    for payload in payloads:
        # Test symptom input
        data = {
            'symptoms': payload,
            'age': '25',
            'gender': 'male'
        }
        response = requests.post('http://localhost:5000/analyze', data=data)
        
        # Payload should be escaped in response
        assert payload not in response.text
        
        # Test admin forms (if accessible)
        admin_data = {
            'description': payload,
            'contact_info': 'test@test.com'
        }
        response = requests.post('http://localhost:5000/report-bug', data=admin_data)
        assert payload not in response.text

if __name__ == "__main__":
    test_xss_payloads()
    print("✅ XSS tests passed")
```

---

## 3. Infrastructure Security Testing

### **SSL/TLS Configuration**
```bash
# Test SSL configuration with testssl.sh
git clone https://github.com/drwetter/testssl.sh.git
cd testssl.sh
./testssl.sh https://yourdomain.com

# Or use online tools:
# - SSL Labs: https://www.ssllabs.com/ssltest/
# - Security Headers: https://securityheaders.com/
```

### **HTTP Security Headers**
```python
# Test script: test_security_headers.py
import requests

def test_security_headers():
    """Test for proper security headers"""
    
    response = requests.get('http://localhost:5000')
    headers = response.headers
    
    # Required security headers
    required_headers = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': None,  # Should exist
        'Content-Security-Policy': None     # Should exist
    }
    
    for header, expected_value in required_headers.items():
        assert header in headers, f"Missing security header: {header}"
        if expected_value:
            assert headers[header] == expected_value

if __name__ == "__main__":
    test_security_headers()
    print("✅ Security headers tests passed")
```

---

## 4. API Security Testing

### **Rate Limiting Tests**
```python
# Test script: test_rate_limiting.py
import requests
import time
import threading

def test_rate_limiting():
    """Test API rate limiting"""
    
    def make_request():
        return requests.post('http://localhost:5000/admin/login', 
                           data={'username': 'test', 'password': 'test'})
    
    # Make rapid requests
    responses = []
    for i in range(100):
        response = make_request()
        responses.append(response.status_code)
        time.sleep(0.1)
    
    # Should see rate limiting kick in (429 status codes)
    rate_limited = [r for r in responses if r == 429]
    assert len(rate_limited) > 0, "Rate limiting not working"

def test_concurrent_requests():
    """Test handling of concurrent requests"""
    
    def worker():
        return requests.get('http://localhost:5000/analyze')
    
    # Launch concurrent requests
    threads = []
    for i in range(50):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()
    
    # Wait for all to complete
    for t in threads:
        t.join()
    
    print("✅ Server handled concurrent requests")

if __name__ == "__main__":
    test_rate_limiting()
    test_concurrent_requests()
    print("✅ API security tests passed")
```

### **Authorization Tests**
```python
# Test script: test_authorization.py
import requests

def test_privilege_escalation():
    """Test for privilege escalation vulnerabilities"""
    
    # Login as regular admin
    session = requests.Session()
    login_data = {'username': 'regular_admin', 'password': 'password'}
    session.post('http://localhost:5000/admin/login', data=login_data)
    
    # Try to access super admin functions
    super_admin_endpoints = [
        '/admin/users/create',
        '/admin/config',
        '/admin/api/user-permissions/update'
    ]
    
    for endpoint in super_admin_endpoints:
        response = session.get(f'http://localhost:5000{endpoint}')
        # Should be denied
        assert response.status_code in [403, 401, 302]

def test_direct_object_references():
    """Test for insecure direct object references"""
    
    session = requests.Session()
    # Login as one user
    login_data = {'username': 'admin1', 'password': 'password'}
    session.post('http://localhost:5000/admin/login', data=login_data)
    
    # Try to access another user's data
    response = session.get('http://localhost:5000/admin/severe-cases/1/review')
    # Should check permissions properly
    
if __name__ == "__main__":
    test_privilege_escalation()
    test_direct_object_references()
    print("✅ Authorization tests passed")
```

---

## 5. Database Security Testing

### **Database Connection Security**
```python
# Test script: test_database_security.py
import sqlite3
import os

def test_database_permissions():
    """Test database file permissions"""
    
    db_files = ['admin_data.db', 'doctors.db']
    
    for db_file in db_files:
        if os.path.exists(db_file):
            # Check file permissions
            stat = os.stat(db_file)
            permissions = oct(stat.st_mode)[-3:]
            
            # Should not be world-readable
            assert permissions[2] == '0', f"{db_file} is world-readable"

def test_sql_injection_in_queries():
    """Test our actual database queries for SQL injection"""
    
    # Test with malicious input
    malicious_inputs = [
        "'; DROP TABLE users; --",
        "' OR 1=1 --",
        "UNION SELECT * FROM admin_users"
    ]
    
    # This would require importing your actual database functions
    # and testing them with malicious input
    pass

if __name__ == "__main__":
    test_database_permissions()
    print("✅ Database security tests passed")
```

---

## 6. Load Testing for DoS Resistance

### **Stress Testing with Locust**
```python
# File: locustfile.py
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def view_homepage(self):
        self.client.get("/")
    
    @task(2)
    def search_doctors(self):
        self.client.post("/analyze", data={
            "symptoms": "headache fever",
            "age": "30",
            "gender": "male"
        })
    
    @task(1)
    def admin_login_attempt(self):
        self.client.post("/admin/login", data={
            "username": "test",
            "password": "test"
        })

# Run with: locust -f locustfile.py --host=http://localhost:5000
```

---

## 7. Security Testing Checklist

### **Pre-Deployment Security Checklist**

#### **Authentication & Authorization**
- [ ] 2FA cannot be bypassed
- [ ] Sessions expire properly
- [ ] Session fixation prevented
- [ ] Password policies enforced
- [ ] Account lockout after failed attempts
- [ ] Privilege escalation prevented

#### **Input Validation**
- [ ] SQL injection prevented
- [ ] XSS attacks blocked
- [ ] CSRF protection enabled
- [ ] File upload restrictions
- [ ] Input length limits enforced

#### **Data Protection**
- [ ] Sensitive data encrypted
- [ ] Database access restricted
- [ ] Backup files secured
- [ ] Logs don't contain sensitive data
- [ ] HTTPS enforced everywhere

#### **Infrastructure**
- [ ] Security headers configured
- [ ] Rate limiting implemented
- [ ] Error messages don't leak info
- [ ] Debug mode disabled in production
- [ ] Unnecessary services disabled

---

## 8. Automated Security Testing Pipeline

### **GitHub Actions Security Workflow**
```yaml
# .github/workflows/security.yml
name: Security Tests

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install bandit safety
        pip install -r requirements.txt
    
    - name: Run Bandit security scan
      run: bandit -r . -f json -o bandit-report.json
    
    - name: Check for vulnerabilities
      run: safety check --json --output safety-report.json
    
    - name: Run custom security tests
      run: |
        python test_sql_injection.py
        python test_xss.py
        python test_session_security.py
```

---

## 9. Penetration Testing

### **When to Hire Professionals**
Consider professional penetration testing when:
- Handling sensitive medical data (like we do)
- Before major releases
- After significant security changes
- Annually for compliance

### **What to Look For**
- OWASP Top 10 coverage
- Medical data compliance (HIPAA, etc.)
- Social engineering tests
- Physical security assessment
- Detailed remediation guidance

---

## 10. Monitoring & Incident Response

### **Security Monitoring**
```python
# Add to your Flask app
import logging
from functools import wraps

def log_security_event(event_type, details):
    """Log security events for monitoring"""
    security_logger = logging.getLogger('security')
    security_logger.warning(f"SECURITY EVENT: {event_type} - {details}")

def monitor_failed_logins(f):
    """Decorator to monitor failed login attempts"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)
        
        # Log failed attempts
        if request.method == 'POST' and 'login failed' in result:
            log_security_event('FAILED_LOGIN', {
                'ip': request.remote_addr,
                'username': request.form.get('username'),
                'timestamp': datetime.now()
            })
        
        return result
    return decorated_function
```

### **Incident Response Plan**
1. **Detect**: Monitor logs, alerts, user reports
2. **Contain**: Isolate affected systems
3. **Investigate**: Determine scope and cause
4. **Remediate**: Fix vulnerabilities, restore systems
5. **Learn**: Update security measures

---

## Bottom Line

Security testing isn't a one-time thing - it's an ongoing process. For a healthcare app like ours, we need to be extra careful because:

- Medical data is highly sensitive
- Regulatory compliance is required
- User trust is everything
- Attacks are getting more sophisticated

Start with the automated tools (they catch the obvious stuff), then do manual testing for the tricky vulnerabilities. And remember - assume you'll be attacked, because you probably will be.

---

*Last Updated: September 18, 2025*
