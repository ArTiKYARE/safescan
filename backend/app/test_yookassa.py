import urllib.request
import urllib.error
import json
import base64
import os
import sys

shop_id = os.getenv("YOOKASSA_SHOP_ID", "")
secret_key = os.getenv("YOOKASSA_SECRET_KEY", "")
return_url = os.getenv("YOOKASSA_RETURN_URL", "http://localhost:3000/account")

print(f"SHOP_ID: {shop_id}")
print(f"SECRET_KEY: {secret_key[:10]}...")
print(f"RETURN_URL: {return_url}")

auth_str = base64.b64encode(f"{shop_id}:{secret_key}".encode()).decode()

payment_data = {
    "amount": {"value": "1.00", "currency": "RUB"},
    "confirmation": {"type": "redirect", "return_url": return_url},
    "capture": True,
    "description": "Test payment",
}

body = json.dumps(payment_data).encode('utf-8')
req = urllib.request.Request(
    "https://api.yookassa.ru/v3/payments",
    data=body,
    headers={
        "Content-Type": "application/json",
        "Idempotency-Key": "test-key-from-python-script-001",
        "Authorization": f"Basic {auth_str}",
    },
    method="POST",
)

print(f"\nHeaders being sent: {dict(req.headers)}")

try:
    with urllib.request.urlopen(req, timeout=30.0) as response:
        data = response.read().decode('utf-8')
        print(f"\nStatus: {response.status}")
        print(f"Response: {data}")
except urllib.error.HTTPError as e:
    body_err = e.read().decode('utf-8')
    print(f"\nHTTP Error: {e.code}")
    print(f"Response: {body_err}")
except Exception as e:
    print(f"\nException: {e}")
