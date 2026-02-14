
import requests
import json
import sys
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
WS_SLUG = "demo-spa"

def login(email, password):
    r = requests.post(f"{BASE_URL}/api/login", data={"username": email, "password": password})
    r.raise_for_status()
    return r.json()["access_token"]

def run():
    print("--- Flow 1: Customer -> Booking (API) ---")
    
    try:
        # 1. Get Workspace & Services
        print(f"Fetching public config for '{WS_SLUG}'...")
        r = requests.get(f"{BASE_URL}/api/public/workspace/{WS_SLUG}")
        r.raise_for_status()
        ws_data = r.json()
        services = ws_data.get("services", [])
        if not services:
            print("FAIL: No services found")
            return
        
        service = services[0]
        service_id = service['id']
        print(f"[OK] Found Service: {service['name']} (ID: {service_id})")
        
        # 2. Get Slots (Ensure Weekday)
        # 2026-02-12 is Thursday. +1=Fri, +4=Mon
        target_dates = [
            (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"), # Friday
            (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d")  # Monday
        ]
        
        slot = None
        selected_date = None
        
        for d in target_dates:
            print(f"Checking slots for {d}...")
            r = requests.get(f"{BASE_URL}/api/public/services/{service_id}/availability?date={d}")
            if r.status_code == 200:
                slots = r.json()
                if slots:
                    slot = slots[0]
                    selected_date = d
                    break
        
        if not slot:
            print("FAIL: No slots found (checked Fri/Mon).")
            return

        print(f"[OK] Found Slot: {slot} on {selected_date}")

        # 3. Create Booking
        # Construct ISO datetime
        start_dt_str = f"{selected_date}T{slot}:00"
        
        payload = {
            "service_id": service_id,
            "start_datetime": start_dt_str,
            "name": "QA Tester",
            "email": "qa@careops.com",
            "phone": "555-0123"
        }
        
        print(f"Booking payload: {payload}")
        r = requests.post(f"{BASE_URL}/api/bookings/", json=payload)
        
        if r.status_code != 200:
             print(f"FAIL: Booking Failed {r.status_code} - {r.text}")
             return
             
        booking = r.json()
        booking_id = booking.get("id")
        print(f"[OK] Booking Created: ID {booking_id}")
        
        # 4. Verification Check (As Owner)
        print("Logging in as Owner to verify...")
        token = login("owner@careops.com", "owner123")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Check Booking History
        r = requests.get(f"{BASE_URL}/api/bookings/{booking_id}/history", headers=headers)
        if r.status_code == 200:
            history = r.json()
            # Verify 'booking.created' audit
            has_create = any(e['action'] == 'booking.created' for e in history)
            if has_create:
                print(f"[OK] Audit Log verified: booking.created found.")
            else:
                print(f"WARN: Audit Log missing booking.created event. History: {history}")
                
            # Verify 'inventory.deducted' audit
            has_deduct = any(e['action'] == 'inventory.deducted' for e in history)
            if has_deduct:
                print(f"[OK] Inventory Log verified: inventory.deducted found.")
            else:
                 # Might not expect if no inventory attached to service
                 pass
        else:
            print(f"FAIL: Could not fetch booking history: {r.status_code}")

        # Check Dashboard (Visibility)
        r = requests.get(f"{BASE_URL}/api/dashboard/", headers=headers) 
        if r.status_code == 200:
            stats = r.json()
            # Verify stats
            print(f"[OK] Dashboard Stats Fetched. Today: {stats.get('bookings', {}).get('today_count')}")
        else:
             print(f"FAIL: Dashboard fetch failed {r.status_code}")
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run()
