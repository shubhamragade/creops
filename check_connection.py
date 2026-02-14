import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.db.session import SessionLocal
from app.models.user import User  # Fix for relationship loading
from app.models.workspace import Workspace
from app.models.email_integration import EmailIntegration
from sqlalchemy import text

def check_connection():
    db = SessionLocal()
    try:
        print("--- Checking Workspaces ---")
        workspaces = db.query(Workspace).all()
        for w in workspaces:
            print(f"Workspace: {w.name} (ID: {w.id})")
            print(f"  Google Connected: {w.google_connected}")
            print(f"  Google Email: {w.google_email}")
            print(f"  Refresh Token Present: {bool(w.google_refresh_token)}")
            
        print("\n--- Checking Email Integrations ---")
        integrations = db.query(EmailIntegration).all()
        for i in integrations:
             print(f"Integration ID: {i.id}, WS ID: {i.workspace_id}, Email: {i.email}, Active: {i.is_active}")

        print("\n--- Checking Recent Comm Logs (Raw SQL) ---")
        result = db.execute(text("SELECT id, type, status, error_message, recipient_email FROM communication_logs ORDER BY created_at DESC LIMIT 5"))
        for row in result:
            print(f"Log: {row}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_connection()
