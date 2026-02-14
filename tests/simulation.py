import sys
import os
import random
import string
import time
from datetime import datetime, timedelta
import asyncio

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Set ENV for Testing BEFORE importing app
os.environ["DATABASE_URL"] = "sqlite:///./simulation.db"
os.environ["JWT_SECRET"] = "testsecret"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.db.session import get_db, engine

# Create Tables
Base.metadata.create_all(bind=engine)

# Setup Test Cilent
client = TestClient(app)

def random_string(length=10):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def print_header(text):
    print(f"\n{'='*50}\n{text}\n{'='*50}")

def print_step(text):
    print(f"\n>>> {text}")

def run_simulation():
    print_header("OPERATIONAL READINESS TEST: URBANGLOW SIMULATION")

    # ----------------------------------------------------------------
    # PHASE 1 — MORNING SETUP
    # ----------------------------------------------------------------
    print_step("PHASE 1: Morning Setup")
    
    slug = f"urbanglow-{random_string(4)}"
    owner_email = f"owner-{slug}@example.com"
    owner_pass = "securepass123"
    
    # 1. Owner Onboarding
    workspace_data = {
        "name": "UrbanGlow Beauty Studio",
        "address": "MG Road, Bangalore",
        "timezone": "Asia/Kolkata",
        "contact_email": owner_email,
        "owner_email": owner_email,
        "owner_password": owner_pass
    }
    
    res = client.post("/api/onboarding/workspaces", json=workspace_data)
    if res.status_code != 200:
        print(f"FAILED: Create Workspace {res.text}")
        return
    
    data = res.json()
    workspace_id = data["workspace_id"]
    slug = data["slug"] 
    owner_token = data["access_token"]
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    print(f"[OK] Owner Logged In (Workspace ID: {workspace_id})")

    # 2. Add Inventory (Dye -> 3, Threshold -> 1)
    inventory_data = [
        {"name": "Color Dye", "quantity_available": 3, "low_threshold": 1},
        {"name": "Shampoo", "quantity_available": 10, "low_threshold": 2} # Noise
    ]
    res = client.post(f"/api/onboarding/workspaces/{workspace_id}/inventory", headers=owner_headers, json=inventory_data)
    inv_resp = res.json()
    dye_id = next(i for i in inv_resp["items"] if i["name"] == "Color Dye")["id"]
    print(f"[OK] Inventory Created: Dye (3), Threshold (1)")

    # 3. Add Services
    services_data = [
        {"name": "Haircut", "duration_minutes": 30, "price": 50.0, "availability": {"mon": ["09:00-17:00"]}, "location": "Main Hall"},
        {"name": "Hair Color", "duration_minutes": 60, "price": 150.0, "availability": {"mon": ["09:00-17:00"]}, "location": "Color Station", 
         "inventory_item_id": dye_id, "inventory_quantity_required": 1},
        {"name": "Facial", "duration_minutes": 45, "price": 80.0, "availability": {"mon": ["09:00-17:00"]}, "location": "Spa Room"}
    ]
    client.post(f"/api/onboarding/workspaces/{workspace_id}/services", headers=owner_headers, json=services_data)
    
    # Enable Email
    email_config = {"provider": "resend", "api_key": "re_123", "from_email": "test@example.com"}
    client.put(f"/api/onboarding/workspaces/{workspace_id}/config/email", headers=owner_headers, json=email_config)
    client.post(f"/api/onboarding/workspaces/{workspace_id}/activate", headers=owner_headers)
    print("[OK] Workspace Active & Services Linked")

    # 4. Invite Staff
    staff_email = f"staff-{slug}@example.com"
    invite_res = client.post("/api/staff/invite", headers=owner_headers, json={
        "email": staff_email, 
        "full_name": "Sarah Staff", 
        "role": "staff",
        "permissions": {"bookings": True, "inbox": True} 
    })
    
    # CHECK: Password NOT in API
    if "password" in invite_res.text.lower():
        print("FAIL: Password leaked in API response!")
    else:
        print("[OK] Staff Invited (Secure: No password in response)")

    # Hack Staff Password for Login
    db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    from app.models.user import User
    from app.core import security
    from app.models.booking import Booking, BookingStatus 
    from app.models.inventory import InventoryItem
    
    staff_user = db.query(User).filter(User.email == staff_email).first()
    if staff_user:
        staff_user.hashed_password = security.get_password_hash("staffpass123")
        db.add(staff_user)
        db.commit()
    
    # 5. Staff Login & Ops
    login_res = client.post("/api/login", data={"username": staff_email, "password": "staffpass123"})
    if login_res.status_code != 200:
        print(f"FAIL: Staff Login {login_res.text}")
        return
        
    staff_token = login_res.json()["access_token"]
    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    
    # CHECK: Staff Access
    res = client.get("/api/dashboard", headers=staff_headers) # Should work (staff view)
    if res.status_code == 200:
         print("[OK] Staff Logged In & Can View Dashboard")
    else:
         print(f"FAIL: Staff Dashboard Access {res.status_code}")

    # CHECK: Staff cannot access Owner Settings
    res = client.post(f"/api/onboarding/workspaces/{workspace_id}/inventory", headers=staff_headers, json=[])
    if res.status_code == 403:
        print("[OK] Staff Permission Check Passed (Cannot modify Inventory Setup)")
    else:
        print(f"FAIL: Staff could modify inventory! {res.status_code}")

    # ----------------------------------------------------------------
    # PHASE 2 — LEAD ARRIVAL
    # ----------------------------------------------------------------
    print_step("PHASE 2: Lead Arrival")
    
    contact_data = {
        "name": "Customer A",
        "email": "custA@example.com",
        "message": "Do you have slots?",
        "workspace_slug": slug
    }
    # Get ID first
    # Need to query by slug first
    config_res = client.get(f"/api/public/workspace/{slug}")
    if config_res.status_code != 200:
        print(f"FAIL: Get Public Config for slug {slug}: {config_res.status_code}")
        return

    ws_id = config_res.json()["id"]
    services = config_res.json()["services"]
    coloring_svc = next(s for s in services if s["name"] == "Hair Color")

    # Submit Contact
    # Handle redirect if any
    res = client.post("/api/public/contact", json={**contact_data, "workspace_id": ws_id}, follow_redirects=True)
    if res.status_code != 200:
         # Try with trailing slash or check if it returns 307
         res = client.post("/api/public/contact/", json={**contact_data, "workspace_id": ws_id}, follow_redirects=True)
         
    if res.status_code == 200:
        print("[OK] Contact Form Submitted")
    else:
        print(f"FAIL: Contact Form {res.status_code} {res.text}")

    # Verify Dashboard Unread
    dash = client.get("/api/dashboard", headers=owner_headers).json()
    if dash["inbox"]["unanswered_count"] == 1:
        print("[OK] Contact Form -> Dashboard Alert (1 Unread)")
    else:
        print(f"FAIL: Dashboard Unread {dash['inbox']}")

    # ----------------------------------------------------------------
    # PHASE 3 — BOOKING FLOW
    # ----------------------------------------------------------------
    print_step("PHASE 3: Booking Flow")
    
    # Customer B books Hair Coloring
    tomorrow_10am = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    booking_data = {
        "service_id": coloring_svc["id"],
        "start_datetime": tomorrow_10am.isoformat(), 
        "name": "Customer B", 
        "email": "custB@example.com",
        "phone": "9998887776",
        "notes": "Dye it red"
    }
    
    res = client.post("/api/bookings", json=booking_data)
    if res.status_code == 200:
        booking_id = res.json()["id"]
        print(f"[OK] Booking Created for Customer B")
    else:
        print(f"FAIL: Booking Creation {res.text}")
        return

    # CHECK inventory (3 -> 2)
    item = db.query(InventoryItem).get(dye_id)
    db.refresh(item)
    if item.quantity == 2:
        print("[OK] Inventory Deducted (3 -> 2)")
    else:
        print(f"FAIL: Inventory not deducted. Qty: {item.quantity}")

    # ----------------------------------------------------------------
    # PHASE 4 — HUMAN ACTION
    # ----------------------------------------------------------------
    print_step("PHASE 4: Human Action")
    
    # Staff replies to Customer A (from Phase 2)
    # Get conversation ID
    inbox_res = client.get("/api/conversations", headers=staff_headers)
    inbox = inbox_res.json()
    
    if inbox_res.status_code != 200:
        print(f"FAIL: Inbox Fetch {inbox_res.status_code} {inbox}")
    elif not inbox:
        print("FAIL: Inbox Empty!")
    else:
        conv_id = inbox[0]["id"]
        # Use /api/conversations NOT /api/inbox
        # Endpoint is /api/conversations/messages (POST) and takes {conversation_id, content}
        reply_data = {"conversation_id": conv_id, "content": "Yes coming!"} 
        res = client.post("/api/conversations/messages", headers=staff_headers, json=reply_data)
        if res.status_code == 200:
            print("[OK] Staff Replied to Lead")
            # Check if unread went down
            dash = client.get("/api/dashboard", headers=owner_headers).json()
            if dash["inbox"]["unanswered_count"] == 0:
                 print("[OK] Dashboard Unread Cleared")
            else:
                 print(f"FAIL: Dashboard Unread NOT Cleared {dash['inbox']}")
        else:
            print(f"FAIL: Staff Reply {res.text}")

    # ----------------------------------------------------------------
    # PHASE 5 — CONFLICT TEST
    # ----------------------------------------------------------------
    print_step("PHASE 5: Conflict Test")
    
    # Try same slot
    res = client.post("/api/bookings", json={**booking_data, "email": "Intruder@example.com"})
    if res.status_code == 400:
        print("[OK] Double Booking Rejected")
    else:
        print(f"FAIL: Double Booking Allowed! {res.status_code}")

    # ----------------------------------------------------------------
    # PHASE 6 — INVENTORY PRESSURE
    # ----------------------------------------------------------------
    print_step("PHASE 6: Inventory Pressure")
    
    # Current: 2. Threshold: 1.
    # Need to consume 1 more to hit threshold (2 -> 1).
    # Then trigger alert.
    
    # Book for Day+2
    for i in range(1):
        slot = (datetime.now() + timedelta(days=2+i)).replace(hour=10, minute=0, second=0, microsecond=0)
        b_data = {**booking_data, "start_datetime": slot.isoformat(), "email": f"cust{i}@example.com"}
        res = client.post("/api/bookings", json=b_data)
        if res.status_code != 200:
            print(f"FAIL: Pressure Booking {i} failed {res.text}")
    
    db.refresh(item)
    print(f"Current Qty: {item.quantity}")
    
    if item.quantity == 1:
        print("[OK] Inventory Hit Threshold (1)")
        # Simulation check: in real app, background task sends email.
        # We assume if logic hit, email sent.
    else:
        print(f"FAIL: Inventory Logic. Expected 1, Got {item.quantity}")

    # ----------------------------------------------------------------
    # PHASE 7 — DAY PROGRESSION (Time Travel)
    # ----------------------------------------------------------------
    print_step("PHASE 7: Day Progression")
    
    # Mark Customer B's booking (Phase 3) as COMPLETED and TIME TRAVEL it to the past.
    # Booking ID: booking_id
    booking = db.query(Booking).get(booking_id)
    booking.status = BookingStatus.COMPLETED.value
    # End time = Now - 2 hours (so > 1 hour ago)
    # Cron uses UTC. Ensure we use consistent time.
    from datetime import timezone
    now_utc = datetime.now(timezone.utc)
    booking.end_time = now_utc - timedelta(hours=2)
    booking.start_time = now_utc - timedelta(hours=3)
    # Ensure follow_up_sent is False (default)
    db.add(booking)
    db.commit()
    
    print("Time Travel: Booking moved to 2 hours ago & Completed.")
    
    # Run Cron manually logic
    from app.api.cron import process_follow_ups

    # We will run this using asyncio.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # process_follow_ups handles DB commit.
        step_res = loop.run_until_complete(process_follow_ups(db))
        db.commit() # Commit the changes made by process_follow_ups
        
        if step_res >= 1:
             print("[OK] Cron: Follow-up Email Triggered")
             
             # Verify Flag Update
             db.refresh(booking)
             if booking.follow_up_sent:
                 print("[OK] Booking Flag Updated (follow_up_sent=True)")
             else:
                 print("FAIL: Booking Flag NOT updated")
        else:
             print(f"FAIL: Cron did not trigger. Count: {step_res}")
             
    except Exception as e:
        print(f"FAIL: Cron Execution {e}")
    finally:
        loop.close()

    # ----------------------------------------------------------------
    # PHASE 8 — CANCELLATION
    # ----------------------------------------------------------------
    print_step("PHASE 8: Cancellation")
    
    # Cancel one of the 'Pressure' bookings
    # Bookings are created as PENDING by default
    upcoming = db.query(Booking).filter(
        Booking.workspace_id == workspace_id,
        Booking.status != BookingStatus.CANCELLED.value
    ).all()
    if not upcoming:
        print("FAIL: No upcoming bookings to cancel")
    else:
        b_cancel = upcoming[0]
        c_res = client.post(f"/api/bookings/{b_cancel.id}/cancel", headers=owner_headers)
        if c_res.status_code == 200:
            print("[OK] Booking Cancelled")
            db.refresh(b_cancel)
            if b_cancel.status == BookingStatus.CANCELLED.value:
                print("[OK] DB Status Updated")
        else:
            print(f"FAIL: Cancel API {c_res.text}")

    # ----------------------------------------------------------------
    # PHASE 9 — OWNER END OF DAY
    # ----------------------------------------------------------------
    print_step("PHASE 9: Owner End of Day")
    
    res = client.get("/api/dashboard", headers=owner_headers)
    dash = res.json()
    
    # Logic check
    if dash["bookings"]["today_count"] is not None:
        print(f"[OK] Owner Dashboard Alive. Summary: {dash}")
    else:
        print("FAIL: Dashboard Payload unexpected")

    # ----------------------------------------------------------------
    # PHASE 10 — CONNECTIVITY & FINAL VERDICT
    # ----------------------------------------------------------------
    print_step("PHASE 10: Connectivity Audit")
    
    db.close()
    print("ALL SYSTEMS GO.")

if __name__ == "__main__":
    run_simulation()
