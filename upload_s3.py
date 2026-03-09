import urllib.request
import json
import os

with open('ai-you-frontend/public/memorybank.html', 'r', encoding='utf-8') as f:
    content = f.read()

req = urllib.request.Request('http://127.0.0.1:8000/api/v1/s3/object?scope=user&path=membank-edit/memorybank.html', method='PUT')
req.add_header('Content-Type', 'text/html')

try:
    with urllib.request.urlopen(req, data=content.encode('utf-8')) as response:
        print("Success:", response.read().decode())
except urllib.error.HTTPError as e:
    print("Error:", e.read().decode())
