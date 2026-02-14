import requests

BASE = 'http://localhost:8001'

# Login as owner (OAuth2 form data)
r = requests.post(f'{BASE}/api/login', data={'username':'owner@careops.com','password':'owner123'})
print('Login:', r.status_code)
token = r.json().get('access_token','')
h = {'Authorization': f'Bearer {token}'}

# List inventory
r = requests.get(f'{BASE}/api/inventory', headers=h)
print(f'GET /inventory: {r.status_code} -> {len(r.json())} items')

# Create item
r = requests.post(f'{BASE}/api/inventory', json={'name':'Test Towels','quantity':50,'threshold':10}, headers=h)
print(f'POST /inventory: {r.status_code} -> {r.json()}')
item_id = r.json().get('id')

# Update item
r = requests.patch(f'{BASE}/api/inventory/{item_id}', json={'quantity':3}, headers=h)
print(f'PATCH /inventory/{item_id}: {r.status_code} -> qty={r.json().get("quantity")}')

# Delete item
r = requests.delete(f'{BASE}/api/inventory/{item_id}', headers=h)
print(f'DELETE /inventory/{item_id}: {r.status_code}')

# List forms
r = requests.get(f'{BASE}/api/forms', headers=h)
print(f'GET /forms: {r.status_code} -> {len(r.json())} forms')

# Create form with Google Form URL
r = requests.post(f'{BASE}/api/forms', json={
    'name':'Client Intake', 'type':'intake',
    'google_form_url':'https://docs.google.com/forms/d/example',
    'fields':[]
}, headers=h)
print(f'POST /forms: {r.status_code} -> {r.json()}')
form_id = r.json().get('id')

# Delete form
r = requests.delete(f'{BASE}/api/forms/{form_id}', headers=h)
print(f'DELETE /forms/{form_id}: {r.status_code}')

print('\nALL TESTS PASSED')
