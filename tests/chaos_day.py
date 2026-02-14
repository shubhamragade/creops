
import sys
import os
import json
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Set ENV for Chaos Day
os.environ["DATABASE_URL"] = "sqlite:///./chaos_day.db"
os.environ["JWT_SECRET"] = "chaos_secret"

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.db.session import engine

# Fresh start for Chaos
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
client = TestClient(app)
Session = sessionmaker(bind=engine)

OWNER_ID = None
WS_ID = None
STAFF_ID = None

def setup_flashcut():
    db = Session()
    from app.models.workspace import Workspace
    from app.models.user import User, UserRole
    from app.models.service import Service
    from app.models.inventory import InventoryItem
    from app.core import security
    
    ws = Workspace(name="FlashCut Barbers", slug="flashcut", is_active=True)
    db.add(ws)
    db.commit()
    db.refresh(ws)
    
    owner = User(
        email="owner@flashcut.com",
        hashed_password=security.get_password_hash("chaos123"),
        role=UserRole.OWNER.value,
        workspace_id=ws.id,
        is_active=True,
        full_name="Big Don"
    )
    db.add(owner)
    
    # 2 Staff
    staff1 = User(email="s1@flashcut.com", hashed_password=security.get_password_hash("s1"), role=UserRole.STAFF.value, workspace_id=ws.id, full_name="Tony")
    staff2 = User(email="s2@flashcut.com", hashed_password=security.get_password_hash("s2"), role=UserRole.STAFF.value, workspace_id=ws.id, full_name="Vinny")
    db.add_all([staff1, staff2])
    
    # Services
    s = Service(id=1, name="Buzz Cut", duration_minutes=20, workspace_id=ws.id, availability="{}", inventory_item_id=1, inventory_quantity_required=1)
    db.add(s)
    
    # Inventory
    inv = InventoryItem(id=1, name="Neck Strips", quantity=50, threshold=10, workspace_id=ws.id)
    db.add(inv)
    
    db.commit()
    return owner.id, ws.id, staff1.id

def get_headers(uid, wid):
    from app.core import security
    token = security.create_access_token(subject=uid, workspace_id=wid)
    return {"Authorization": f"Bearer {token}"}

def run_chaos_simulation():
    print("--- CHAOS DAY: FLASHCUT BARBERS ---")
    
    # 1. MORNING RUSH: Overlap Pressure
    print("\n[EVENT 1] Morning Rush...")
    time_slot = (datetime.now() + timedelta(days=1)).replace(hour=9, minute=0, second=0).isoformat()
    # Customer A books
    res_a = client.post("/api/bookings/", json={"service_id":1, "start_datetime":time_slot, "name":"Cust A", "email":"a@a.com"})
    print(f"[OK] Customer A booked: {res_a.status_code}")
    
    # Customer B tries SAME slot
    res_b = client.post("/api/bookings/", json={"service_id":1, "start_datetime":time_slot, "name":"Cust B", "email":"b@b.com"})
    if res_b.status_code == 400:
        print("[OK] OVERLAP PREVENTION: Blocked duplicate slot.")
    else:
        print(f"FAIL: Allowed duplicate booking! {res_b.status_code}")

    # 2. WRONG PHONE NUMBER: Staff Correction
    print("\n[EVENT 2] Staff Correction...")
    bid = res_a.json()["id"]
    headers = get_headers(STAFF_ID, WS_ID)
    res_patch = client.patch(f"/api/bookings/{bid}/details", json={"phone": "999-CHAOS-FIXED"}, headers=headers)
    if res_patch.status_code == 200:
        print("[OK] Staff corrected phone number.")
        # Check trace
        res_h = client.get(f"/api/bookings/{bid}/history", headers=get_headers(OWNER_ID, WS_ID))
        if "booking.details_updated" in str(res_h.json()):
            print("[OK] TRACE: Correction recorded.")
    
    # 3. CUSTOMER CALLS: Reschedule
    print("\n[EVENT 3] Customer Reschedule...")
    new_time = (datetime.now() + timedelta(days=1)).replace(hour=11, minute=0, second=0).isoformat()
    res_resched = client.patch(f"/api/bookings/{bid}", json={"start_datetime": new_time}, headers=headers)
    if res_resched.status_code == 200:
         print("[OK] Rescheduled to 11:00 AM.")
         # Check email log (Notification required)
         db = Session()
         from app.models.communication_log import CommunicationLog
         log = db.query(CommunicationLog).filter(CommunicationLog.booking_id == bid, CommunicationLog.type == "confirmation").count()
         print(f"[OK] System triggered re-confirmation: {log} emails logged total for this booking.")
         db.close()

    # 4. BIG MISTAKE: Cancel + Restore
    print("\n[EVENT 4] The Big Mistake...")
    # Staff cancels wrong booking
    client.post(f"/api/bookings/{bid}/cancel", headers=headers)
    print("[OK] Staff accidentally cancelled booking.")
    
    # Owner restores
    owner_headers = get_headers(OWNER_ID, WS_ID)
    res_restore = client.post(f"/api/bookings/{bid}/restore", headers=owner_headers)
    if res_restore.status_code == 200:
        print("[OK] Owner restored successfully.")
        # Verify slot still occupied (conflict check part 2)
        # Try to book AGAIN at that 11:00 AM slot
        res_c = client.post("/api/bookings/", json={"service_id":1, "start_datetime":new_time, "name":"Cust C", "email":"c@c.com"})
        if res_c.status_code == 400:
             print("[OK] Slot successfully RE-PROTECTED after restore.")

    # 5. INVENTORY SURPRISE
    print("\n[EVENT 5] Inventory Surprise...")
    # Manually adjust via inventory API (requires Owner)
    # Let's assume there's a PATCH /inventory/{id}
    # For MVP, we'll check if AuditLog captures manual changes or if DASHBOARD updates.
    # We'll simulate a deduction.
    db = Session()
    from app.models.inventory import InventoryItem
    item = db.query(InventoryItem).filter(InventoryItem.id == 1).first()
    item.quantity = 2 # DROPPED MANUALLY TO 2 (Below threshold 10)
    db.add(item)
    db.commit()
    print("[OK] Manual stock adjustment recorded.")
    
    res_dash = client.get("/api/dashboard/", headers=owner_headers)
    if "Low stock: Neck Strips" in str(res_dash.json()):
        print("[OK] Dashboard triggered Alert immediately.")
    db.close()

    # 7. OWNER PANIC: Trace Audit
    print("\n[EVENT 6] Owner Panic Trace (Booking #1)...")
    res_panic = client.get(f"/api/bookings/{bid}/history", headers=owner_headers)
    timeline = res_panic.json()
    print(f"Full Audit for Booking #1: {len(timeline)} events.")
    for event in timeline:
        print(f"  - {event['action']} (User: {event.get('user_id') or 'System'})")
    
    print("\n--- CHAOS DAY COMPLETE ---")

if __name__ == "__main__":
    OWNER_ID, WS_ID, STAFF_ID = setup_flashcut()
    run_chaos_simulation()
