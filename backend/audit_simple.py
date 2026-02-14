"""
CAREOPS PRODUCTION READINESS AUDIT - SIMPLIFIED
"""

import requests
import json
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.workspace import Workspace
from app.models.user import User
from app.models.service import Service
from app.models.booking import Booking, BookingStatus
from app.models.contact import Contact
from app.models.inventory import InventoryItem
from app.models.communication_log import CommunicationLog

BASE_URL = "http://127.0.0.1:8000/api"

def test_auth():
    print("\n=== AUTH TESTS ===")
    results = []
    
    # Owner login
    try:
        res = requests.post(f"{BASE_URL}/login", data={"username": "owner@careops.com", "password": "owner123"})
        if res.status_code == 200 and "access_token" in res.json():
            token = res.json()["access_token"]
            results.append(("Auth: Owner Login", "PASS", "Token received"))
            return token, results
        else:
            results.append(("Auth: Owner Login", "FAIL", f"Status {res.status_code}"))
            return None, results
    except Exception as e:
        results.append(("Auth: Owner Login", "FAIL", str(e)))
        return None, results

def test_dashboard(token):
    print("\n=== DASHBOARD ===")
    results = []
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        res = requests.get(f"{BASE_URL}/dashboard", headers=headers)
        if res.status_code == 200:
            data = res.json()
            results.append(("Dashboard: API", "PASS", "Data received"))
            
            if "bookings" in data and "inbox" in data:
                results.append(("Dashboard: Structure", "PASS", "All sections present"))
            else:
                results.append(("Dashboard: Structure", "FAIL", "Missing sections"))
                
            if "attention" in data:
                results.append(("Dashboard: Attention", "PASS", f"{len(data['attention'])} items"))
            else:
                results.append(("Dashboard: Attention", "WARN", "No attention data"))
        else:
            results.append(("Dashboard: API", "FAIL", f"Status {res.status_code}"))
    except Exception as e:
        results.append(("Dashboard: API", "FAIL", str(e)))
    
    return results

def test_bookings(token):
    print("\n=== BOOKINGS ===")
    results = []
    headers = {"Authorization": f"Bearer {token}"}
    db = SessionLocal()
    
    try:
        # List bookings
        res = requests.get(f"{BASE_URL}/bookings", headers=headers)
        if res.status_code == 200:
            bookings = res.json()
            results.append(("Bookings: List", "PASS", f"{len(bookings)} bookings"))
        else:
            results.append(("Bookings: List", "FAIL", f"Status {res.status_code}"))
        
        # Test cancel
        booking = db.query(Booking).filter(Booking.status == BookingStatus.CONFIRMED.value).first()
        if booking:
            res = requests.post(f"{BASE_URL}/bookings/{booking.id}/cancel", headers=headers)
            if res.status_code == 200:
                db.refresh(booking)
                if booking.status == BookingStatus.CANCELLED.value:
                    results.append(("Bookings: Cancel", "PASS", "DB updated"))
                else:
                    results.append(("Bookings: Cancel", "FAIL", "DB not updated"))
            else:
                results.append(("Bookings: Cancel", "FAIL", f"Status {res.status_code}"))
        else:
            results.append(("Bookings: Cancel", "SKIP", "No confirmed booking"))
            
        # Test history
        booking = db.query(Booking).first()
        if booking:
            res = requests.get(f"{BASE_URL}/bookings/{booking.id}/history", headers=headers)
            if res.status_code == 200:
                history = res.json()
                results.append(("Bookings: History", "PASS", f"{len(history)} events"))
            else:
                results.append(("Bookings: History", "FAIL", f"Status {res.status_code}"))
        
    except Exception as e:
        results.append(("Bookings: System", "FAIL", str(e)))
    finally:
        db.close()
    
    return results

def test_inbox(token):
    print("\n=== INBOX ===")
    results = []
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        res = requests.get(f"{BASE_URL}/conversations", headers=headers)
        if res.status_code == 200:
            convos = res.json()
            results.append(("Inbox: List", "PASS", f"{len(convos)} conversations"))
        else:
            results.append(("Inbox: List", "FAIL", f"Status {res.status_code}"))
    except Exception as e:
        results.append(("Inbox: System", "FAIL", str(e)))
    
    return results

def test_security(token):
    print("\n=== SECURITY ===")
    results = []
    
    try:
        # Staff login
        res = requests.post(f"{BASE_URL}/login", data={"username": "staff@careops.com", "password": "staff123"})
        if res.status_code == 200:
            staff_token = res.json()["access_token"]
            results.append(("Security: Staff Login", "PASS", "Token received"))
            
            # Try to access dashboard
            staff_headers = {"Authorization": f"Bearer {staff_token}"}
            res2 = requests.get(f"{BASE_URL}/dashboard", headers=staff_headers)
            if res2.status_code in [401, 403]:
                results.append(("Security: Role Guard", "PASS", "Staff blocked"))
            else:
                results.append(("Security: Role Guard", "FAIL", "Staff has owner access!"))
        else:
            results.append(("Security: Staff Login", "FAIL", "Cannot login"))
    except Exception as e:
        results.append(("Security: System", "FAIL", str(e)))
    
    return results

def main():
    print("="*80)
    print("CAREOPS PRODUCTION READINESS AUDIT")
    print("="*80)
    
    all_results = []
    
    # Run tests
    token, auth_results = test_auth()
    all_results.extend(auth_results)
    
    if token:
        all_results.extend(test_dashboard(token))
        all_results.extend(test_bookings(token))
        all_results.extend(test_inbox(token))
        all_results.extend(test_security(token))
    
    # Print results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"{'FEATURE':<40} {'STATUS':<10} {'NOTES':<30}")
    print("-"*80)
    
    for feature, status, notes in all_results:
        print(f"{feature:<40} {status:<10} {notes:<30}")
    
    # Calculate score
    passed = sum(1 for _, status, _ in all_results if status == "PASS")
    failed = sum(1 for _, status, _ in all_results if status == "FAIL")
    warned = sum(1 for _, status, _ in all_results if status == "WARN")
    total = len(all_results)
    
    print("="*80)
    print(f"PASS: {passed}/{total}")
    print(f"FAIL: {failed}/{total}")
    print(f"WARN: {warned}/{total}")
    print(f"Confidence: {int((passed/total)*10)}/10")
    print(f"\nReady for production: {'YES' if failed == 0 else 'NO'}")
    print("="*80)

if __name__ == "__main__":
    main()
