
import requests
import json

BASE_URL = "http://localhost:8000"

def login(email, password):
    r = requests.post(f"{BASE_URL}/api/login", data={"username": email, "password": password})
    r.raise_for_status()
    return r.json()["access_token"]

def run():
    print("--- Flow 4: Staff Restrictions (API) ---")
    
    try:
        # 1. Login as Staff
        try:
            token = login("staff@careops.com", "staff123")
        except Exception as e:
            print(f"FAIL: Staff Login Failed: {e}")
            return
            
        headers = {"Authorization": f"Bearer {token}"}
        print("[OK] Staff Logged In")
        
        # 2. Attempt Admin Routes (Dashboard)
        # Dashboard is usually Owner only.
        print("Attempting Dashboard Access...")
        r = requests.get(f"{BASE_URL}/api/dashboard/", headers=headers)
        if r.status_code == 403:
             print("[OK] Dashboard Access Denied (403)")
        elif r.status_code == 401:
             print("[OK] Dashboard Access Denied (401)")
        else:
             print(f"FAIL: Expected 403, got {r.status_code}")
             
        # 3. Attempt Config Access (or restricted endpoint)
        # We don't have a specific /api/config, but maybe /api/staff?
        # Staff shouldn't be able to create new staff?
        # Let's try to create a staff member.
        print("Attempting to Create Staff...")
        payload = {
            "email": "malicious@staff.com",
            "password": "pass",
            "full_name": "Malicious Actor",
            "role": "staff"
        }
        # Assuming POST /api/staff/ is restricted or check access.
        # Actually /api/staff/ router usually restricts to Owner.
        r = requests.post(f"{BASE_URL}/api/staff/", json=payload, headers=headers)
        if r.status_code == 403:
             print("[OK] Staff Creation Denied (403)")
        elif r.status_code == 405:
             # Method not allowed? Check route.
             print("WARN: Method not allowed - check routes.")
        elif r.status_code == 200 or r.status_code == 201:
             print(f"CRITICAL: Staff created new staff! {r.status_code}")
        else:
             print(f"[OK] blocked with {r.status_code}")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    run()
