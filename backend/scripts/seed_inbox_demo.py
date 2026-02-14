
import sys
import os
import datetime
from datetime import timedelta, timezone

# Add backend to path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.workspace import Workspace
from app.models.user import User
from app.models.contact import Contact
from app.models.conversation import Conversation, Message

def seed_inbox():
    db = SessionLocal()
    try:
        print("Seeding Inbox for Demo...")
        
        # Get Workspace
        workspace = db.query(Workspace).filter(Workspace.slug == "demo-spa").first()
        if not workspace:
            print("Demo workspace not found! Run auto-seed first.")
            return

        # Get Owner
        owner = db.query(User).filter(User.role == "owner", User.workspace_id == workspace.id).first()
        
        # 1. New Inquiry (Unanswered)
        # -------------------------------------------------
        contact1 = db.query(Contact).filter(Contact.email == "sarah.jones@example.com").first()
        if not contact1:
            contact1 = Contact(
                workspace_id=workspace.id,
                email="sarah.jones@example.com",
                first_name="Sarah",
                last_name="Jones",
                phone="+15550101",
                status="new"
            )
            db.add(contact1)
            db.commit()
            db.refresh(contact1)
            
        # Check if convo exists
        convo1 = db.query(Conversation).filter(Conversation.contact_id == contact1.id).first()
        if not convo1:
            convo1 = Conversation(
                workspace_id=workspace.id,
                contact_id=contact1.id,
                subject="Question about membership prices",
                created_at=datetime.datetime.now(timezone.utc) - timedelta(hours=2),
                last_message_at=datetime.datetime.now(timezone.utc) - timedelta(hours=2),
                last_message_is_internal=False, # Unanswered
                is_paused=False
            )
            db.add(convo1)
            db.commit()
            db.refresh(convo1)
            
            msg1 = Message(
                conversation_id=convo1.id,
                sender_email=contact1.email,
                content="Hi, I was looking at your website but couldn't find the monthly membership rates. Could you send them over?",
                is_internal=False,
                created_at=datetime.datetime.now(timezone.utc) - timedelta(hours=2)
            )
            db.add(msg1)
            db.commit()
            print("Created: Inquiry from Sarah Jones")

        # 2. Booking Confirmation (Ongoing)
        # -------------------------------------------------
        contact2 = db.query(Contact).filter(Contact.email == "mike.brown@example.com").first()
        if not contact2:
            contact2 = Contact(
                workspace_id=workspace.id,
                email="mike.brown@example.com",
                first_name="Mike",
                last_name="Brown",
                phone="+15550102",
                status="contacted"
            )
            db.add(contact2)
            db.commit()
            db.refresh(contact2)

        convo2 = db.query(Conversation).filter(Conversation.contact_id == contact2.id).first()
        if not convo2:
            now = datetime.datetime.now(timezone.utc)
            convo2 = Conversation(
                workspace_id=workspace.id,
                contact_id=contact2.id,
                subject="Rescheduling my appointment",
                created_at=now - timedelta(days=1),
                last_message_at=now - timedelta(minutes=30),
                last_message_is_internal=True, # We replied
                is_paused=True # Automation paused because we replied
            )
            db.add(convo2)
            db.commit()
            db.refresh(convo2)
            
            # Msg 1: Client asks
            msg2a = Message(
                conversation_id=convo2.id,
                sender_email=contact2.email,
                content="Hey, can I move my booking to next Tuesday?",
                is_internal=False,
                created_at=now - timedelta(days=1)
            )
            
            # Msg 2: We reply
            msg2b = Message(
                conversation_id=convo2.id,
                sender_email=owner.email if owner else "staff@careops.com",
                content="Sure Mike, Tuesday at 2 PM is available. Shall I book that for you?",
                is_internal=True,
                created_at=now - timedelta(days=1, minutes=10)
            )
            
            # Msg 3: Client confirms
            msg2c = Message(
                conversation_id=convo2.id,
                sender_email=contact2.email,
                content="Yes please!",
                is_internal=False,
                created_at=now - timedelta(minutes=45)
            )

            # Msg 4: We confirm
            msg2d = Message(
                conversation_id=convo2.id,
                sender_email=owner.email if owner else "staff@careops.com",
                content="Done! You are all set for Tuesday at 2 PM.",
                is_internal=True,
                created_at=now - timedelta(minutes=30)
            )
            
            db.add_all([msg2a, msg2b, msg2c, msg2d])
            db.commit()
            print("Created: Discussion with Mike Brown")

        # 3. Old Inquiry
        # -------------------------------------------------
        # Use existing John Doe if available
        contact3 = db.query(Contact).filter(Contact.email == "john.doe@example.com").first()
        if contact3:
            convo3 = db.query(Conversation).filter(Conversation.contact_id == contact3.id).first()
            if not convo3:
                 convo3 = Conversation(
                    workspace_id=workspace.id,
                    contact_id=contact3.id,
                    subject="Thank you",
                    created_at=datetime.datetime.now(timezone.utc) - timedelta(days=5),
                    last_message_at=datetime.datetime.now(timezone.utc) - timedelta(days=5),
                    last_message_is_internal=False,
                    is_paused=False
                 )
                 db.add(convo3)
                 db.commit()
                 
                 msg3 = Message(
                    conversation_id=convo3.id,
                    sender_email=contact3.email,
                    content="Great service yesterday, thanks!",
                    is_internal=False,
                    created_at=datetime.datetime.now(timezone.utc) - timedelta(days=5)
                 )
                 db.add(msg3)
                 db.commit()
                 print("Created: Feedback from John Doe")

        print("Inbox seeded successfully!")

    except Exception as e:
        print(f"Error seeding inbox: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_inbox()
