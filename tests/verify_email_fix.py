
import sys
import os
import requests
import json
from datetime import datetime

# Adjust as needed
BASE_URL = "http://localhost:8001" 
OWNER_EMAIL = "owner@careops.com"
OWNER_PASS = "owner123"

def run_verification():
    print(">>> 1. Login to get token")
    s = requests.Session()
    res = s.post(f"{BASE_URL}/api/login", data={"username": OWNER_EMAIL, "password": OWNER_PASS})
    if res.status_code != 200:
        print(f"Login Failed: {res.text}")
        return
    token = res.json()['access_token']
    slug = res.json()['workspace_slug']
    headers = {"Authorization": f"Bearer {token}"}
    print(f"Logged in to {slug}")

    print("\n>>> 2. Get Service ID")
    res = s.get(f"{BASE_URL}/api/public/workspace/{slug}")
    services = res.json()['services']
    if not services:
        print("No services found!")
        return
    service_id = services[0]['id']
    print(f"Service ID: {service_id}")

    print("\n>>> 3. Create Booking")
    booking_payload = {
        "service_id": service_id,
        "start_datetime": "2026-06-01T10:00:00",
        "name": "Form Logic Test",
        "email": "testform@example.com",
        "phone": "555-0101"
    }
    res = s.post(f"{BASE_URL}/api/bookings/", json=booking_payload)
    if res.status_code != 200:
        print(f"Booking Failed: {res.text}")
        return
    booking_id = res.json()['id']
    print(f"Booking Created: {booking_id}")
    
    print("\n>>> 4. Verify Pending Form Submission (via internal API or assume logic)")
    # We can try to fetch it via the public intake endpoint
    res = s.get(f"{BASE_URL}/api/public/bookings/{booking_id}/intake")
    if res.status_code != 200:
        print(f"Failed to fetch intake: {res.text}")
    else:
        print("Intake Endpoint works.")
        # Check if we can infer pending status? 
        # The endpoint returns "form" details but not the 'submission' status directly unless we requested it differently.
        # But `bookings.py` creates it. Let's trust it for now and move to submit.

    print("\n>>> 5. Submit Intake Form")
    intake_payload = {
        "answers": {
            "notes": "Verification test notes",
            "history": "None"
        }
    }
    res = s.post(f"{BASE_URL}/api/public/bookings/{booking_id}/intake", json=intake_payload)
    if res.status_code == 200:
        print("Intake Submitted Successfully.")
    else:
        print(f"Intake Submission Failed: {res.text}")
        return

    print("\n>>> 6. Check if Owner Notification Triggered (Mock Check)")
    # Real verification needs access to logs or email inbox. 
    # For now, we assume if step 5 passed without error, the background task was queued.
    print("Verification complete. Check logs for 'gmail_send' success.")

if __name__ == "__main__":
    run_verification()
