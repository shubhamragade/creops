import sys
import os
from datetime import datetime, timedelta, timezone
import random

# Add parent directory to path to import app
sys.path.append(os.getcwd())

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.workspace import Workspace
from app.models.service import Service
from app.models.contact import Contact
from app.models.booking import Booking, BookingStatus
from app.models.form import Form
from app.models.inventory import InventoryItem
from app.models.conversation import Conversation, Message
from app.models.email_integration import EmailIntegration
from app.core.security import get_password_hash

def seed_data():
    db = SessionLocal()
    try:
        user_email = "shubhamragade2003@gmail.com"
        print(f"Checking for user {user_email}...")
        
        user = db.query(User).filter(User.email == user_email).first()
        
        if not user:
            print("User not found. Creating user and workspace...")
            # Create Workspace
            workspace = Workspace(
                name="Luminous Wellness Spa",
                business_email=user_email,
                phone="(415) 555-0328",
                address="450 Sutter St, Suite 1200, San Francisco, CA 94108"
            )
            db.add(workspace)
            db.commit()
            db.refresh(workspace)
            
            # Create User
            user = User(
                email=user_email,
                hashed_password=get_password_hash("Demo@2026!"),
                full_name="Dr. Sophia Carter",
                role=UserRole.OWNER,
                workspace_id=workspace.id
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Created user {user.full_name} and workspace {workspace.name}")
        else:
            print(f"User found: {user.full_name}")
            if not user.workspace:
                print("User has no workspace. Creating...")
                workspace = Workspace(
                    name="Luminous Wellness Spa",
                    business_email=user_email,
                    phone="(415) 555-0328",
                    address="450 Sutter St, Suite 1200, San Francisco, CA 94108"
                )
                db.add(workspace)
                db.commit()
                db.refresh(workspace)
                user.workspace_id = workspace.id
                db.add(user)
                db.commit()
            else:
                workspace = user.workspace
                print(f"Using existing workspace: {workspace.name}")
                if workspace.name != "Luminous Wellness Spa":
                    workspace.name = "Luminous Wellness Spa"
                    workspace.address = "450 Sutter St, Suite 1200, San Francisco, CA 94108"
                    workspace.phone = "(415) 555-0328"
                    db.add(workspace)
                    db.commit()
                    print("Updated workspace details to Luminous Wellness Spa")

        # Create Services
        services_data = [
            {"name": "Deep Tissue Massage", "duration": 60, "price": 120},
            {"name": "HydraFacial Signature", "duration": 45, "price": 180},
            {"name": "Aromatherapy Massage", "duration": 60, "price": 110},
            {"name": "Hot Stone Therapy", "duration": 90, "price": 160},
            {"name": "Chemical Peel", "duration": 30, "price": 150}
        ]
        
        # Default availability: Mon-Sun, 9am - 7pm
        default_availability = {
            "mon": ["09:00-19:00"],
            "tue": ["09:00-19:00"],
            "wed": ["09:00-19:00"],
            "thu": ["09:00-19:00"],
            "fri": ["09:00-19:00"],
            "sat": ["10:00-18:00"],
            "sun": ["10:00-16:00"]
        }

        created_services = []
        for s_data in services_data:
            service = db.query(Service).filter(Service.name == s_data["name"], Service.workspace_id == workspace.id).first()
            if not service:
                service = Service(
                    name=s_data["name"],
                    duration_minutes=s_data["duration"],
                    workspace_id=workspace.id,
                    availability=default_availability
                    # inventory stuff can be null for now
                )
                db.add(service)
                db.commit()
                db.refresh(service)
                print(f"Created service: {service.name}")
            else:
                # Update availability if missing or different (for demo fix)
                if not service.availability or service.availability == {}:
                    service.availability = default_availability
                    db.add(service)
                    db.commit()
                    print(f"Updated availability for service: {service.name}")
            
            created_services.append(service)

        # Create Staff
        staff_data = [
            {"name": "Michael Chen", "email": "michael@luminous.demo", "role": UserRole.STAFF},
            {"name": "Sarah Jenkins", "email": "sarah@luminous.demo", "role": UserRole.STAFF},
            {"name": "Emma Wright", "email": "emma@luminous.demo", "role": UserRole.STAFF}
        ]
        
        staff_members = [user] # Include owner
        for st_data in staff_data:
            staff = db.query(User).filter(User.email == st_data["email"]).first()
            if not staff:
                staff = User(
                    email=st_data["email"],
                    hashed_password=get_password_hash("password"),
                    full_name=st_data["name"],
                    role=st_data["role"],
                    workspace_id=workspace.id
                )
                db.add(staff)
                db.commit()
                db.refresh(staff)
                print(f"Created staff: {staff.full_name}")
            staff_members.append(staff)

        # Create Contacts
        contacts_data = [
            {"name": "Emily Blunt", "email": "emily@example.com", "phone": "555-0101"},
            {"name": "John Doe", "email": "john.doe@example.com", "phone": "555-0102"},
            {"name": "Alice Smith", "email": "alice@example.com", "phone": "555-0103"},
            {"name": "Robert Brown", "email": "robert@example.com", "phone": "555-0104"},
            {"name": "Linda Davis", "email": "linda@example.com", "phone": "555-0105"}
        ]
        
        created_contacts = []
        for c_data in contacts_data:
            contact = db.query(Contact).filter(Contact.email == c_data["email"], Contact.workspace_id == workspace.id).first()
            if not contact:
                contact = Contact(
                    full_name=c_data["name"],
                    email=c_data["email"],
                    phone=c_data["phone"],
                    workspace_id=workspace.id,
                    status="manual" 
                )
                db.add(contact)
                db.commit()
                db.refresh(contact)
                print(f"Created contact: {contact.full_name}")
            created_contacts.append(contact)

        # Create Bookings (Past and Future)
        now = datetime.now(timezone.utc)
        
        # Check if we already have bookings to avoid duplicates if run twice
        existing_bookings = db.query(Booking).filter(Booking.workspace_id == workspace.id).count()
        if existing_bookings < 5:
            print("Seeding bookings...")
            
            # Past bookings (completed)
            for i in range(5):
                service = random.choice(created_services)
                staff = random.choice(staff_members)
                contact = random.choice(created_contacts)
                
                days_ago = random.randint(1, 30)
                start_hour = random.randint(9, 16)
                
                start_time = now - timedelta(days=days_ago)
                start_time = start_time.replace(hour=start_hour, minute=0, second=0, microsecond=0)
                end_time = start_time + timedelta(minutes=service.duration_minutes)
                
                booking = Booking(
                    start_time=start_time,
                    end_time=end_time,
                    status=BookingStatus.COMPLETED,
                    workspace_id=workspace.id,
                    service_id=service.id,
                    contact_id=contact.id,
                    staff_id=staff.id
                )
                db.add(booking)
            
            # Future bookings (confirmed/pending)
            for i in range(5):
                service = random.choice(created_services)
                staff = random.choice(staff_members)
                contact = random.choice(created_contacts)
                
                days_ahead = random.randint(1, 14)
                start_hour = random.randint(9, 16)
                
                start_time = now + timedelta(days=days_ahead)
                start_time = start_time.replace(hour=start_hour, minute=0, second=0, microsecond=0)
                end_time = start_time + timedelta(minutes=service.duration_minutes)
                
                booking = Booking(
                    start_time=start_time,
                    end_time=end_time,
                    status=random.choice([BookingStatus.CONFIRMED, BookingStatus.PENDING]),
                    workspace_id=workspace.id,
                    service_id=service.id,
                    contact_id=contact.id,
                    staff_id=staff.id
                )
                db.add(booking)
            
            db.commit()
            print("Created random bookings.")
        else:
            print("Bookings already exist, skipping.")

        # Create Conversations (Inbox)
        print("Seeding conversations...")
        inbox_data = [
            {
                "contact_email": "emily@example.com",
                "subject": "Question about Hot Stone Therapy",
                "messages": [
                    {"sender": "emily@example.com", "content": "Hi, do I need to bring anything for the Hot Stone session?", "internal": False},
                    {"sender": "shubhamragade2003@gmail.com", "content": "Hi Emily! No need to bring anything. We provide robes and everything you need.", "internal": False},
                    {"sender": "emily@example.com", "content": "Great, see you tomorrow!", "internal": False}
                ]
            },
            {
                "contact_email": "john.doe@example.com",
                "subject": "Reschedule request",
                "messages": [
                    {"sender": "john.doe@example.com", "content": "Hello, something came up. Can I verify my appointment time?", "internal": False},
                    {"sender": "shubhamragade2003@gmail.com", "content": "Hi John, you are booked for tomorrow at 2 PM. Would you like to reschedule?", "internal": False}
                ]
            },
            {
                "contact_email": "alice@example.com",
                "subject": "Gift Card Inquiry",
                "messages": [
                    {"sender": "alice@example.com", "content": "Do you sell gift cards online?", "internal": False}
                ]
            }
        ]

        for conv_data in inbox_data:
            contact = db.query(Contact).filter(Contact.email == conv_data["contact_email"], Contact.workspace_id == workspace.id).first()
            if contact:
                # Check if conversation exists
                existing_conv = db.query(Conversation).filter(Conversation.contact_id == contact.id, Conversation.subject == conv_data["subject"]).first()
                
                if not existing_conv:
                    new_conv = Conversation(
                        workspace_id=workspace.id,
                        contact_id=contact.id,
                        subject=conv_data["subject"],
                        created_at=datetime.now(timezone.utc) - timedelta(days=1),
                        last_message_at=datetime.now(timezone.utc)
                    )
                    db.add(new_conv)
                    db.commit()
                    db.refresh(new_conv)
                    
                    for msg in conv_data["messages"]:
                        new_msg = Message(
                            conversation_id=new_conv.id,
                            sender_email=msg["sender"],
                            content=msg["content"],
                            is_internal=msg["internal"],
                            created_at=datetime.now(timezone.utc)
                        )
                        db.add(new_msg)
                    db.commit()
                    print(f"Created conversation: {conv_data['subject']}")
                else:
                     print(f"Conversation '{conv_data['subject']}' already exists.")


        # Create Intake Form
        print("Seeding intake form...")
        intake_form = db.query(Form).filter(Form.workspace_id == workspace.id, Form.type == "intake").first()
        if not intake_form:
            intake_form = Form(
                workspace_id=workspace.id,
                name="New Client Intake",
                type="intake",
                is_public=True,
                fields=[
                    {
                        "name": "allergies",
                        "label": "Do you have any allergies?",
                        "type": "textarea",
                        "required": True,
                        "placeholder": "e.g. Latex, Nuts, specific oils"
                    },
                    {
                        "name": "medical_history",
                        "label": "Any medical conditions we should know about?",
                        "type": "textarea",
                        "required": False,
                        "placeholder": "e.g. Back pain, pregnancy, recent surgery"
                    },
                    {
                        "name": "skincare_goals",
                        "label": "What are your primary skincare goals?",
                        "type": "select",
                        "required": False,
                        "options": ["Hydration", "Anti-aging", "Acne treatment", "Relaxation"]
                    },
                    {
                        "name": "pressure_preference",
                        "label": "Preferred massage pressure?",
                        "type": "radio",
                        "required": True,
                        "options": ["Light", "Medium", "Firm", "Deep Tissue"]
                    }
                ]
            )
            db.add(intake_form)
            db.commit()
            print("Created 'New Client Intake' form.")
        else:
            print("Intake form already exists.")



    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error seeding data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
