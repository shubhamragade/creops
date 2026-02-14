import time
import requests
import sys
import os

# Default to localhost:8001 (based on user metadata active port) or 8000
# User metadata says uvicorn running on 8001
API_URL = os.getenv("API_URL", "http://localhost:8001/api/cron/run")
CRON_SECRET = os.getenv("CRON_SECRET", "careops-cron-key-2026")

def run_loop():
    print(f"Starting Cron Loop targeting {API_URL}")
    print("Press Ctrl+C to stop.")
    
    while True:
        try:
            print(f"[{time.strftime('%H:%M:%S')}] Triggering cron...", end=" ")
            # Authenticated POST request
            response = requests.post(API_URL, headers={"X-Cron-Secret": CRON_SECRET})
            if response.status_code == 200:
                print(f"Success: {response.json()}")
            else:
                print(f"Failed ({response.status_code}): {response.text}")
        except Exception as e:
            print(f"Error: {e}")
            print("Make sure the backend is running on port 8001.")
        
        # Wait 60 seconds
        time.sleep(60)

if __name__ == "__main__":
    try:
        run_loop()
    except KeyboardInterrupt:
        print("\nStopping Cron Loop.")
