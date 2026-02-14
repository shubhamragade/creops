
import requests
import json
import sys

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
    
    # Login response might vary structure. 
    # Usually it returns token and user object.
    # Let's inspect or just use slug to fetch details.
    try:
        data = res.json()
        token = data.get('access_token')
        slug = data.get('workspace_slug')
        # If user object is missing, fetch /me
        headers = {"Authorization": f"Bearer {token}"}
        res_me = s.get(f"{BASE_URL}/api/users/me", headers=headers)
        if res_me.status_code == 200:
            user = res_me.json()
            ws_id = user['workspace_id']
        else:
            # Fallback if specific endpoint fails, try public workspace
            res_ws = s.get(f"{BASE_URL}/api/public/workspace/{slug}")
            ws_id = res_ws.json()['id']
            
    except Exception as e:
        print(f"Error parsing login: {e}")
        print(res.text)
        return
    print(f"Logged in. Workspace: {slug} (ID: {ws_id})")

    print("\n>>> 2. Get/Create Form")
    res = s.get(f"{BASE_URL}/api/forms/", headers=headers)
    forms = res.json()
    form_id = None
    
    if forms:
        print(f"Found {len(forms)} forms.")
        for f in forms:
            if f['type'] == 'intake': # usage for lead capture
                form_id = f['id']
                print(f"Using existing Intake/Contact form ID: {form_id}")
                break
        if not form_id:
            form_id = forms[0]['id'] # Fallback
            print(f"Using updated fallback form ID: {form_id}")
    
    if not form_id:
        print("Creating new form...")
        payload = {
            "name": "General Contact",
            "type": "contact",
            "fields": [
                {"name": "name", "label": "Name", "type": "text"},
                {"name": "email", "label": "Email", "type": "email"}
            ]
        }
        res = s.post(f"{BASE_URL}/api/forms/", json=payload, headers=headers)
        if res.status_code != 201:
            print(f"Create Failed: {res.text}")
            return
        form_id = res.json()['id']
        print(f"Created Form ID: {form_id}")

    print(f"\n>>> 3. Submit Lead Capture (Public) to Form {form_id}")
    # Simulating Public User
    # URI: /api/public/forms/{id}/submit
    payload = {
        "answers": {
            "name": "Lead Capture Test User",
            "email": "leadcapture2@example.com"
        }
    }
    res = requests.post(f"{BASE_URL}/api/public/forms/{form_id}/submit", json=payload)
    
    if res.status_code == 200:
        print("Success! Lead captured.")
        print("Response:", res.json())
        print("This should have triggered 'send_welcome_email' with a booking link.")
    else:
        print(f"Submission Failed: {res.text}")

if __name__ == "__main__":
    run()
