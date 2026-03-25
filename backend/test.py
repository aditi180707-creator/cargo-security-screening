import requests

url = "http://127.0.0.1:5000/predict"

files = {'image': open('test.jpg', 'rb')}

response = requests.post(url, files=files)

print("STATUS:", response.status_code)
print("TEXT:", response.text)   # 👈 ADD THIS