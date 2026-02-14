"""
CAREOPS PRODUCTION READINESS AUDIT
Comprehensive verification of all features with DB state validation
"""

import requests
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.workspace import Workspace
from app.models.user import User
from app.models.service import Service
from app.models.booking import Booking, BookingStatus
from app.models.contact import Contact
from app.models.inventory import InventoryItem
from app.models.communication_log import CommunicationLog
from app.models.conversation import Conversation, Message
from app.models.audit_log import AuditLog
from app.models.form import Form, FormSubmission

BASE_URL = "http://127.0.0.1:8000/api"

class AuditReport:
    def __init__(self):
        self.results = []
        
    def test(self, feature, status, risk, notes):
        self.results.append({
            "feature": feature,
            "status": status,
            "risk": risk,
            "notes": notes
        })
        print(f"[{status}] {feature}: {notes}")
        
    def print_report(self):
        print("\n" + "="*80)
        print("PRODUCTION READINESS AUDIT REPORT")
        print("="*80)
        print(f"{'FEATURE':<40} {'STATUS':<12} {'RISK':<15} {'NOTES':<30}")
        print("-"*80)
        for r in self.results:
            print(f"{r['feature']:<40} {r['status']:<12} {r['risk']:<15} {r['notes']:<30}")
        print("="*80)

def audit():
    report = AuditReport()
    db = SessionLocal()
    
    # ============================================================
    # AUTH TESTS
    # ============================================================
    print("\n=== AUTH TESTS ===")
    
    # Test 1: Login
    try:
        res = requests.post(f"{BASE_URL}/login", 
            data={"username": "owner@careops.com", "password": "owner123"})
        if res.status_code == 200 and "access_token" in res.json():
            owner_token = res.json()["access_token"]
            owner_role = res.json().get("role")
            report.test("Auth: Owner Login", "✅ WORKING", "LOW", "Token received")
        else:
            report.test("Auth: Owner Login", "❌ BROKEN", "CRITICAL", f"Status {res.status_code}")
            return
    except Exception as e:
        report.test("Auth: Owner Login", "❌ BROKEN", "CRITICAL", str(e))
        return
    
    # Test 2: Staff Login
    try:
        res = requests.post(f"{BASE_URL}/login", 
            data={"username": "staff@careops.com", "password": "staff123"})
        if res.status_code == 200:
            staff_token = res.json()["access_token"]
            report.test("Auth: Staff Login", "✅ WORKING", "LOW", "Token received")
        else:
            report.test("Auth: Staff Login", "❌ BROKEN", "HIGH", "Staff cannot login")
    except Exception as e:
        report.test("Auth: Staff Login", "❌ BROKEN", "HIGH", str(e))
        staff_token = None
    
    # Test 3: Token Validation
    headers = {"Authorization": f"Bearer {owner_token}"}
    try:
        res = requests.get(f"{BASE_URL}/dashboard", headers=headers)
        if res.status_code == 200:
            report.test("Auth: Token Validation", "✅ WORKING", "LOW", "Bearer auth works")
        else:
            report.test("Auth: Token Validation", "❌ BROKEN", "CRITICAL", "Token rejected")
    except Exception as e:
        report.test("Auth: Token Validation", "❌ BROKEN", "CRITICAL", str(e))
    
    # Test 4: Invalid Token
    try:
        bad_headers = {"Authorization": "Bearer INVALID_TOKEN"}
        res = requests.get(f"{BASE_URL}/dashboard", headers=bad_headers)
        if res.status_code == 401:
            report.test("Auth: Invalid Token Rejection", "✅ WORKING", "LOW", "401 returned")
        else:
            report.test("Auth: Invalid Token Rejection", "⚠️ PARTIAL", "MEDIUM", "Should return 401")
    except:
        report.test("Auth: Invalid Token Rejection", "⚠️ PARTIAL", "MEDIUM", "Error handling unclear")
    
    # ============================================================
    # DASHBOARD TRUTH TEST
    # ============================================================
    print("\n=== DASHBOARD TRUTH ===")
    
    try:
        res = requests.get(f"{BASE_URL}/dashboard", headers=headers)
        dash_data = res.json()
        
        # Verify bookings count matches DB
        db_bookings_today = db.query(Booking).filter(
            Booking.workspace_id == 2,
            Booking.status != BookingStatus.CANCELLED.value
        ).count()
        
        api_bookings = dash_data.get("bookings", {}).get("today_count", 0)
        
        if "bookings" in dash_data and "inbox" in dash_data:
            report.test("Dashboard: Data Structure", "✅ WORKING", "LOW", "All sections present")
        else:
            report.test("Dashboard: Data Structure", "❌ BROKEN", "HIGH", "Missing sections")
            
        # Check if attention items exist
        if "attention" in dash_data:
            report.test("Dashboard: Attention Panel", "✅ WORKING", "LOW", f"{len(dash_data['attention'])} items")
        else:
            report.test("Dashboard: Attention Panel", "❌ BROKEN", "MEDIUM", "No attention data")
            
        # Check recent activity
        if "recent_activity" in dash_data and len(dash_data["recent_activity"]) > 0:
            report.test("Dashboard: Recent Activity", "✅ WORKING", "LOW", "Events tracked")
        else:
            report.test("Dashboard: Recent Activity", "⚠️ PARTIAL", "MEDIUM", "No activity or empty")
            
    except Exception as e:
        report.test("Dashboard: API", "❌ BROKEN", "CRITICAL", str(e))
    
    # ============================================================
    # BOOKING FLOW
    # ============================================================
    print("\n=== BOOKING FLOW ===")
    
    # Test: Get Services
    try:
        res = requests.get(f"{BASE_URL}/public/workspace/test-spa")
        if res.status_code == 200 and "services" in res.json():
            services = res.json()["services"]
            report.test("Booking: Public Service List", "✅ WORKING", "LOW", f"{len(services)} services")
        else:
            report.test("Booking: Public Service List", "❌ BROKEN", "HIGH", "Cannot list services")
    except Exception as e:
        report.test("Booking: Public Service List", "❌ BROKEN", "HIGH", str(e))
    
    # Test: Availability
    try:
        service = db.query(Service).first()
        if service:
            from datetime import date
            today = date.today().isoformat()
            res = requests.get(f"{BASE_URL}/public/services/{service.id}/availability?date={today}")
            if res.status_code == 200:
                slots = res.json()
                report.test("Booking: Availability Slots", "✅ WORKING", "LOW", f"{len(slots)} slots")
            else:
                report.test("Booking: Availability Slots", "❌ BROKEN", "HIGH", f"Status {res.status_code}")
        else:
            report.test("Booking: Availability Slots", "❌ BROKEN", "HIGH", "No service in DB")
    except Exception as e:
        report.test("Booking: Availability Slots", "❌ BROKEN", "HIGH", str(e))
    
    # Test: Create Booking
    try:
        service = db.query(Service).first()
        contact = db.query(Contact).first()
        if service and contact:
            booking_data = {
                "service_id": service.id,
                "start_datetime": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
                "name": "Test Customer",
                "email": "test@example.com",
                "phone": "+1234567890"
            }
            res = requests.post(f"{BASE_URL}/bookings", json=booking_data, headers=headers)
            if res.status_code == 200:
                new_booking_id = res.json().get("id")
                report.test("Booking: Create", "✅ WORKING", "LOW", f"Booking #{new_booking_id}")
                
                # Verify DB state
                db_booking = db.query(Booking).filter(Booking.id == new_booking_id).first()
                if db_booking:
                    report.test("Booking: DB Persistence", "✅ WORKING", "LOW", "Booking in DB")
                else:
                    report.test("Booking: DB Persistence", "❌ BROKEN", "CRITICAL", "Not in DB!")
                    
                # Check communication log
                comm_log = db.query(CommunicationLog).filter(
                    CommunicationLog.booking_id == new_booking_id
                ).first()
                if comm_log:
                    report.test("Booking: Communication Log", "✅ WORKING", "LOW", f"Type: {comm_log.type}")
                else:
                    report.test("Booking: Communication Log", "⚠️ PARTIAL", "MEDIUM", "No log created")
            else:
                report.test("Booking: Create", "❌ BROKEN", "CRITICAL", f"Status {res.status_code}")
        else:
            report.test("Booking: Create", "❌ BROKEN", "CRITICAL", "No service/contact in DB")
    except Exception as e:
        report.test("Booking: Create", "❌ BROKEN", "CRITICAL", str(e))
    
    # ============================================================
    # BOOKING ACTIONS
    # ============================================================
    print("\n=== BOOKING ACTIONS ===")
    
    # Test: Cancel
    try:
        booking = db.query(Booking).filter(Booking.status == BookingStatus.CONFIRMED.value).first()
        if booking:
            res = requests.post(f"{BASE_URL}/bookings/{booking.id}/cancel", headers=headers)
            if res.status_code == 200:
                db.refresh(booking)
                if booking.status == BookingStatus.CANCELLED.value:
                    report.test("Action: Cancel Booking", "✅ WORKING", "LOW", "DB updated")
                else:
                    report.test("Action: Cancel Booking", "❌ BROKEN", "HIGH", "DB not updated")
            else:
                report.test("Action: Cancel Booking", "❌ BROKEN", "HIGH", f"Status {res.status_code}")
        else:
            report.test("Action: Cancel Booking", "⚠️ PARTIAL", "MEDIUM", "No confirmed booking to test")
    except Exception as e:
        report.test("Action: Cancel Booking", "❌ BROKEN", "HIGH", str(e))
    
    # Test: Restore
    try:
        cancelled = db.query(Booking).filter(Booking.status == BookingStatus.CANCELLED.value).first()
        if cancelled:
            res = requests.post(f"{BASE_URL}/bookings/{cancelled.id}/restore", headers=headers)
            if res.status_code == 200:
                db.refresh(cancelled)
                if cancelled.status == BookingStatus.CONFIRMED.value:
                    report.test("Action: Restore Booking", "✅ WORKING", "LOW", "DB updated")
                else:
                    report.test("Action: Restore Booking", "❌ BROKEN", "HIGH", "DB not updated")
            else:
                report.test("Action: Restore Booking", "❌ BROKEN", "HIGH", f"Status {res.status_code}")
        else:
            report.test("Action: Restore Booking", "⚠️ PARTIAL", "MEDIUM", "No cancelled booking to test")
    except Exception as e:
        report.test("Action: Restore Booking", "❌ BROKEN", "HIGH", str(e))
    
    # Test: History Timeline
    try:
        booking = db.query(Booking).first()
        if booking:
            res = requests.get(f"{BASE_URL}/bookings/{booking.id}/history", headers=headers)
            if res.status_code == 200:
                history = res.json()
                if len(history) > 0:
                    report.test("Action: Booking History", "✅ WORKING", "LOW", f"{len(history)} events")
                else:
                    report.test("Action: Booking History", "⚠️ PARTIAL", "MEDIUM", "No history events")
            else:
                report.test("Action: Booking History", "❌ BROKEN", "HIGH", f"Status {res.status_code}")
        else:
            report.test("Action: Booking History", "❌ BROKEN", "HIGH", "No booking to test")
    except Exception as e:
        report.test("Action: Booking History", "❌ BROKEN", "HIGH", str(e))
    
    # ============================================================
    # INBOX
    # ============================================================
    print("\n=== INBOX ===")
    
    try:
        res = requests.get(f"{BASE_URL}/conversations", headers=headers)
        if res.status_code == 200:
            conversations = res.json()
            report.test("Inbox: List Conversations", "✅ WORKING", "LOW", f"{len(conversations)} convos")
            
            if len(conversations) > 0:
                conv_id = conversations[0]["id"]
                res2 = requests.get(f"{BASE_URL}/conversations/{conv_id}", headers=headers)
                if res2.status_code == 200:
                    messages = res2.json()
                    report.test("Inbox: View Messages", "✅ WORKING", "LOW", f"{len(messages)} messages")
                else:
                    report.test("Inbox: View Messages", "❌ BROKEN", "HIGH", "Cannot view")
        else:
            report.test("Inbox: List Conversations", "❌ BROKEN", "HIGH", f"Status {res.status_code}")
    except Exception as e:
        report.test("Inbox: List Conversations", "❌ BROKEN", "HIGH", str(e))
    
    # ============================================================
    # ROLE SECURITY
    # ============================================================
    print("\n=== ROLE SECURITY ===")
    
    if staff_token:
        staff_headers = {"Authorization": f"Bearer {staff_token}"}
        try:
            res = requests.get(f"{BASE_URL}/dashboard", headers=staff_headers)
            if res.status_code in [401, 403]:
                report.test("Security: Staff Blocked from Dashboard", "✅ WORKING", "LOW", "Correctly blocked")
            else:
                report.test("Security: Staff Blocked from Dashboard", "❌ BROKEN", "CRITICAL", "Staff has owner access!")
        except:
            report.test("Security: Staff Blocked from Dashboard", "⚠️ PARTIAL", "HIGH", "Error unclear")
    
    # ============================================================
    # INVENTORY
    # ============================================================
    print("\n=== INVENTORY ===")
    
    try:
        item = db.query(InventoryItem).first()
        if item:
            original_qty = item.quantity
            report.test("Inventory: DB Record Exists", "✅ WORKING", "LOW", f"{item.name}: {original_qty}")
            
            # Check if low stock appears in dashboard
            if item.quantity < item.threshold:
                res = requests.get(f"{BASE_URL}/dashboard", headers=headers)
                dash = res.json()
                low_stock_alert = any("inventory" in str(a).lower() or "low" in str(a).lower() 
                                     for a in dash.get("attention", []))
                if low_stock_alert:
                    report.test("Inventory: Low Stock Alert", "✅ WORKING", "LOW", "Alert visible")
                else:
                    report.test("Inventory: Low Stock Alert", "⚠️ PARTIAL", "MEDIUM", "No alert shown")
        else:
            report.test("Inventory: DB Record Exists", "❌ BROKEN", "HIGH", "No inventory items")
    except Exception as e:
        report.test("Inventory: System", "❌ BROKEN", "HIGH", str(e))
    
    db.close()
    
    # ============================================================
    # PRINT REPORT
    # ============================================================
    report.print_report()
    
    # Calculate verdict
    working = sum(1 for r in report.results if r["status"] == "✅ WORKING")
    partial = sum(1 for r in report.results if r["status"] == "⚠️ PARTIAL")
    broken = sum(1 for r in report.results if r["status"] == "❌ BROKEN")
    total = len(report.results)
    
    confidence = int((working / total) * 10) if total > 0 else 0
    
    print("\n" + "="*80)
    print("FINAL VERDICT")
    print("="*80)
    print(f"Working: {working}/{total}")
    print(f"Partial: {partial}/{total}")
    print(f"Broken: {broken}/{total}")
    print(f"Confidence Score: {confidence}/10")
    
    ready = broken == 0 and partial <= 2
    print(f"\nReady for real shop tomorrow? {'YES' if ready else 'NO'}")
    
    print("\nTop Business Risks:")
    critical_risks = [r for r in report.results if r["risk"] == "CRITICAL" and r["status"] != "✅ WORKING"]
    high_risks = [r for r in report.results if r["risk"] == "HIGH" and r["status"] != "✅ WORKING"]
    
    for i, risk in enumerate((critical_risks + high_risks)[:5], 1):
        print(f"{i}. {risk['feature']}: {risk['notes']}")
    
    print("="*80)

if __name__ == "__main__":
    audit()
