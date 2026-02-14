from app.db.base import Base
from app.db.session import SessionLocal
from app.models.communication_log import CommunicationLog
from sqlalchemy import desc

def check_logs():
    db = SessionLocal()
    try:
        logs = db.query(CommunicationLog).order_by(desc(CommunicationLog.created_at)).limit(20).all()
        with open("log_output.txt", "w") as f:
            f.write(f"{'ID':<5} | {'Recipient':<30} | {'Type':<15} | {'Status':<10} | {'Error'}\n")
            f.write("-" * 100 + "\n")
            for log in logs:
                f.write(f"{log.id:<5} | {log.recipient_email:<30} | {log.type:<15} | {log.status:<10} | {log.error_message or ''}\n")
    finally:
        db.close()

if __name__ == "__main__":
    check_logs()
