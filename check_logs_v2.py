import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.db.session import SessionLocal
from app.models.communication_log import CommunicationLog
from app.models.workspace import Workspace
from app.models.user import User
from app.models.contact import Contact
# Import Base to ensure registry is populated
from app.db.base import Base
from sqlalchemy import desc

def check_logs():
    db = SessionLocal()
    try:
        print("--- Checking Communication Logs ---")
        logs = db.query(CommunicationLog).order_by(desc(CommunicationLog.created_at)).limit(5).all()
        if not logs:
            print("No logs found.")
        for log in logs:
            print(f"ID: {log.id} | Type: {log.type} | Status: {log.status} | To: {log.recipient_email}")
            if log.error_message:
                print(f"   ERROR: {log.error_message}")
            
        print("\n--- Checking Workspace Connection ---")
        workspaces = db.query(Workspace).all()
        for w in workspaces:
            print(f"Workspace: {w.name} | Connected: {w.google_connected} | Email: {w.google_email}")
            print(f"   Scopes: {w.email_integration[0].scope if w.email_integration else 'N/A'}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_logs()
