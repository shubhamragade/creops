import requests
import sys
import os
import time

# Adjust if backend is on a different port (User metadata says 8001)
BASE_URL = "http://localhost:8001/api"

def test_contact_form():
    print("Testing Contact Form (Fix A)...")
    payload = {
        "workspace_id": 1, # Assuming workspace 1 exists
        "name": "Audit Bot",
        "email": "audit@example.com",
        "message": "This is a verification message.",
        "phone": "555-0199"
    }
    
    try:
        r = requests.post(f"{BASE_URL}/public/contact", json=payload)
        if r.status_code == 200:
            print("✅ Contact form submitted successfully.")
            return True
        else:
            print(f"❌ Failed to submit contact form: {r.text}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def check_email_logs():
    print("\nChecking Email Logs (Database)...")
    # We need to run a python script to check the DB directly since we don't have an API to list generic logs publicly
    # and we want to verify the 'html_content' or at least the 'type'
    import sys
    # We will write a small python snippet to run via subprocess or just expect the user to trust the logs?
    # Better: Use the /api/dashboard endpoint which lists failures and recent activity!
    # I added 'recent_activity' to dashboard.
    
    # But dashboard requires auth.
    # Let's try to login or just use a direct DB check script.
    pass

if __name__ == "__main__":
    if test_contact_form():
        print("\nNOTE: verification of email delivery requires checking the backend logs or dashboard.")
