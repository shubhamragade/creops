
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
from app.models.audit_log import AuditLog
from app.models.booking import Booking

# Create Tables (Ensure AuditLog exists in simulation.db)
Base.metadata.create_all(bind=engine)

# Setup Test Cilent
client = TestClient(app)

def run_verification():
    print("\n>>> VERIFICATION: BOOKING HISTORY & TRACE")
    
    # 1. Login as Owner (reuse existing if possible, or create new)
    # Let's assume Workspace 1 exists from previous sims.
    # Getting owner token is hard without knowing credentials.
    # We will "Backdoor" a token or use the same credentials as Simulation.
    owner_email = "owner-urbanglow-test@example.com"
    # We need to find a valid user to log in. 
    # Let's use the DB to find an owner.
    db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    from app.models.user import User, UserRole
    owner = db.query(User).filter(User.role == UserRole.OWNER.value).first()
    
    if not owner:
        print("FAIL: No owner found in DB. Run simulation first?")
        return
        
    # We can't login without password.
    # We will generate a token directly using `security.create_access_token`
    from app.core import security
    access_token = security.create_access_token(subject=owner.id, workspace_id=owner.workspace_id)
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print(f"[OK] Authenticated as Owner ID {owner.id}")
    
    # 2. Get Service
    from app.models.service import Service
    service = db.query(Service).filter(Service.workspace_id == owner.workspace_id).first()
    if not service:
        print("FAIL: No service found")
        return
        
    print(f"[OK] Service Found: {service.name}")

    # 3. Create Booking
    start_time = (datetime.now() + timedelta(days=5)).isoformat()
    booking_data = {
        "service_id": service.id,
        "start_datetime": start_time,
        "name": "History Test",
        "email": "history@example.com",
        "phone": "5550001111"
    }
    
    print(">>> Creating Booking...")
    res = client.post("/api/bookings", json=booking_data)
    if res.status_code != 200:
        print(f"FAIL: Create Booking {res.text}")
        return
    
    booking_id = res.json()["id"]
    print(f"[OK] Booking Created ID {booking_id}")
    
    # 4. Verify Audit Log (Creation)
    # Check DB directly first
    audit = db.query(AuditLog).filter(
        AuditLog.booking_id == booking_id,
        AuditLog.action == "booking.created"
    ).first()
    
    if audit:
        print(f"[OK] Audit Log Found: {audit.action} - {audit.details}")
    else:
        print("FAIL: No 'booking.created' audit log found")
        
    # 5. Cancel Booking
    print(">>> Cancelling Booking...")
    res = client.post(f"/api/bookings/{booking_id}/cancel", headers=headers)
    if res.status_code != 200:
        print(f"FAIL: Cancel Booking {res.text}")
        return
    print("[OK] Booking Cancelled")
    
    # 6. Verify Audit Log (Cancellation)
    audit_c = db.query(AuditLog).filter(
        AuditLog.booking_id == booking_id,
        AuditLog.action == "booking.cancelled"
    ).first()
    
    if audit_c:
         print(f"[OK] Audit Log Found: {audit_c.action} - {audit_c.details} by User {audit_c.user_id}")
    else:
         print("FAIL: No 'booking.cancelled' audit log found")

    # 7. Test History Endpoint
    print(">>> Testing GET /history endpoint...")
    res = client.get(f"/api/bookings/{booking_id}/history", headers=headers)
    if res.status_code == 200:
        history = res.json()
        print(f"[OK] History Endpoint Returned {len(history)} items")
        for item in history:
            print(f" - {item['created_at']}: {item['type'].upper()} {item['action']}")
            
        # Verify content
        actions = [h['action'] for h in history]
        if "booking.created" in actions and "booking.cancelled" in actions:
            print("[SUCCESS] Full Trace Verified")
        else:
            print(f"FAIL: Missing actions in history. Got: {actions}")
            
    else:
        print(f"FAIL: History Endpoint {res.status_code} {res.text}")

if __name__ == "__main__":
    run_verification()
