import requests

# Test login
url = "http://localhost:8000/api/login"
data = {
    "username": "owner@careops.com",
    "password": "owner123"
}

try:
    response = requests.post(url, data=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✅ LOGIN SUCCESSFUL!")
    else:
        print("❌ LOGIN FAILED!")
        
except Exception as e:
    print(f"❌ Error: {e}")
