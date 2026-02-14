
import requests
import json
import time

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
    slug = res.json().get('workspace_slug')
    
    # Get User Details for Workspace ID
    headers = {"Authorization": f"Bearer {token}"}
    res_me = s.get(f"{BASE_URL}/api/users/me", headers=headers)
    if res_me.status_code == 200:
        data = res_me.json()
        # 'workspace_id' is direct field in User model, not nested in 'workspace' dict?
        # Model: user.workspace_id. 
        # API: UserOut usually has workspace_id at top level.
        ws_id = data.get('workspace_id')
        if not ws_id and 'workspace' in data:
             ws_id = data['workspace']['id']
    else:
        # Fallback to public lookup
        res_ws = s.get(f"{BASE_URL}/api/public/workspace/{slug}")
        ws_id = res_ws.json()['id']
    print(f"Logged in. Workspace ID: {ws_id}")

    print("\n>>> 2. Submit Contact Form (Public)")
    payload = {
        "workspace_id": ws_id,
        "name": "Inbox Debugger",
        "email": "debug_inbox@example.com",
        "message": "This is a test message to check if it appears in the inbox."
    }
    res = requests.post(f"{BASE_URL}/api/public/contact", json=payload)
    if res.status_code == 200:
        print("Contact Form Submitted.")
    else:
        print(f"Contact Form Failed: {res.text}")
        return

    print("\n>>> 3. Check /api/conversations/ (DB-based)")
    res = s.get(f"{BASE_URL}/api/conversations/", headers=headers)
    convs = res.json()
    print(f"Found {len(convs)} conversations in DB.")
    
    found_db = False
    for c in convs:
        # Check if our contact is there. 
        # We don't have contact name in list directly but we have ID.
        # Let's inspect the latest one.
        if c['subject'] == 'New Inquiry' or c['unanswered'] == True:
             print(f" - ID: {c['id']}, Subject: {c['subject']}, Last Msg: {c['last_message_at']}")
             found_db = True

    if found_db:
        print("SUCCESS: Message saved to DB and visible in /api/conversations/")
    else:
        print("FAILURE: Message NOT found in /api/conversations/")

    print("\n>>> 4. Check /api/inbox/sync (Gmail-based)")
    try:
        res = s.get(f"{BASE_URL}/api/inbox/sync", headers=headers)
        if res.status_code == 200:
            threads = res.json()
            print(f"Found {len(threads)} threads in Gmail Inbox.")
        else:
            print(f"Gmail Sync Failed: {res.text}")
    except Exception as e:
        print(f"Gmail Sync Error: {e}")

if __name__ == "__main__":
    run()
