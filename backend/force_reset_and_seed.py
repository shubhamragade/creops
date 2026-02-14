
import sys
import os
from datetime import datetime, timedelta, timezone
from sqlalchemy import text

# Add backend to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.core.security import get_password_hash
# Import all models to ensure metadata is loaded
from app.models import workspace, user, service, contact, booking, inventory, conversation, communication_log, audit_log, form

def force_reset_and_seed():
    print(">>> FORCE RESETTING DATABASE...")
    
    # 1. Drop All Tables
    Base.metadata.drop_all(bind=engine)
    print(">>> Tables Dropped.")
    
    # 2. Create All Tables
    Base.metadata.create_all(bind=engine)
    print(">>> Tables Re-Created.")
    
    # 3. Seed Professional Demo Data
    print(">>> Seeding Professional Demo Data...")
    db = SessionLocal()
    try:
        # -- Workspace --
        ws = workspace.Workspace(
            name="CareOps Demo Spa",
            slug="demo-spa",
            contact_email="admin@careops.demo",
            timezone="Asia/Kolkata",
            is_active=True
        )
        db.add(ws)
        db.flush()
        
        # -- Owner --
        owner = user.User(
            email="admin@careops.demo",
            hashed_password=get_password_hash("demo123"), # Simple password
            role="owner",
            full_name="Demo Admin",
            workspace_id=ws.id,
            is_active=True
        )
        db.add(owner)
        
        # -- Staff --
        staff = user.User(
            email="staff@careops.demo",
            hashed_password=get_password_hash("demo123"),
            role="staff",
            full_name="Sarah Staff",
            workspace_id=ws.id,
            is_active=True
        )
        db.add(staff)
        db.flush()
        
        # -- Services --
        s1 = service.Service(
            workspace_id=ws.id,
            name="Full Body Massage",
            duration_minutes=60,
            availability={"mon": ["09:00-17:00"], "tue": ["09:00-17:00"], "wed": ["09:00-17:00"], "thu": ["09:00-17:00"], "fri": ["09:00-17:00"]}
        )
        s2 = service.Service(
            workspace_id=ws.id,
            name="Facial Rejuvenation",
            duration_minutes=45,
            availability={"mon": ["10:00-18:00"], "wed": ["10:00-18:00"], "fri": ["10:00-18:00"]}
        )
        db.add_all([s1, s2])
        db.flush()
        
        # -- Contacts --
        c1 = contact.Contact(workspace_id=ws.id, email="alice.client@example.com", full_name="Alice Client", phone="555-0101")
        c2 = contact.Contact(workspace_id=ws.id, email="bob.customer@example.com", full_name="Bob Customer", phone="555-0102")
        db.add_all([c1, c2])
        db.flush()
        
        # -- Bookings --
        now = datetime.now(timezone.utc)
        
        # Upcoming (Tomorrow)
        b1 = booking.Booking(
            workspace_id=ws.id, service_id=s1.id, contact_id=c1.id,
            start_time=now + timedelta(days=1, hours=2),
            end_time=now + timedelta(days=1, hours=3),
            status="confirmed"
        )
        
        # Completed (Yesterday)
        b2 = booking.Booking(
            workspace_id=ws.id, service_id=s2.id, contact_id=c2.id,
            start_time=now - timedelta(days=1, hours=4),
            end_time=now - timedelta(days=1, hours=3, minutes=15),
            status="completed"
        )
        
        db.add_all([b1, b2])
        db.flush()
        
        # -- Inventory --
        i1 = inventory.InventoryItem(workspace_id=ws.id, name="Massage Oil (Liters)", quantity=5, threshold=2)
        i2 = inventory.InventoryItem(workspace_id=ws.id, name="Face Masks", quantity=15, threshold=20) # Low stock
        db.add_all([i1, i2])
        
        # -- Inbox / Conversations --
        conv = conversation.Conversation(
            workspace_id=ws.id, contact_id=c1.id, subject="Question about booking",
            created_at=now - timedelta(hours=2),
            last_message_at=now - timedelta(hours=2),
            last_message_is_internal=False,
            is_paused=False
        )
        db.add(conv)
        db.flush()
        
        msg = conversation.Message(
            conversation_id=conv.id,
            sender_email=c1.email,
            content="Hi, do I need to bring anything for the massage?",
            is_internal=False,
            created_at=now - timedelta(hours=2)
        )
        db.add(msg)
        
        db.commit()
        print(">>> SUCCESS: Database reset and seeded with PROFESSIONAL demo data.")
        print(f"Login: {owner.email} / demo123")
        
    except Exception as e:
        db.rollback()
        print(f">>> ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    force_reset_and_seed()
