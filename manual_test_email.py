import sys
import os
import asyncio

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.db.session import SessionLocal
from app.services.email import send_test_email
from app.models.communication_log import CommunicationLog
from sqlalchemy import desc

async def run_test():
    print("Sending test email to workspace 1...")
    try:
        await send_test_email(1)
        print("Email function executed.")
    except Exception as e:
        print(f"Error executing function: {e}")

    # Check logs
    db = SessionLocal()
    try:
        log = db.query(CommunicationLog).order_by(desc(CommunicationLog.created_at)).first()
        if log:
            print(f"Latest Log ID: {log.id}")
            print(f"Type: {log.type}")
            print(f"Status: {log.status}")
            print(f"Error: {log.error_message}")
        else:
            print("No logs found.")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_test())
