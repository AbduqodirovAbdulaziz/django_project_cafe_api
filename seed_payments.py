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
        print('Error', e.code, url, e.read().decode()[:300])
        return None

auth = post('/api/auth/login/', {'username': 'cafe_manager', 'password': 'CafeManager@2026#Secure'})
token = auth['access']
print('Token olindi!')

# Buyurtma ID va summalari (yuqorida kiritilgan)
orders = [
    {'id': 1,  'total': '86000.00',  'method': 'CASH'},
    {'id': 2,  'total': '156000.00', 'method': 'CARD'},
    {'id': 3,  'total': '180000.00', 'method': 'CASH'},
    {'id': 4,  'total': '162000.00', 'method': 'QR'},
    {'id': 5,  'total': '130000.00', 'method': 'CASH'},
    {'id': 6,  'total': '415000.00', 'method': 'CARD'},
    {'id': 7,  'total': '114000.00', 'method': 'CASH'},
]

print('\n=== TOLLOVLAR ===')
methods_uz = {'CASH': 'Naqd', 'CARD': 'Karta', 'QR': 'QR kod'}
for o in orders:
    r = post('/api/payments/', {
        'order': o['id'],
        'method': o['method'],
        'amount': o['total'],
    }, token)
    if r and r.get('id'):
        print(f"  + Buyurtma #{o['id']} — {o['total']} so'm — {methods_uz[o['method']]} (id={r['id']})")

print('\n=== TOLLOVLAR TAYYOR ===')
