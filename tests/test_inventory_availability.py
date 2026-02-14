import requests
import sys

# Configuration
API_URL = "http://localhost:8000"

def test_inventory_check():
    print("Testing Inventory-Aware Availability...")
    
    # 1. Create Workspace
    import random
    suffix = random.randint(1000, 9999)
    print("1. Creating Workspace...")
    ws_payload = {
        "name": f"Inventory Test Spa {suffix}",
        "address": "123 Test St",
        "timezone": "UTC",
        "contact_email": f"test{suffix}@spa.com",
        "owner_email": f"owner{suffix}@spa.com",
        "owner_password": "password123"
    }
    r = requests.post(f"{API_URL}/api/onboarding/workspaces", json=ws_payload)
    if r.status_code != 200:
        print(f"Failed to create workspace: {r.text}")
        sys.exit(1)
    
    data = r.json()
    ws_id = data["workspace_id"]
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create Inventory Item (Qty 1)
    print("2. Creating Inventory Item (Qty 1)...")
    inv_payload = [{
        "name": "Test Serum",
        "quantity_available": 1,
        "low_threshold": 5
    }]
    r = requests.post(f"{API_URL}/api/onboarding/workspaces/{ws_id}/inventory", json=inv_payload, headers=headers)
    print(f"Inv create status: {r.status_code}")
    print(f"Inv create text: {r.text}")
    if r.status_code != 200:
        print(f"Failed to create inventory: {r.text}")
        sys.exit(1)
    inv_item_id = r.json()["items"][0]["id"]
    
    # 3. Create Service Linked to Inventory
    print("3. Creating Service linked to Item...")
    svc_payload = [{
        "name": "Serum Facial",
        "duration_minutes": 60,
        "location": "Main Room",
        "availability": {"day_slots": {"mon": ["09:00-17:00"]}}, # Schema expects specific format? 
        # Schema says `availability: Dict[str, Any] # e.g. {"days": ["mon","tue"], "slots": ["10:00-18:00"]}`
        # But public.py uses `availability.get(day_str, [])` where day_str is "mon", "tue".
        # So format should be {"mon": ["09:00-17:00"]} directly?
        # Let's match public.py logic: availability.get("mon") -> List[str]
        "availability": {"mon": ["09:00-17:00"]}, 
        "inventory_item_id": inv_item_id,
        "inventory_quantity_required": 1
    }]
    r = requests.post(f"{API_URL}/api/onboarding/workspaces/{ws_id}/services", json=svc_payload, headers=headers)
    if r.status_code != 200:
        print(f"Failed to create service: {r.text}")
        sys.exit(1)
    print(f"Service creation response: {r.text}")
    service_id = r.json()["service_ids"][0]
    
    # 4. Check Availability (Should have slots)
    print("4. Checking Availability (Expect Slots)...")
    # Find next Monday
    from datetime import date, timedelta
    today = date.today()
    days_ahead = 0 - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    next_mon = today + timedelta(days=days_ahead)
    
    r = requests.get(f"{API_URL}/api/public/services/{service_id}/availability?date={next_mon}")
    print(f"Avail status: {r.status_code}")
    print(f"Avail text: {r.text}")
    slots = r.json()
    print(f"Slots found: {len(slots)}")
    if len(slots) == 0:
        print("FAIL: Expected slots, found none.")
        sys.exit(1)
        
    # 5. Book the Service (Consumes 1 Qty -> 0 Left)
    print("5. Booking the Service (Consuming Inventory)...")
    slot = slots[0]
    book_payload = {
        "service_id": service_id,
        "start_datetime": f"{next_mon}T{slot}:00", # MVP usually takes ISO or similar, backend parses
        "name": "Tester",
        "email": "tester@example.com"
    }
    # Need to match schema format. Backend expects datetime obj/str logic.
    # bookings.py: start_datetime: datetime
    # Let's try ISO format
    # But wait, create_booking is POST /api/public/bookings/ ?? No, /api/bookings/ is typically authenticated or public?
    # bookings.py is mounted. Let's check main.py mount. 
    # Usually public booking is different router? 
    # Ah, bookings.py has @router.post("/"). 
    # Assume it is mounted at /api/bookings as public? Or /api/public/bookings?
    # Let's try /api/bookings first (standard).
    
    r = requests.post(f"{API_URL}/api/bookings/", json=book_payload)
    if r.status_code != 200:
        print(f"Booking failed: {r.text}")
        sys.exit(1)
        
    print("Booking success. Inventory should be 0.")
    
    # 6. Check Availability AGAIN (Should be empty due to 0 stock)
    print("6. Checking Availability (Expect ZERO slots)...")
    # Use same date or next week Monday
    next_next_mon = next_mon + timedelta(days=7)
    r = requests.get(f"{API_URL}/api/public/services/{service_id}/availability?date={next_next_mon}")
    slots_after = r.json()
    print(f"Slots found: {len(slots_after)}")
    
    if len(slots_after) == 0:
        print("SUCCESS! Inventory check blocked availability.")
    else:
        print("FAIL! Slots still available despite 0 inventory.")
        sys.exit(1)

if __name__ == "__main__":
    test_inventory_check()
