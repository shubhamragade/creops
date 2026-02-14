
import requests
import json

BASE_URL = "http://localhost:8001"
OWNER_EMAIL = "owner@careops.com"
OWNER_PASS = "owner123"

def run():
    print(">>> 1. Login")
    s = requests.Session()
    res = s.post(f"{BASE_URL}/api/login", data={"username": OWNER_EMAIL, "password": OWNER_PASS})
    if res.status_code != 200:
        print(f"Login Failed: {res.text}")
        return
    token = res.json().get('access_token')
    headers = {"Authorization": f"Bearer {token}"}
    
    res_me = s.get(f"{BASE_URL}/api/users/me", headers=headers)
    ws_id = res_me.json()['workspace']['id'] # Or equivalent parsing from previous steps if this fails
    # Based on previous step, this might fail if 'workspace' key is missing. 
    # Let's use the safer parsing logic from before.
    data = res_me.json()
    if 'workspace' in data: ws_id = data['workspace']['id']
    elif 'workspace_id' in data: ws_id = data['workspace_id']
    else: ws_id = 1 # Fallback
    
    print(f"Checking Integration for Workspace ID: {ws_id}")

    # I can't query the DB directly easily without imports, but I can check specific endpoints?
    # Or just use a python script that imports app.models like I did for verification tasks?
    # Actually, importing app code in these scripts works because I'm running them in the backend env content.
    # But usually I run them as 'python tests/...' which might have path issues if not set up.
    # The previous scripts used 'requests' which is external.
    # To check DB, I should use the backend code directly if possible, or add an endpoint?
    # Waiting... I can just use the provided 'deps' in a script if I add the path.
    
    # Better yet, let's just attempt to hit the 'send email' endpoint and see the specific error DETAIL.
    # The failure logs in dashboard already say "Failed".
    # I want to KNOW if EmailIntegration exists.
    
    # Is there a settings endpoint that shows integration status?
    # Usually /api/settings or /api/workspaces/me?
    res_ws = s.get(f"{BASE_URL}/api/workspaces/{ws_id}", headers=headers) # Guessing endpoint
    # If that fails, I'll try to just read the table via a script that imports models.
    # Let's write a script that imports models.
    
    pass

if __name__ == "__main__":
    # We will use the 'script with imports' approach since we are in the environment
    import sys
    import os
    sys.path.append(os.getcwd())
    
    from app.db.session import SessionLocal
    from app.models.email_integration import EmailIntegration
    from app.models.communication_log import CommunicationLog
    
    db = SessionLocal()
    try:
        user_ws_id = 1 # Assuming ID 1 for 'demo-spa' or 'owner' default
        # Let's try to find the workspace ID for owner@careops.com
        from app.models.user import User
        user = db.query(User).filter(User.email == "owner@careops.com").first()
        if user:
            user_ws_id = user.workspace_id
            print(f"Owner Workspace ID: {user_ws_id}")
            
        integration = db.query(EmailIntegration).filter(
            EmailIntegration.workspace_id == user_ws_id,
            EmailIntegration.provider == "google",
            EmailIntegration.is_active == True
        ).first()
        
        if integration:
            print(f"SUCCESS: Found Active Integration for {integration.email}")
            print(f" - Expires At: {integration.expires_at}")
        else:
            print("FAILURE: No Active Email Integration Found.")
            
        # Also check logs
        logs = db.query(CommunicationLog).filter(
            CommunicationLog.workspace_id == user_ws_id,
            CommunicationLog.status == "failed"
        ).limit(5).all()
        
        print(f"\nRecent Failures ({len(logs)}):")
        for log in logs:
            print(f" - {log.type}: {log.error_message}")
            
    finally:
        db.close()
