import requests, json

# Login as admin
resp = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'email': 'test@test.com',
    'password': 'admin123'
})
token = resp.json()['access_token']
print(f'Logged in as admin')

# Get all users
users = requests.get('http://localhost:8000/api/v1/admin/users', headers={'Authorization': f'Bearer {token}'})
users_data = users.json()
print(f'Users: {len(users_data)}')

# Find a non-admin user
non_admin = None
for u in users_data:
    if u['role'] != 'admin':
        non_admin = u
        break

if not non_admin:
    print('No non-admin user found')
    exit()

print(f'Testing user: {non_admin["email"]} ({non_admin["id"]})')

# Get user domains
domains = requests.get(f'http://localhost:8000/api/v1/admin/users/{non_admin["id"]}/domains', 
    headers={'Authorization': f'Bearer {token}'})
print(f'Domains status: {domains.status_code}')
if domains.status_code == 200:
    domains_data = domains.json()
    print(f'Domains: {len(domains_data)}')
    for d in domains_data:
        print(f'  {d["domain"]} - verified: {d["is_verified"]}, id: {d["id"]}')
        if not d['is_verified']:
            # Try to approve
            print(f'  Approving domain {d["id"]}...')
            approve_resp = requests.post(
                f'http://localhost:8000/api/v1/admin/users/{non_admin["id"]}/domains/{d["id"]}/approve',
                headers={'Authorization': f'Bearer {token}'}
            )
            print(f'  Approve status: {approve_resp.status_code}')
            print(f'  Approve response: {approve_resp.text[:500]}')
else:
    print(f'Response: {domains.text[:500]}')
