import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE = 'https://cafeapi.pythonanywhere.com'

def get(url, token):
    req = urllib.request.Request(BASE + url, headers={'Authorization': 'Bearer ' + token})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

def post(url, data, token=None):
    body = json.dumps(data).encode('utf-8')
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request(BASE + url, data=body, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print('Error', e.code, e.read().decode()[:200])
        return None

# Token
auth = post('/api/auth/login/', {'username': 'cafe_manager', 'password': 'CafeManager@2026#Secure'})
token = auth['access']

# Django admin orqali permissions olish uchun - manage.py shell ishlatamiz
# Avval mavjud permission codename larni konsolga chiqaramiz
print('Token:', token[:30], '...')
