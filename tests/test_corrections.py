
import sys
import os
import time
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Set ENV for Testing
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
    print("\n>>> VERIFICATION: SAFE CORRECTIONS (RESCHEDULE)")
    
    # 1. Login as Owner
    db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    from app.models.user import User, UserRole
    owner = db.query(User).filter(User.role == UserRole.OWNER.value).first()
    
    from app.core import security
    access_token = security.create_access_token(subject=owner.id, workspace_id=owner.workspace_id)
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Cleanup previous test data
    db.query(Booking).filter(
        Booking.contact.has(Contact.email.in_(["corrections@example.com", "target@example.com"]))
    ).delete(synchronize_session=False)
    db.commit()

    from app.models.service import Service
    service = db.query(Service).filter(Service.workspace_id == owner.workspace_id).first()

    # 2. Create Initial Booking
    start_time = (datetime.now() + timedelta(days=40)).replace(hour=10, minute=0, second=0)
    booking_data = {
        "service_id": service.id,
        "start_datetime": start_time.isoformat(),
        "name": "Correction Test",
        "email": "corrections@example.com",
        "phone": "5559998888"
    }
    
    res = client.post("/api/bookings", json=booking_data)
    booking_id = res.json()["id"]
    print(f"[OK] Created Booking {booking_id}")

    # 3. Reschedule Success
    print(">>> Testing Reschedule (Success)...")
    new_start = start_time + timedelta(hours=2)
    patch_data = {"start_datetime": new_start.isoformat()}
    
    res = client.patch(f"/api/bookings/{booking_id}", json=patch_data, headers=headers)
    if res.status_code == 200:
        print("[OK] Reschedule Success")
        # Verify Audit Log
        audit = db.query(AuditLog).filter(
            AuditLog.booking_id == booking_id,
            AuditLog.action == "booking.rescheduled"
        ).first()
        if audit:
            print(f"[OK] Audit Log Found: {audit.details}")
        else:
            print("FAIL: No audit log")
    else:
        print(f"FAIL: Reschedule {res.status_code} {res.text}")

    # 4. Reschedule Conflict
    print(">>> Testing Reschedule (Conflict)...")
    # Create another booking at the target time
    target_data = {
        "service_id": service.id,
        "start_datetime": (start_time + timedelta(days=1)).isoformat(),
        "name": "Target",
        "email": "target@example.com",
        "phone": "5551112222"
    }
    res_t = client.post("/api/bookings", json=target_data)
    target_start = start_time + timedelta(days=1)
    
    # Try to move original booking to target's slot
    res = client.patch(f"/api/bookings/{booking_id}", json={"start_datetime": target_start.isoformat()}, headers=headers)
    if res.status_code == 409:
        print("[OK] Conflict Blocked")
    else:
        print(f"FAIL: Conflict should have been blocked! Got {res.status_code}")

    # 5. Terminal State Block
    print(">>> Testing Terminal State Block...")
    # Complete the booking
    b = db.query(Booking).get(booking_id)
    b.status = BookingStatus.COMPLETED.value
    db.commit()
    
    res = client.patch(f"/api/bookings/{booking_id}", json={"start_datetime": start_time.isoformat()}, headers=headers)
    if res.status_code == 400:
        print("[OK] Terminal State Update Blocked")
    else:
        print(f"FAIL: Should block completed booking! Got {res.status_code}")

    # 6. Update Details
    print(">>> Testing Detail Updates...")
    detail_data = {"full_name": "Updated Name", "phone": "1234567890"}
    res = client.patch(f"/api/bookings/{booking_id}/details", json=detail_data, headers=headers)
    if res.status_code == 200:
        print("[OK] Details Updated")
        db.refresh(b.contact)
        if b.contact.full_name == "Updated Name":
            print("[OK] DB reflected changes")
        else:
            print(f"FAIL: Name is {b.contact.full_name}")
    else:
        print(f"FAIL: Detail Update {res.status_code} {res.text}")

if __name__ == "__main__":
    run_verification()
