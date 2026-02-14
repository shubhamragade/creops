
import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def login(email, password):
    r = requests.post(f"{BASE_URL}/api/login", data={"username": email, "password": password})
    r.raise_for_status()
    return r.json()["access_token"]

def run():
    print("--- Flow 3: Owner Operations (API) ---")
    
    try:
        # 1. Login
        token = login("owner@careops.com", "owner123")
        headers = {"Authorization": f"Bearer {token}"}
        print("[OK] Owner Logged In")
        
        # 2. List Bookings to find a target
        r = requests.get(f"{BASE_URL}/api/bookings/", headers=headers)
        r.raise_for_status()
        bookings = r.json()
        
        target = None
        # Find a CONFIRMED or PENDING booking
        for b in bookings:
            if b['status'] in ['confirmed', 'pending']:
                 target = b
                 break
                 
        if not target:
            print("FAIL: No active bookings to modify. Run Flow 1 first.")
            return

        bid = target['id']
        print(f"[OK] Target Booking: {bid} ({target['status']})")
        
        # 3. Modify (Reschedule)
        # Move forward 1 hour
        original_start = datetime.fromisoformat(target['start_time'])
        new_start = original_start + timedelta(hours=1)
        # We need to ensure new slot is valid/free. 
        # If original was 10:00, new is 11:00.
        # But wait, audit_flow_1 might have booked 11:00 if 10:00 was taken?
        # Let's just try. API should return 409 if conflict.
        # To be safe, let's move it to a weird time or +2 hours.
        # Or just try +1 hour.
        
        print(f"Rescheduling booking {bid} to {new_start}...")
        resched_payload = {"start_datetime": new_start.isoformat()}
        r = requests.patch(f"{BASE_URL}/api/bookings/{bid}", json=resched_payload, headers=headers)
        
        if r.status_code == 200:
             print("[OK] Reschedule Success")
        elif r.status_code == 409:
             print("[WARN] Reschedule Conflict. Trying +2 hours...")
             new_start = original_start + timedelta(hours=2)
             resched_payload = {"start_datetime": new_start.isoformat()}
             r = requests.patch(f"{BASE_URL}/api/bookings/{bid}", json=resched_payload, headers=headers)
             if r.status_code == 200:
                 print("[OK] Reschedule Success (Retry)")
             else:
                 print(f"FAIL: Reschedule Failed {r.status_code} - {r.text}")
        else:
             print(f"FAIL: Reschedule Failed {r.status_code} - {r.text}")

        # 4. Cancel
        print(f"Cancelling booking {bid}...")
        r = requests.post(f"{BASE_URL}/api/bookings/{bid}/cancel", headers=headers)
        if r.status_code == 200:
             print("[OK] Cancellation Success")
        else:
             print(f"FAIL: Cancellation Failed {r.status_code} - {r.text}")
             return

        # Verify status
        r = requests.get(f"{BASE_URL}/api/bookings/{bid}/history", headers=headers)
        history = r.json()
        has_cancel = any(e['action'] == 'booking.cancelled' for e in history)
        if has_cancel:
             print("[OK] Verification: Audit log shows cancellation.")
        else:
             print("FAIL: Audit log missing cancellation.")

        # 5. Restore
        print(f"Restoring booking {bid}...")
        r = requests.post(f"{BASE_URL}/api/bookings/{bid}/restore", headers=headers)
        if r.status_code == 200:
             print("[OK] Restore Success")
        else:
             print(f"FAIL: Restore Failed {r.status_code} - {r.text}")
             return
             
        # Verify status again
        r = requests.get(f"{BASE_URL}/api/bookings/", headers=headers)
        bookings = r.json()
        restored = next((b for b in bookings if b['id'] == bid), None)
        if restored and restored['status'] == 'confirmed':
             print("[OK] Verification: Booking is CONFIRMED again.")
        else:
             print(f"FAIL: Verification failed. Status: {restored['status'] if restored else 'None'}")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run()
