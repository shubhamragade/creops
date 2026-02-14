import requests
import sys
import os

# Add backend to path if run from root
sys.path.append(os.path.join(os.getcwd(), 'backend'))

BASE_URL = "http://localhost:8000"

def verify_intake_flow():
    print("--- Verifying Intake Form API ---")
    
    # 1. We need a booking ID.
    # Ideally we fetch one or create one.
    # For now, let's try ID 1 (simulation usually creates some).
    booking_id = 1 
    
    print(f"Testing Booking ID: {booking_id}")
    
    # GET
    try:
        url = f"{BASE_URL}/api/public/bookings/{booking_id}/intake"
        print(f"GET {url}...")
        res = requests.get(url)
        
        if res.status_code == 404:
            print("Booking 1 not found. Attempting to list bookings to find a valid ID...")
            # This requires auth, so we might skip automated creation and ask user.
            # But let's assume if 1 fails, we might need manual check.
            print("FAILED: Booking not found.")
            return
            
        if res.status_code != 200:
            print(f"FAILED: Status {res.status_code}")
            print(res.text)
            return
            
        data = res.json()
        print("SUCCESS: Retrieved Intake Details")
        print(f"  Service: {data.get('service_name')}")
        print(f"  Form Fields: {len(data.get('form', {}).get('fields', []))}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        return

    # POST
    try:
        url = f"{BASE_URL}/api/public/bookings/{booking_id}/intake"
        payload = {
            "answers": {
                "notes": "Automated verification test notes.",
                "allergies": "None" 
            }
        }
        print(f"POST {url}...")
        res = requests.post(url, json=payload)
        
        if res.status_code != 200:
             print(f"FAILED: Status {res.status_code}")
             print(res.text)
             return
             
        data = res.json()
        print("SUCCESS: Submitted Intake Form")
        print(data)
        
    except Exception as e:
        print(f"ERROR: {e}")
        return

if __name__ == "__main__":
    verify_intake_flow()
