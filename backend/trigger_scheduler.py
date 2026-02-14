
import requests
import time

BASE_URL = "http://localhost:8001"
CRON_SECRET = "careops-cron-key-2026"

def trigger_scheduler():
    print(">>> Triggering Auto-Scheduler (Cron Jobs)...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/cron/run",
            headers={"x-cron-secret": CRON_SECRET}
        )
        if response.status_code == 200:
            print(">>> SUCCESS: Scheduler ran successfully.")
            print("Results:", response.json())
        else:
            print(f">>> FAILED: Status {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f">>> ERROR: {e}")
        print("Make sure the backend is running on port 8000!")

if __name__ == "__main__":
    trigger_scheduler()
