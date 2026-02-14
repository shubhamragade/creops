# SURGICAL FIX P0-3: Safe seed data for demo
# Import from base.py first to ensure all models load in correct order
from app.db.base import Base  # This imports all models in correct order
from app.db.session import SessionLocal
from app.models.workspace import Workspace
from app.models.user import User
from app.models.service import Service
from app.models.contact import Contact
from app.models.booking import Booking, BookingStatus
from app.models.inventory import InventoryItem
from app.core.security import get_password_hash
from datetime import datetime, timedelta, timezone

def seed_demo_data():
    """Seed minimal safe data for demo without breaking existing data."""
    db = SessionLocal()
    
    try:
        # Check if already seeded
        existing_ws = db.query(Workspace).filter(Workspace.slug == "demo-spa").first()
        if existing_ws:
            print("Demo data already exists. Skipping seed.")
            return
        
        # 1. Create Workspace
        workspace = Workspace(
            name="Demo Spa & Wellness",
            slug="demo-spa",
            contact_email="owner@demo-spa.com",
            address="123 Wellness Way, Mumbai, Maharashtra 400001, India",
            timezone="Asia/Kolkata",
            is_active=True
        )
        db.add(workspace)
        db.flush()
        
        # 2. Create Owner User
        owner = User(
            email="owner@careops.com",
            hashed_password=get_password_hash("owner123"),
            role="owner",
            workspace_id=workspace.id,
            is_active=True
        )
        db.add(owner)
        
        # 3. Create Staff User
        staff = User(
            email="staff@careops.com",
            hashed_password=get_password_hash("staff123"),
            role="staff",
            workspace_id=workspace.id,
            is_active=True
        )
        db.add(staff)
        db.flush()
        
        # 4. Create Services
        massage_service = Service(
            workspace_id=workspace.id,
            name="Deep Tissue Massage",
            duration_minutes=60,
            availability={
                "mon": ["09:00-17:00"],
                "tue": ["09:00-17:00"],
                "wed": ["09:00-17:00"],
                "thu": ["09:00-17:00"],
                "fri": ["09:00-17:00"]
            }
        )
        facial_service = Service(
            workspace_id=workspace.id,
            name="Facial Treatment",
            duration_minutes=45,
            availability={
                "mon": ["10:00-16:00"],
                "tue": ["10:00-16:00"],
                "wed": ["10:00-16:00"],
                "thu": ["10:00-16:00"],
                "fri": ["10:00-16:00"]
            }
        )
        db.add_all([massage_service, facial_service])
        db.flush()
        
        # 5. Create Contacts
        contact1 = Contact(
            workspace_id=workspace.id,
            email="john.doe@example.com",
            full_name="John Doe",
            phone="+1234567890"
        )
        contact2 = Contact(
            workspace_id=workspace.id,
            email="jane.smith@example.com",
            full_name="Jane Smith",
            phone="+0987654321"
        )
        db.add_all([contact1, contact2])
        db.flush()
        
        # 6. Create Bookings
        now = datetime.now(timezone.utc)
        
        # Today's confirmed booking
        booking1 = Booking(
            workspace_id=workspace.id,
            service_id=massage_service.id,
            contact_id=contact1.id,
            start_time=now + timedelta(hours=3),
            end_time=now + timedelta(hours=4),
            status=BookingStatus.CONFIRMED.value
        )
        
        # Tomorrow's booking
        booking2 = Booking(
            workspace_id=workspace.id,
            service_id=facial_service.id,
            contact_id=contact2.id,
            start_time=now + timedelta(days=1, hours=2),
            end_time=now + timedelta(days=1, hours=2, minutes=45),
            status=BookingStatus.CONFIRMED.value
        )
        
        # Past completed booking
        booking3 = Booking(
            workspace_id=workspace.id,
            service_id=massage_service.id,
            contact_id=contact1.id,
            start_time=now - timedelta(days=2),
            end_time=now - timedelta(days=2, hours=-1),
            status=BookingStatus.COMPLETED.value
        )
        
        db.add_all([booking1, booking2, booking3])
        db.flush()
        
        # 7. Create Inventory Items
        oil = InventoryItem(
            workspace_id=workspace.id,
            name="Massage Oil",
            quantity=3,  # Below threshold
            threshold=5
        )
        towels = InventoryItem(
            workspace_id=workspace.id,
            name="Towels",
            quantity=20,
            threshold=10
        )
        db.add_all([oil, towels])
        
        db.commit()
        print(f"V Demo data seeded successfully!")
        print(f"  Workspace: {workspace.slug}")
        print(f"  Owner: owner@careops.com / owner123")
        print(f"  Staff: staff@careops.com / staff123")
        print(f"  Services: {massage_service.name}, {facial_service.name}")
        print(f"  Bookings: {len([booking1, booking2, booking3])}")
        
    except Exception as e:
        db.rollback()
        print(f"X Seed failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_data()
