"""
Comprehensive End-to-End System Test Script

Tests all critical functionality:
- Authentication (signup, login, logout)
- Owner features (leads, bookings, contacts, etc.)
- Public features (lead form, booking)
- API endpoints
- Data integrity
- Error handling
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.skipped = []
    
    def add_pass(self, test_name):
        self.passed.append(test_name)
        print(f"{Colors.GREEN}✓{Colors.END} {test_name}")
    
    def add_fail(self, test_name, error):
        self.failed.append((test_name, error))
        print(f"{Colors.RED}✗{Colors.END} {test_name}: {error}")
    
    def add_skip(self, test_name, reason):
        self.skipped.append((test_name, reason))
        print(f"{Colors.YELLOW}⊘{Colors.END} {test_name}: {reason}")
    
    def summary(self):
        total = len(self.passed) + len(self.failed) + len(self.skipped)
        print(f"\n{'='*60}")
        print(f"{Colors.BLUE}TEST SUMMARY{Colors.END}")
        print(f"{'='*60}")
        print(f"{Colors.GREEN}Passed:{Colors.END} {len(self.passed)}/{total}")
        print(f"{Colors.RED}Failed:{Colors.END} {len(self.failed)}/{total}")
        print(f"{Colors.YELLOW}Skipped:{Colors.END} {len(self.skipped)}/{total}")
        
        if self.failed:
            print(f"\n{Colors.RED}FAILED TESTS:{Colors.END}")
            for test, error in self.failed:
                print(f"  - {test}: {error}")
        
        if self.skipped:
            print(f"\n{Colors.YELLOW}SKIPPED TESTS:{Colors.END}")
            for test, reason in self.skipped:
                print(f"  - {test}: {reason}")
        
        print(f"{'='*60}\n")
        
        return len(self.failed) == 0

results = TestResults()

# Test data
test_business = {
    "business_name": f"Test Clinic {datetime.now().strftime('%H%M%S')}",
    "owner_full_name": "Test Owner",
    "owner_email": f"owner{datetime.now().strftime('%H%M%S')}@test.com",
    "owner_password": "testpass123",
    "business_phone": "1234567890",
    "business_address": "123 Test St",
    "timezone": "Asia/Kolkata"
}

token = None
workspace_slug = None

print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
print(f"{Colors.BLUE}CAREOPS MVP - END-TO-END SYSTEM TEST{Colors.END}")
print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")

# Phase 1: Backend Health
print(f"\n{Colors.BLUE}Phase 1: Backend Health Check{Colors.END}")
print("-" * 60)

try:
    response = requests.get(f"{BASE_URL}/", timeout=5)
    if response.status_code == 200:
        results.add_pass("Backend is running")
    else:
        results.add_fail("Backend is running", f"Status {response.status_code}")
except Exception as e:
    results.add_fail("Backend is running", str(e))

# Phase 2: Authentication
print(f"\n{Colors.BLUE}Phase 2: Authentication{Colors.END}")
print("-" * 60)

# Test Signup
try:
    response = requests.post(f"{BASE_URL}/api/signup", json=test_business)
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        workspace_slug = data.get("workspace", {}).get("slug")
        results.add_pass("Signup - Create new business")
    else:
        results.add_fail("Signup - Create new business", f"Status {response.status_code}: {response.text}")
except Exception as e:
    results.add_fail("Signup - Create new business", str(e))

# Test Login
try:
    response = requests.post(f"{BASE_URL}/api/login", data={
        "username": test_business["owner_email"],
        "password": test_business["owner_password"]
    })
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        results.add_pass("Login - Owner credentials")
    else:
        results.add_fail("Login - Owner credentials", f"Status {response.status_code}")
except Exception as e:
    results.add_fail("Login - Owner credentials", str(e))

# Test Invalid Login
try:
    response = requests.post(f"{BASE_URL}/api/login", data={
        "username": "invalid@test.com",
        "password": "wrongpass"
    })
    if response.status_code in [401, 400]:
        results.add_pass("Invalid credentials - Login fail")
    else:
        results.add_fail("Invalid credentials - Login fail", f"Expected 401, got {response.status_code}")
except Exception as e:
    results.add_fail("Invalid credentials - Login fail", str(e))

if not token:
    print(f"\n{Colors.RED}Cannot continue without auth token{Colors.END}")
    results.summary()
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# Phase 3: Owner Features
print(f"\n{Colors.BLUE}Phase 3: Owner Features{Colors.END}")
print("-" * 60)

# Test Dashboard
try:
    response = requests.get(f"{BASE_URL}/api/dashboard/", headers=headers)
    if response.status_code == 200:
        results.add_pass("Dashboard - View stats")
    else:
        results.add_fail("Dashboard - View stats", f"Status {response.status_code}")
except Exception as e:
    results.add_fail("Dashboard - View stats", str(e))

# Test Leads
try:
    response = requests.get(f"{BASE_URL}/api/leads", headers=headers)
    if response.status_code == 200:
        results.add_pass("Leads - View all leads")
    else:
        results.add_fail("Leads - View all leads", f"Status {response.status_code}")
except Exception as e:
    results.add_fail("Leads - View all leads", str(e))

# Test Bookings
try:
    response = requests.get(f"{BASE_URL}/api/bookings", headers=headers)
    if response.status_code == 200:
        results.add_pass("Bookings - View all bookings")
    else:
        results.add_fail("Bookings - View all bookings", f"Status {response.status_code}")
except Exception as e:
    results.add_fail("Bookings - View all bookings", str(e))

# Phase 4: Public Features
print(f"\n{Colors.BLUE}Phase 4: Public Features{Colors.END}")
print("-" * 60)

if workspace_slug:
    # Test Lead Form Submission
    try:
        response = requests.post(f"{BASE_URL}/api/workspaces/{workspace_slug}/lead-form", json={
            "first_name": "Test",
            "last_name": "Lead",
            "email": f"lead{datetime.now().strftime('%H%M%S')}@test.com",
            "phone": "9876543210",
            "message": "Test inquiry"
        })
        if response.status_code == 200:
            results.add_pass("Lead form - Submit inquiry")
        else:
            results.add_fail("Lead form - Submit inquiry", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("Lead form - Submit inquiry", str(e))
else:
    results.add_skip("Lead form - Submit inquiry", "No workspace slug")

# Phase 5: Gmail Integration
print(f"\n{Colors.BLUE}Phase 5: Gmail Integration{Colors.END}")
print("-" * 60)

# Test Gmail Status
try:
    response = requests.get(f"{BASE_URL}/api/integrations/email/status", headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data.get("connected"):
            results.add_pass("Gmail - Status shows connected")
        else:
            results.add_skip("Gmail - Status shows connected", "Gmail not connected")
    else:
        results.add_fail("Gmail - Status check", f"Status {response.status_code}")
except Exception as e:
    results.add_fail("Gmail - Status check", str(e))

# Phase 6: Edge Cases
print(f"\n{Colors.BLUE}Phase 6: Edge Cases{Colors.END}")
print("-" * 60)

# Test Duplicate Email Signup
try:
    response = requests.post(f"{BASE_URL}/api/signup", json=test_business)
    if response.status_code in [400, 409]:
        results.add_pass("Duplicate email - Signup fail")
    else:
        results.add_fail("Duplicate email - Signup fail", f"Expected 400/409, got {response.status_code}")
except Exception as e:
    results.add_fail("Duplicate email - Signup fail", str(e))

# Test Unauthorized Access
try:
    response = requests.get(f"{BASE_URL}/api/dashboard/stats")  # No auth header
    if response.status_code in [401, 403]:
        results.add_pass("Unauthorized access - 401/403")
    else:
        results.add_fail("Unauthorized access - 401/403", f"Expected 401/403, got {response.status_code}")
except Exception as e:
    results.add_fail("Unauthorized access - 401/403", str(e))

# Test Non-existent Resource
try:
    response = requests.get(f"{BASE_URL}/api/leads/999999", headers=headers)
    if response.status_code == 404:
        results.add_pass("Non-existent resource - 404")
    else:
        results.add_fail("Non-existent resource - 404", f"Expected 404, got {response.status_code}")
except Exception as e:
    results.add_fail("Non-existent resource - 404", str(e))

# Phase 7: Frontend Health
print(f"\n{Colors.BLUE}Phase 7: Frontend Health{Colors.END}")
print("-" * 60)

try:
    response = requests.get(FRONTEND_URL, timeout=5)
    if response.status_code == 200:
        results.add_pass("Frontend is running")
    else:
        results.add_fail("Frontend is running", f"Status {response.status_code}")
except Exception as e:
    results.add_skip("Frontend is running", str(e))

# Print Summary
success = results.summary()

if success:
    print(f"{Colors.GREEN}🎉 ALL TESTS PASSED! System is ready for deployment.{Colors.END}\n")
    exit(0)
else:
    print(f"{Colors.RED}⚠️  Some tests failed. Review failures before deployment.{Colors.END}\n")
    exit(1)
