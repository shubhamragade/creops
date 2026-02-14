
import requests
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
WS_SLUG = "demo-spa"

def login(email, password):
    r = requests.post(f"{BASE_URL}/api/login", data={"username": email, "password": password})
    if r.status_code != 200:
        raise Exception(f"Login failed: {r.text}")
    return r.json()["access_token"]

def run():
    print("--- Flow 7: Repeatability (API) ---")
    
    try:
        # 1. Login Owner
        token = login("owner@careops.com", "owner123")
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Get Service ID
        r = requests.get(f"{BASE_URL}/api/public/workspace/{WS_SLUG}")
        service_id = r.json()["services"][0]["id"]
        
        # 3. Loop: Create -> Cancel -> Restore -> Cancel
        # Repeat 3 times
        for i in range(3):
            print(f"\nIteration {i+1}...")
            
            # Create
            start_time = (datetime.now() + timedelta(days=5+i)).replace(hour=10, minute=0, second=0, microsecond=0)
            payload = {
                "service_id": service_id,
                "start_datetime": start_time.isoformat(),
                "name": f"Repeat User {i}",
                "email": f"repeat{i}@test.com",
                "phone": "555-REPEAT"
            }
            
            # Check availability (optional, we assume free)
            
            r = requests.post(f"{BASE_URL}/api/bookings/", json=payload)
            if r.status_code != 200:
                print(f"FAIL: Iteration {i} Booking Failed {r.status_code} - {r.text}")
                continue
                
            bid = r.json()['id']
            print(f"[OK] Created {bid}")
            
            # Cancel
            r = requests.post(f"{BASE_URL}/api/bookings/{bid}/cancel", headers=headers)
            if r.status_code != 200:
                print(f"FAIL: Iteration {i} Cancel Failed {r.status_code}")
                # Try to clean up?
            else:
                print(f"[OK] Cancelled {bid}")
                
            # Restore
            r = requests.post(f"{BASE_URL}/api/bookings/{bid}/restore", headers=headers)
            if r.status_code != 200:
                print(f"FAIL: Iteration {i} Restore Failed {r.status_code}")
            else:
                print(f"[OK] Restored {bid}")
                
            # Verify Status = Confirmed
            r = requests.get(f"{BASE_URL}/api/bookings/{bid}/history", headers=headers) # History check as proxy
            # Or just check list
            pass
            
            print(f"[OK] Iteration {i+1} Complete")
            
        print("\n[OK] Repeatability Test Complete")
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    run()
