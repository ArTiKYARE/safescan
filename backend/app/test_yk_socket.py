import socket
import ssl
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
    "description": "Test via raw socket",
}

body = json.dumps(payment_data)

request_lines = [
    "POST /v3/payments HTTP/1.1",
    "Host: api.yookassa.ru",
    "Content-Type: application/json",
    f"Idempotency-Key: test-raw-socket-key-003",
    f"Authorization: Basic {auth_str}",
    f"Content-Length: {len(body)}",
    "Connection: close",
    "",
    body,
]
raw_request = "\r\n".join(request_lines)

print("=== RAW REQUEST (first 300 chars) ===")
print(raw_request[:300])
print("=== END ===\n")

context = ssl.create_default_context()
with socket.create_connection(("api.yookassa.ru", 443)) as sock:
    with context.wrap_socket(sock, server_hostname="api.yookassa.ru") as ssock:
        ssock.sendall(raw_request.encode('utf-8'))
        response = b""
        while True:
            chunk = ssock.recv(4096)
            if not chunk:
                break
            response += chunk

response_str = response.decode('utf-8')
print(f"=== RESPONSE (first 500 chars) ===")
print(response_str[:500])
