
import requests
import json

BASE_URL = "http://localhost:8001"
OWNER_EMAIL = "owner@careops.com"
OWNER_PASS = "owner123"

def run():
    print(">>> 1. Login as Owner")
    s = requests.Session()
    res = s.post(f"{BASE_URL}/api/login", data={"username": OWNER_EMAIL, "password": OWNER_PASS})
    if res.status_code != 200:
        print(f"Login Failed: {res.text}")
        return
    token = res.json().get('access_token')
    slug = res.json().get('workspace_slug')
    headers = {"Authorization": f"Bearer {token}"}
    print(f"Logged in to {slug}")

    print("\n>>> 2. Create/Update Custom Intake Form")
    # First, list forms to see if one exists
    res = s.get(f"{BASE_URL}/api/forms/", headers=headers)
    forms = res.json()
    intake_id = None
    for f in forms:
        if f['type'] == 'intake':
            intake_id = f['id']
            break
            
    custom_fields = [
        {"name": "allergies", "label": "Do you have any allergies?", "type": "text", "required": True},
        {"name": "referral", "label": "How did you hear about us?", "type": "select", "options": ["Google", "Friend", "Other"]}
    ]
    
    if intake_id:
        print(f"Updating existing Intake Form {intake_id} with custom questions...")
        res = s.patch(f"{BASE_URL}/api/forms/{intake_id}", json={"fields": custom_fields}, headers=headers)
    else:
        print("Creating new Intake Form with custom questions...")
        payload = {
            "name": "General Intake",
            "type": "intake",
            "fields": custom_fields
        }
        res = s.post(f"{BASE_URL}/api/forms/", json=payload, headers=headers)
        intake_id = res.json()['id']

    if res.status_code not in [200, 201]:
        print(f"Form Config Failed: {res.text}")
        return
    print("Form Configuration Saved.")

    print("\n>>> 3. Verify Public API Serves These Questions")
    # We need a booking ID to check the intake link. 
    # Let's create a dummy booking first.
    print("Creating booking to generate intake link...")
    # Get Service
    res_ws = s.get(f"{BASE_URL}/api/public/workspace/{slug}")
    service_id = res_ws.json()['services'][0]['id']
    
    book_payload = {
        "service_id": service_id,
        "start_datetime": "2026-08-01T10:00:00",
        "name": "Form Verifier",
        "email": "verifier@example.com"
    }
    res_b = s.post(f"{BASE_URL}/api/bookings/", json=book_payload)
    if res_b.status_code != 200:
        print(f"Booking failed: {res_b.text}")
        return
    booking_id = res_b.json()['id']
    
    # Now fetch the intake schema for this booking
    print(f"Fetching Intake Schema for Booking {booking_id}...")
    res_intake = s.get(f"{BASE_URL}/api/public/bookings/{booking_id}/intake")
    data = res_intake.json()
    
    served_fields = data['form']['fields']
    print("\n>>> 4. Comparison Results:")
    print(f"Served {len(served_fields)} fields.")
    found_allergy = any(f['name'] == 'allergies' for f in served_fields)
    
    if found_allergy:
        print("SUCCESS: The system served the Custom Owner-Defined Questions.")
    else:
        print("FAILURE: The system served generic questions.")
        print(served_fields)

if __name__ == "__main__":
    run()
