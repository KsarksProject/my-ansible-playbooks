import requests

url = "https://172.28.0.251:8006/api2/json/access/ticket"
data = {"username": "root@pam", "password": "D1rectum20!9"}
response = requests.post(url, data=data, verify=False)

if response.status_code == 200:
    print("Authenticated successfully.")
    print(response.json())
else:
    print(f"Authentication failed: {response.status_code}")
    print(response.text)
