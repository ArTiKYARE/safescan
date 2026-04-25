import requests, json

# Login
resp = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'email': 'test@test.com',
    'password': 'admin123'
})
print(f'Login: {resp.status_code}')
token = resp.json()['access_token']

# Get domain
domains = requests.get('http://localhost:8000/api/v1/domains/', headers={'Authorization': f'Bearer {token}'})
domain_id = domains.json()[0]['id']
print(f'Domain: {domain_id}')

# Create scan
scan_resp = requests.post('http://localhost:8000/api/v1/scans/', 
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
    json={'domain_id': domain_id, 'scan_type': 'quick', 'consent_acknowledged': True}
)
print(f'Scan: {scan_resp.status_code}')
if scan_resp.status_code == 201:
    data = scan_resp.json()
    print(f'Scan ID: {data["id"]}')
    print(f'Cost: {data["cost"]}')
    print(f'Free remaining: {data["free_scans_remaining"]}')
else:
    print(f'Response: {scan_resp.text[:500]}')
