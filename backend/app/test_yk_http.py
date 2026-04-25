import http.client
import json
import base64
import os

shop_id = os.getenv("YOOKASSA_SHOP_ID", "")
secret_key = os.getenv("YOOKASSA_SECRET_KEY", "")
return_url = os.getenv("YOOKASSA_RETURN_URL", "http://localhost:3000/account")

auth_str = base64.b64encode(f"{shop_id}:{secret_key}".encode()).decode()

payment_data = {
    "amount": {"value": "1.00", "currency": "RUB"},
    "confirmation": {"type": "redirect", "return_url": return_url},
    "capture": True,
    "description": "Test payment via http.client",
}

body = json.dumps(payment_data)
conn = http.client.HTTPSConnection("api.yookassa.ru", timeout=30)
conn.request(
    "POST",
    "/v3/payments",
    body=body,
    headers={
        "Content-Type": "application/json",
        "Idempotency-Key": "test-http-client-key-002",
        "Authorization": f"Basic {auth_str}",
    },
)
resp = conn.getresponse()
data = resp.read().decode('utf-8')
print(f"Status: {resp.status}")
print(f"Response: {data}")
conn.close()
