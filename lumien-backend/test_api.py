import requests

try:
    r = requests.get("http://localhost:8000/")
    print(f"Root: {r.status_code} - {r.text}")
    
    r = requests.post("http://localhost:8000/api/v1/auth/login", 
                      data={"username": "admin", "password": "fiducia123"},
                      headers={"Content-Type": "application/x-www-form-urlencoded"})
    print(f"Login: {r.status_code} - {r.text}")
except Exception as e:
    print(f"Error: {e}")
