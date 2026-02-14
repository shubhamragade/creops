
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load env from backend/.env
load_dotenv("backend/.env")

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.models.form import Form, FormSubmission
from app.models.audit_log import AuditLog
from app.models.conversation import Conversation, Message
from app.core.config import settings

# Import models to ensure SQLAlchemy registration
from app.models.communication_log import CommunicationLog
from app.models.workspace import Workspace
from app.models.contact import Contact
from app.models.booking import Booking
from app.models.inventory import InventoryItem
from app.models.service import Service
from app.models.user import User
from app.db.session import SessionLocal

from app.services.email import (
    _send_smtp_email, 
    send_welcome_email, 
    send_booking_confirmation, 
    send_inventory_alert, 
    send_reply_email,
    send_form_magic_link,
    send_booking_reminder
)

async def verify_smtp():
    print("--- 1. Testing Raw SMTP Connection ---")
    log_data = {"workspace_id": 1, "type": "test_verification"}
    await _send_smtp_email(
        to_email=settings.SMTP_USER, # Send to self
        subject="CareOps SMTP Test",
        html_content="<h1>SMTP Configured Successfully</h1>",
        log_data=log_data
    )
    print("[OK] Test email function called (Check logs)")

async def verify_flows():
    print("\n--- 2. verifying Business Flows (Simulated) ---")
    
    # Welcome
    print("Triggering Welcome Email...")
    # Need a valid contact email. existing data?
    # Let's use 'inquiry@test.com' if it exists or create dummy
    # Actually `send_welcome_email` queries DB.
    # We should ensure 'inquiry@test.com' exists.
    # We can rely on Flow 2 data or create clean.
    await send_welcome_email("inquiry@test.com")
    
    # Inventory Alert
    print("Triggering Inventory Alert...")
    # Need item 1
    await send_inventory_alert(1)
    
    # Confirmation
    print("Triggering Booking Confirmation...")
    await send_booking_confirmation(1)

    # Form Link
    print("Triggering Form Link...")
    await send_form_magic_link(1)

    # Reminder
    print("Triggering Reminder...")
    await send_booking_reminder(1)

def check_logs():
    print("\n--- 3. Verifying Database Logs ---")
    db = SessionLocal()
    try:
        logs = db.query(CommunicationLog).order_by(CommunicationLog.id.desc()).limit(5).all()
        print(f"{'ID':<5} | {'Type':<20} | {'Status':<10} | {'Provider':<10} | {'Recipient'}")
        print("-" * 80)
        for log in logs:
            # provider field might not be in model if it wasn't there before?
            # Model definition needs checking. 
            # If 'provider' column doesn't exist, code might fail or generic kwarg.
            # Assuming 'CommunicationLog' has 'provider' or we just check status.
            # Wait, I added `provider="smtp"` in `_send_smtp_email`. 
            # Does the model support it?
            # If not, that line will crash.
            # I must check `app/models/communication_log.py`.
            # provider = getattr(log, "provider", "N/A") 
            # Provider column doesn't exist in MVP schema.
            print(f"{log.id:<5} | {log.type:<20} | {log.status:<10} | {log.recipient_email}")
            
    finally:
        db.close()

async def main():
    await verify_smtp()
    await verify_flows()
    check_logs()

if __name__ == "__main__":
    if not settings.SMTP_HOST:
        print("FAIL: SMTP_HOST not set in settings")
        sys.exit(1)
    if not settings.SMTP_PASSWORD:
        print("FAIL: SMTP_PASSWORD not set")
        sys.exit(1)
        
    print(f"Configured SMTP: {settings.SMTP_HOST}:{settings.SMTP_PORT} as {settings.SMTP_USER}")
    asyncio.run(main())
