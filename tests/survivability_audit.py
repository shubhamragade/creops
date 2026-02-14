
import sys
import os
import json
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Set ENV for Testing
os.environ["DATABASE_URL"] = "sqlite:///./simulation_audit.db"
os.environ["JWT_SECRET"] = "testsecret"

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.db.session import engine

# Drop and Re-create for fresh state
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
client = TestClient(app)
Session = sessionmaker(bind=engine)

OWNER_ID = None
WS_ID = None

def setup_fresh_owner():
    db = Session()
    from app.models.workspace import Workspace
    from app.models.user import User, UserRole
    from app.models.service import Service
    from app.models.inventory import InventoryItem
    from app.core import security
    
    ws = Workspace(name="Audit Spa", slug="audit-spa", is_active=True)
    db.add(ws)
    db.commit()
    db.refresh(ws)
    
    owner = User(
        email="owner@audit.com",
        hashed_password=security.get_password_hash("password"),
        role=UserRole.OWNER.value,
        workspace_id=ws.id,
        is_active=True,
        full_name="Audit Owner"
    )
    db.add(owner)
    
    # Create Low stock item for Audit
    inv = InventoryItem(name="Oil", quantity=1, threshold=5, workspace_id=ws.id)
    db.add(inv)
    
    s = Service(name="Massage", duration_minutes=60, workspace_id=ws.id, availability="{}", inventory_item_id=1, inventory_quantity_required=1)
    db.add(s)
    
    db.commit()
    return owner.id, ws.id

def get_auth_headers(user_id, workspace_id):
    from app.core import security
    token = security.create_access_token(subject=user_id, workspace_id=workspace_id)
    return {"Authorization": f"Bearer {token}"}

def audit_p1():
    print("\n--- P1: OWNER DASHBOARD ---")
    headers = get_auth_headers(OWNER_ID, WS_ID)
    res = client.get("/api/dashboard/", headers=headers)
    if res.status_code == 200:
        d = res.json()
        print(f"[OK] Dashboard Stats: {json.dumps(d['bookings'], indent=1)}")
        if len(d['alerts']) > 0:
            print(f"[OK] Owner sees Alert: {d['alerts'][0]['message']}")
        else:
            print("FAIL: No inventory alerts found")

def audit_p2():
    print("\n--- P2: STAFF INVITE SECURITY ---")
    headers = get_auth_headers(OWNER_ID, WS_ID)
    res = client.post("/api/staff/invite", json={"email":"staff@audit.com", "permissions":{}}, headers=headers)
    if res.status_code == 200:
        print(f"[OK] Invite API: {res.json()['message']}")
        if "password" not in res.text:
            print("[OK] SECURITY: Credentials NOT in API response")

def audit_p3():
    print("\n--- P3: STAFF RESTRICTIONS ---")
    db = Session()
    from app.models.user import User
    staff = db.query(User).filter(User.email == "staff@audit.com").first()
    headers = get_auth_headers(staff.id, WS_ID)
    res = client.post("/api/staff/invite", json={}, headers=headers)
    if res.status_code == 403:
        print("[OK] Staff blocked from admin actions (403)")
    db.close()

def audit_p4():
    print("\n--- P4: CUSTOMER LIFECYCLE & TRACE ---")
    db = Session()
    from app.models.service import Service
    s = db.query(Service).first()
    time = (datetime.now() + timedelta(days=90)).isoformat()
    res = client.post("/api/bookings/", json={"service_id":s.id, "start_datetime":time, "name":"Cust", "email":"c@c.com"})
    bid = res.json()["id"]
    print(f"[OK] Booking {bid} created. Time: {time}")
    
    headers = get_auth_headers(OWNER_ID, WS_ID)
    res = client.get(f"/api/bookings/{bid}/history", headers=headers)
    if res.status_code == 200:
        actions = [h['action'] for h in res.json()]
        print(f"[OK] SURVIVABILITY TRACE: {actions}")
        if "inventory.deducted" in actions:
            print("[OK] Inventory movement captured in trace.")
    else:
        print(f"FAIL: History Trace {res.status_code} {res.text}")
    db.close()

def audit_p5():
    print("\n--- P5: RECOVERY ---")
    db = Session()
    from app.models.booking import Booking
    b = db.query(Booking).first()
    headers = get_auth_headers(OWNER_ID, WS_ID)
    # Cancel
    client.post(f"/api/bookings/{b.id}/cancel", headers=headers)
    # Restore
    res = client.post(f"/api/bookings/{b.id}/restore", headers=headers)
    if res.status_code == 200:
        print("[OK] Restore success")
        rh = client.get(f"/api/bookings/{b.id}/history", headers=headers)
        if "booking.restored" in str(rh.json()):
            print("[OK] Recovery recorded.")
    db.close()

if __name__ == "__main__":
    OWNER_ID, WS_ID = setup_fresh_owner()
    audit_p1()
    audit_p2()
    audit_p3()
    audit_p4()
    audit_p5()
    print("\n--- AUDIT COMPLETE ---")
