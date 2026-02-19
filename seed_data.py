import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE = 'https://cafeapi.pythonanywhere.com'

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
        print('Error', e.code, url, e.read().decode()[:200])
        return None

# 1. Token olish
print('=== TOKEN OLISH ===')
auth = post('/api/auth/login/', {'username': 'cafe_manager', 'password': 'CafeManager@2026#Secure'})
if not auth:
    exit()
token = auth['access']
print('Token olindi!')

# 2. Kategoriyalar
print('\n=== KATEGORIYALAR ===')
categories = [
    'Salatlar', "Sho'rvalar", 'Asosiy taomlar',
    'Ichimliklar', 'Desertlar', 'Fastfood', 'Milliy taomlar'
]
cat_ids = {}
for name in categories:
    r = post('/api/categories/', {'name': name}, token)
    if r and r.get('id'):
        cat_ids[name] = r['id']
        print(f'  + {name} (id={r["id"]})')

print('Kategoriyalar:', cat_ids)
