import requests
import sys

BASE_URL = "http://localhost:8000"
OWNER_EMAIL = "owner@careops.com"
OWNER_PASS = "owner123"

def create_booking_and_get_id():
    # Login
    res = requests.post(f"{BASE_URL}/api/login", data={"username": OWNER_EMAIL, "password": OWNER_PASS})
    if res.status_code != 200:
        print(f"Login Failed: {res.text}")
        return
    token = res.json()['access_token']
    slug = res.json()['workspace_slug']
    
    # Get Service
    res = requests.get(f"{BASE_URL}/api/public/workspace/{slug}")
    if res.status_code != 200:
         print(f"WS Fetch Failed")
         return
    sid = res.json()['services'][0]['id']
    
    # Create Booking
    payload = {
        "service_id": sid,
        "start_datetime": "2026-05-01T10:00:00",
        "name": "Browser Test User",
        "email": "browser@example.com",

    }
    res = requests.post(f"{BASE_URL}/api/bookings/", json=payload)
    if res.status_code == 200:
        bid = res.json()['id']
        print(f"BOOKING_ID:{bid}")
    else:
        print(f"Booking Failed: {res.text}")

if __name__ == "__main__":
    create_booking_and_get_id()
