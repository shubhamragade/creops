"""Quick retest on a weekday with slots."""
import requests, json

BASE = "http://localhost:8001"

# 1. Create Booking on Monday
print("=== BOOKING (Monday 14:00) ===")
r = requests.post(f"{BASE}/api/bookings/", json={
    "service_id": 1,
    "start_datetime": "2026-02-16T14:00:00Z",
    "name": "External Customer",
    "email": "customer.test@example.com",
    "phone": "+1555000111"
})
print(f"Status: {r.status_code}")
data = r.json()
print(json.dumps(data, indent=2, default=str))

if r.status_code == 200:
    bid = data["id"]

    # 2. Get Intake Form
    print("\n=== INTAKE FORM (GET) ===")
    r2 = requests.get(f"{BASE}/api/public/bookings/{bid}/intake")
    print(f"Status: {r2.status_code}")
    print(json.dumps(r2.json(), indent=2, default=str))

    # 3. Submit Intake Form
    print("\n=== INTAKE FORM (POST) ===")
    r3 = requests.post(f"{BASE}/api/public/bookings/{bid}/intake", json={
        "answers": {"notes": "First time visit, no allergies."}
    })
    print(f"Status: {r3.status_code}")
    print(json.dumps(r3.json(), indent=2, default=str))
else:
    print("Booking failed, skipping intake tests")

# 4. Contact Form
print("\n=== CONTACT FORM ===")
r4 = requests.post(f"{BASE}/api/public/contact", json={
    "workspace_id": 1,
    "name": "New Customer",
    "email": "newcustomer@example.com",
    "message": "I want to learn about your services"
})
print(f"Status: {r4.status_code}")
print(json.dumps(r4.json(), indent=2, default=str))

print("\n=== ALL DONE ===")
