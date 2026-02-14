from app.db.session import SessionLocal
from app.db.base import Base
from app.models.workspace import Workspace
from app.models.user import User
from app.models.service import Service
from app.models.contact import Contact
from app.models.booking import Booking, BookingStatus
from app.models.inventory import InventoryItem
from app.core.security import get_password_hash
from datetime import datetime, timedelta

db = SessionLocal()

# 1. Workspace
ws = Workspace(name="Test Spa", slug="test-spa", is_active=True, contact_email="owner@test.com")
db.add(ws)
db.flush()

# 2. Users
owner = User(
    email="owner@careops.com",
    hashed_password=get_password_hash("owner123"),
    role="owner",
    workspace_id=ws.id,
    is_active=True
)
staff = User(
    email="staff@careops.com",
    hashed_password=get_password_hash("staff123"),
    role="staff",
    workspace_id=ws.id,
    is_active=True
)
db.add_all([owner, staff])

# 3. Service
svc = Service(
    workspace_id=ws.id,
    name="Initial Massage",
    duration_minutes=60,
    availability={"mon": ["09:00-17:00"], "tue": ["09:00-17:00"], "wed": ["09:00-17:00"], "thu": ["09:00-17:00"], "fri": ["09:00-17:00"]}
)
db.add(svc)
db.flush()

# 4. Contact
contact = Contact(workspace_id=ws.id, email="customer@example.com", full_name="John Doe")
db.add(contact)
db.flush()

# 5. Booking
booking = Booking(
    workspace_id=ws.id,
    service_id=svc.id,
    contact_id=contact.id,
    start_time=datetime.utcnow() + timedelta(hours=2),
    end_time=datetime.utcnow() + timedelta(hours=3),
    status=BookingStatus.CONFIRMED.value
)
db.add(booking)

# 6. Inventory (for alerts)
item = InventoryItem(workspace_id=ws.id, name="Oil", quantity=2, threshold=5)
db.add(item)

db.commit()
print(f"SEED_COMPLETE: WS_ID={ws.id}, SVC_ID={svc.id}, BOOKING_ID={booking.id}")
db.close()
