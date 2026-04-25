import requests, json

# Login
resp = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'email': 'test@test.com',
    'password': 'admin123'
})
print(f'Login: {resp.status_code}')
token = resp.json()['access_token']

# Get admin users
resp = requests.get('http://localhost:8000/api/v1/admin/users', headers={
    'Authorization': f'Bearer {token}'
})
print(f'Admin users: {resp.status_code}')
if resp.status_code == 200:
    users = resp.json()
    print(f'Users count: {len(users)}')
    for u in users:
        print(f'  {u["email"]} - {u["role"]} - blocked: {u["is_blocked"]}')
else:
    print(f'Error: {resp.text}')
