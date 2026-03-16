import requests
try:
    resp = requests.post("http://127.0.0.1:8000/api/register", json={
        "username": "testuser_new_123",
        "password": "password123",
        "email": "testuser_new_123@example.com",
        "mobile": "1234567890"
    })
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")
except Exception as e:
    print(f"Error: {e}")
