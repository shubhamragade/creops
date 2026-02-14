
import sys
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Override DB for testing - MUST happen before imports that use get_db or models if they bind globally
# But app.db.base binds to settings.DATABASE_URL usually. 
# We'll set env var.
os.environ['DATABASE_URL'] = 'sqlite:///./test_cancellation.db'

from app.main import app
from app.api.deps import get_db
from app.db.base import Base
from app.models.workspace import Workspace
from app.models.service import Service
from app.models.inventory import InventoryItem
from app.models.booking import Booking, BookingStatus
from app.models.contact import Contact
from app.models.audit_log import AuditLog
from app.core.security_utils import generate_cancel_token

# Setup Test DB
DATABASE_URL = "sqlite:///./test_cancellation.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def setup_data():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    
    # 1. Workspace
    ws = Workspace(
        name="Test WS", 
        slug="test-ws"
    )
    db.add(ws)
    db.commit()
    db.refresh(ws)
    
    # 2. Inventory
    item = InventoryItem(
        workspace_id=ws.id,
        name="Test Item",
        quantity=10,
        threshold=2
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    
    # 3. Service linking to Inventory
    svc = Service(
        workspace_id=ws.id,
        name="Test Service",
        duration_minutes=60,
        inventory_item_id=item.id,
        inventory_quantity_required=2
    )
    db.add(svc)
    db.commit()
    db.refresh(svc)
    
    # 4. Booking
    contact = Contact(workspace_id=ws.id, email="customer@example.com", full_name="John Doe")
    db.add(contact)
    db.commit()
    
    booking = Booking(
        workspace_id=ws.id,
        service_id=svc.id,
        contact_id=contact.id,
        start_time=datetime.now(timezone.utc) + timedelta(days=1),
        end_time=datetime.now(timezone.utc) + timedelta(days=1, hours=1),
        status=BookingStatus.CONFIRMED.value
    )
    db.add(booking)
    
    # Deduct inventory manually to simulate booking creation logic (since we are testing cancel, not create here)
    item.quantity -= 2 # 10 -> 8
    db.add(item)
    
    db.commit()
    db.refresh(booking)
    
    return db, booking.id, item.id

def test_public_cancellation():
    print("\n=== Test Public Cancellation ===")
    
    # Setup
    db, booking_id, item_id = setup_data()
    
    # Verify Initial State
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    print(f"Initial Inventory: {item.quantity} (Should be 8)")
    assert item.quantity == 8
    
    # Generate Token
    token = generate_cancel_token(booking_id)
    print(f"Generated Token: {token}")
    
    # Act: Call Cancel Endpoint
    response = client.post(f"/api/bookings/{booking_id}/cancel?token={token}")
    
    print(f"Response: {response.status_code} - {response.json()}")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    
    # Verify DB State
    db.expire_all()
    
    # 1. Status
    updated_booking = db.query(Booking).filter(Booking.id == booking_id).first()
    print(f"Booking Status: {updated_booking.status}")
    assert updated_booking.status == BookingStatus.CANCELLED.value
    
    # 2. Inventory Return
    updated_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    print(f"Updated Inventory: {updated_item.quantity} (Should be 10)")
    assert updated_item.quantity == 10
    
    # 3. Audit Log
    log = db.query(AuditLog).filter(
        AuditLog.booking_id == booking_id,
        AuditLog.action == "inventory.returned"
    ).first()
    assert log is not None
    print(f"Audit Log Found: {log.action} - {log.details}")
    
    # Test Idempotency
    resp2 = client.post(f"/api/bookings/{booking_id}/cancel?token={token}")
    assert resp2.json()["status"] == "already_cancelled"
    
    # Test Invalid Token
    random_id = booking_id + 999
    bad_token = generate_cancel_token(random_id) # Valid signature, wrong ID for this URL if we swapped
    # Or just garbage
    resp3 = client.post(f"/api/bookings/{booking_id}/cancel?token=invalid_token")
    assert resp3.status_code == 401
    
    print("\n[PASS] Public Cancellation Logic Verified")

if __name__ == "__main__":
    test_public_cancellation()
