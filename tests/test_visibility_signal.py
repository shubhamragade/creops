
import sys
import os
import json
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Set ENV for Testing
os.environ["DATABASE_URL"] = "sqlite:///./visibility_test.db"
os.environ["JWT_SECRET"] = "vis_secret"

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.db.session import engine

# Fresh start
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
client = TestClient(app)
Session = sessionmaker(bind=engine)

def get_auth_headers(user_id, workspace_id):
    from app.core import security
    token = security.create_access_token(subject=user_id, workspace_id=workspace_id)
    return {"Authorization": f"Bearer {token}"}

def test_dashboard_signal_prioritization():
    db = Session()
    from app.models.workspace import Workspace
    from app.models.user import User, UserRole
    from app.models.booking import Booking
    from app.models.service import Service
    from app.models.communication_log import CommunicationLog
    from app.models.audit_log import AuditLog
    from app.core import security
    
    # Setup Workspace 1 (Target)
    ws1 = Workspace(name="Spa A", slug="spa-a", is_active=True)
    db.add(ws1)
    db.commit()
    db.refresh(ws1)
    
    owner1 = User(email="o1@a.com", hashed_password=security.get_password_hash("p"), role=UserRole.OWNER.value, workspace_id=ws1.id, is_active=True, full_name="Owner A")
    db.add(owner1)
    db.commit()
    
    # Actions for WS 1
    # 1. Failed Email (High Priority)
    f1 = CommunicationLog(workspace_id=ws1.id, type="confirmation", recipient_email="fail@a.com", status="failed", error_message="SMTP down")
    db.add(f1)
    
    # 2. Recent Activity
    a1 = AuditLog(workspace_id=ws1.id, action="booking.created", booking_id=1, user_id=None) # System
    db.add(a1)
    
    # Setup Workspace 2 (Isolation Check)
    ws2 = Workspace(name="Spa B", slug="spa-b", is_active=True)
    db.add(ws2)
    db.commit()
    
    f2 = CommunicationLog(workspace_id=ws2.id, type="reminder", recipient_email="leak@b.com", status="failed")
    db.add(f2)
    db.commit()
    
    # Request Dashboard for WS 1
    headers = get_auth_headers(owner1.id, ws1.id)
    res = client.get("/api/dashboard/", headers=headers)
    assert res.status_code == 200
    data = res.json()
    
    # VERIFY PRIORITIZATION & SIGNAL
    print("\n--- Dashboard Signal Verification ---")
    
    # Failures
    failures = data.get("failures", [])
    print(f"Failures (WS1): {len(failures)}")
    assert len(failures) == 1
    assert failures[0]["recipient"] == "fail@a.com"
    
    # Attention Items
    attention = data.get("attention", [])
    print(f"Attention Items (WS1): {len(attention)}")
    # Should have a failure item
    failure_attention = [a for a in attention if a["type"] == "failure"]
    assert len(failure_attention) >= 1
    assert failure_attention[0]["action_type"] == "RETRY_EMAIL"
    assert failure_attention[0]["entity_id"] == f1.id
    
    # Recent Activity
    activity = data.get("recent_activity", [])
    print(f"Recent Activity (WS1): {len(activity)}")
    assert len(activity) == 1
    assert activity[0]["actor_name"] == "System"
    assert activity[0]["action"] == "booking.created"
    
    # ISOLATION
    # Ensure no data from WS2 leaked
    all_emails = [f["recipient"] for f in failures]
    assert "leak@b.com" not in all_emails
    print("[OK] Isolation Verified. No cross-workspace leakage found.")
    
    db.close()

if __name__ == "__main__":
    test_dashboard_signal_prioritization()
    print("\n--- ALL VISIBILITY TESTS PASSED ---")
