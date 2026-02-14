
import sys
import os
import time
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Set ENV for Testing BEFORE importing app
os.environ["DATABASE_URL"] = "sqlite:///./simulation.db"
os.environ["JWT_SECRET"] = "testsecret"

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.db.session import engine
from app.models.booking import Booking, BookingStatus
from app.models.contact import Contact
from app.models.audit_log import AuditLog

# Create Tables
Base.metadata.create_all(bind=engine)

# Setup Test Cilent
client = TestClient(app)

def run_verification():
    print("\n>>> VERIFICATION: UNDO / RESTORE ACTIONS")
    
    # 1. Login as Owner
    # Reuse logic from history test to get owner
    db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    from app.models.user import User, UserRole
    owner = db.query(User).filter(User.role == UserRole.OWNER.value).first()
    
    if not owner:
        print("FAIL: No owner found")
        return
        
    from app.core import security
    access_token = security.create_access_token(subject=owner.id, workspace_id=owner.workspace_id)
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 2. Setup: Create a Booking to Cancel
    from app.models.service import Service
    service = db.query(Service).filter(Service.workspace_id == owner.workspace_id).first()
    
    # Cleanup previous test data to avoid conflicts
    db.query(Booking).filter(
        Booking.contact.has(Contact.email.in_(["restore@example.com", "blocker@example.com"]))
    ).delete(synchronize_session=False)
    db.commit()

    # Use a far future date to avoid overlap with existing simulation data
    import random
    random_day = random.randint(30, 60)
    start_time = (datetime.now() + timedelta(days=random_day)).replace(hour=10, minute=0, second=0).isoformat()
    booking_data = {
        "service_id": service.id,
        "start_datetime": start_time,
        "name": "Restore Test",
        "email": "restore@example.com",
        "phone": "5550002222"
    }
    
    res = client.post("/api/bookings", json=booking_data)
    if res.status_code != 200:
        print(f"FAIL: Create Booking {res.text}")
        return
    booking_id = res.json()["id"]
    print(f"[OK] Created Booking {booking_id}")
    
    # 3. Cancel It
    res = client.post(f"/api/bookings/{booking_id}/cancel", headers=headers)
    if res.status_code != 200:
        print(f"FAIL: Cancel {res.text}")
        return
    print("[OK] Cancelled Booking")
    
    # 4. Restore It (Happy Path)
    print(">>> Testing Restore (Happy Path)...")
    res = client.post(f"/api/bookings/{booking_id}/restore", headers=headers)
    if res.status_code == 200:
        print("[OK] Restore Success")
        
        # Verify DB Status
        b = db.query(Booking).get(booking_id)
        if b.status == BookingStatus.CONFIRMED.value:
            print("[OK] DB Status is CONFIRMED")
        else:
            print(f"FAIL: DB Status is {b.status}")
            
        # Verify Audit Log
        audit = db.query(AuditLog).filter(
            AuditLog.booking_id == booking_id,
            AuditLog.action == "booking.restored"
        ).first()
        if audit:
            print(f"[OK] Audit Log Found: {audit.action}")
        else:
            print("FAIL: No audit log for restore")
            
    else:
        print(f"FAIL: Restore Request {res.status_code} {res.text}")

    # 5. Restore Again (Idempotency)
    print(">>> Testing Restore (Idempotency)...")
    res = client.post(f"/api/bookings/{booking_id}/restore", headers=headers)
    if res.status_code == 200:
         if res.json().get("status") == "already_confirmed":
             print("[OK] Idempotency Check Passed")
         else:
             print(f"FAIL: Unexpected response for active booking: {res.json()}")
    else:
         print(f"FAIL: Idempotency Request {res.status_code} {res.text}")

    # 6. Conflict Test
    # Create another booking in same slot
    # First, cancel the original again to free the slot? 
    # Or try to restore a different cancelled booking into an occupied slot.
    
    # Let's cancel the original again.
    client.post(f"/api/bookings/{booking_id}/cancel", headers=headers)
    print("[OK] Cancelled Booking Again")
    
    # Create overlapping booking
    overlap_data = {
        "service_id": service.id,
        "start_datetime": start_time, # SAME TIME
        "name": "Blocker",
        "email": "blocker@example.com",
        "phone": "5550003333"
    }
    print(">>> Creating Overlapping Booking...")
    res = client.post("/api/bookings", json=overlap_data)
    if res.status_code == 200:
        print("[OK] Created Blocker Booking")
    else:
        print(f"FAIL: Create Blocker {res.text}")
        return
        
    # Try Restore Original
    print(">>> Testing Restore (Conflict)...")
    res = client.post(f"/api/bookings/{booking_id}/restore", headers=headers)
    if res.status_code == 409:
        print("[OK] Restore Blocked (409 Conflict) as expected")
    else:
        print(f"FAIL: Restore should have failed! Got {res.status_code} {res.text}")

    # 7. Retry Communication (Bonus)
    # Find a log
    from app.models.communication_log import CommunicationLog
    log = db.query(CommunicationLog).filter(CommunicationLog.booking_id == booking_id).first()
    if log:
        print(f">>> Testing Retry Communication ID {log.id}...")
        res = client.post(f"/api/communications/{log.id}/retry", headers=headers)
        if res.status_code == 200:
            print("[OK] Retry Queued")
            db.refresh(log)
            if log.status == "retrying":
                print("[OK] Log Status Updated to 'retrying'")
            else:
                print(f"FAIL: Log status is {log.status}")
        else:
            print(f"FAIL: Retry Request {res.status_code} {res.text}")
    else:
        print("SKIP: No communication log found to retry")

if __name__ == "__main__":
    run_verification()
