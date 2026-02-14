
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def login(email, password):
    r = requests.post(f"{BASE_URL}/api/login", data={"username": email, "password": password})
    if r.status_code != 200:
        print(f"Login failed: {r.status_code} {r.text}")
        sys.exit(1)
    return r.json()["access_token"]

def run():
    print("--- DEBUG REPLY ---")
    
    # 1. Login Staff
    print("Logging in as Staff...")
    token = login("staff@careops.com", "staff123")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Get Conversations
    print("Fetching conversations...")
    r = requests.get(f"{BASE_URL}/api/conversations/", headers=headers)
    if r.status_code != 200:
        print(f"Failed to list conversations: {r.status_code} {r.text}")
        return
    
    convs = r.json()
    if not convs:
        print("No conversations found. Create one first via Flow 2.")
        return
        
    target = convs[0]
    cid = target['id']
    print(f"Target Conversation: {cid} (Subject: {target.get('subject')})")
    
    # 3. Try Reply
    url = f"{BASE_URL}/api/conversations/messages"
    payload = {
        "conversation_id": cid,
        "content": "Debug Reply Content"
    }
    
    print(f"POST {url}")
    print(f"Payload: {payload}")
    
    r = requests.post(url, json=payload, headers=headers)
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text}")
    
    # 4. Check for implicit 404 on trailing slash?
    url_slash = f"{BASE_URL}/api/conversations/messages/"
    print(f"POST {url_slash} (Trailing Slash Check)")
    r_slash = requests.post(url_slash, json=payload, headers=headers)
    print(f"Status: {r_slash.status_code}")
    print(f"Body: {r_slash.text}")

if __name__ == "__main__":
    run()
