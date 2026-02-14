import requests
import json

def test_staff_endpoint():
    url = "http://localhost:8001/api/staff/"
    # We don't have a token easily available, but we can check if it returns 401 instead of 404 or 500
    try:
        print(f"Testing {url}...")
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 401:
            print("Success: Endpoint exists and is protected (401)")
        elif response.status_code == 200:
             print("Success: Endpoint exists and returned 200")
        elif response.status_code == 403:
             print("Success: Endpoint exists and returned 403 (Permission denied)")
        else:
            print(f"Warning: Unexpected status code {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error connecting to backend: {e}")

if __name__ == "__main__":
    test_staff_endpoint()
