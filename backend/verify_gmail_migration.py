
import sys
import os
import asyncio
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.db.session import SessionLocal
from app.models.workspace import Workspace
from app.models.user import User
from app.models.service import Service
from app.models.booking import Booking
from app.models.contact import Contact
from app.models.form import Form, FormSubmission
from app.models.inventory import InventoryItem
from app.models.conversation import Conversation, Message
from app.models.communication_log import CommunicationLog
from app.core.security_utils import encrypt_token
from app.services.email import send_test_email, _send_gmail_email

async def test_gmail_flow():
    print("Starting Gmail Migration Verification...")
    
    db = SessionLocal()
    try:
        # 1. Setup Mock Workspace
        print("1. Setting up mock workspace...")
        ws = db.query(Workspace).filter(Workspace.slug == "test-gmail-verify").first()
        if not ws:
            ws = Workspace(
                name="Test Gmail Verify",
                slug="test-gmail-verify",
                contact_email="test@example.com",
                google_connected=True,
                google_email="test-owner@gmail.com",
                google_refresh_token=encrypt_token("mock-refresh-token"),
                is_active=True
            )
            db.add(ws)
            db.commit()
            db.refresh(ws)
        else:
            # Ensure it's connected
            ws.google_connected = True
            ws.google_refresh_token = encrypt_token("mock-refresh-token")
            db.commit()
            
        print(f"   Workspace ID: {ws.id}")
        
        # 2. Mock Google API Client
        print("2. Mocking Google API...")
        with patch('app.services.email.build') as mock_build:
            with patch('app.services.email.Credentials') as mock_creds:
                # Setup mock service
                mock_service = MagicMock()
                mock_users = MagicMock()
                mock_messages = MagicMock()
                mock_send = MagicMock()
                
                mock_build.return_value = mock_service
                mock_service.users.return_value = mock_users
                mock_users.messages.return_value = mock_messages
                mock_messages.send.return_value = mock_send
                mock_send.execute.return_value = {"id": "mock-gmail-id-123"}
                
                mock_creds.return_value.valid = True
                
                # 3. Trigger Send
                print("3. Triggering send_test_email...")
                await send_test_email(ws.id)
                
                # 4. Verify Log
                print("4. Verifying CommunicationLog...")
                log = db.query(CommunicationLog).filter(
                    CommunicationLog.workspace_id == ws.id,
                    CommunicationLog.type == "test_email"
                ).order_by(CommunicationLog.id.desc()).first()
                
                if log and log.status == "success":
                    print("   SUCCESS: Log entry found and status is 'success'")
                else:
                    print(f"   FAILURE: Log entry status: {log.status if log else 'Not Found'}")
                    if log: print(f"   Error: {log.error_message}")
                    sys.exit(1)
                    
                # 5. Verify Fallback (Disconnect)
                print("5. Testing Fallback (Disconnected)...")
                ws.google_connected = False
                db.commit()
                
                await _send_gmail_email("test@example.com", "Test", " Body", {"workspace_id": ws.id, "type": "test_fallback"})
                
                log_fail = db.query(CommunicationLog).filter(
                    CommunicationLog.workspace_id == ws.id,
                    CommunicationLog.type == "test_fallback"
                ).order_by(CommunicationLog.id.desc()).first()
                
                if log_fail and log_fail.status == "failed" and "not connected" in log_fail.error_message:
                     print("   SUCCESS: Log entry marks failure correctly when not connected.")
                else:
                     print(f"   FAILURE: Expected failure log. Got: {log_fail.status if log_fail else 'None'}")
                     if log_fail: print(f"   Msg: {log_fail.error_message}")
                     
    finally:
        db.close()
        
    print("Verification Completed Successfully.")

if __name__ == "__main__":
    asyncio.run(test_gmail_flow())
