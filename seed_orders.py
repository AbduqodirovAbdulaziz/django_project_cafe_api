import urllib.request
import json
import sys
import random

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

def patch(url, data, token):
    body = json.dumps(data).encode('utf-8')
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token}
    req = urllib.request.Request(BASE + url, data=body, headers=headers, method='PATCH')
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print('Patch Error', e.code, url, e.read().decode()[:200])
        return None

# Token
auth = post('/api/auth/login/', {'username': 'cafe_manager', 'password': 'CafeManager@2026#Secure'})
token = auth['access']
print('Token olindi!')

# =====================
# BUYURTMALAR (status=NEW katta harf)
# =====================
print('\n=== BUYURTMALAR ===')

dine_in_orders = [
    {'table': 1,  'items': [{'menu_item_id': 20, 'qty': 2}, {'menu_item_id': 10, 'qty': 2}]},
    {'table': 2,  'items': [{'menu_item_id': 7,  'qty': 2}, {'menu_item_id': 12, 'qty': 2}, {'menu_item_id': 1,  'qty': 2}]},
    {'table': 3,  'items': [{'menu_item_id': 5,  'qty': 3}, {'menu_item_id': 13, 'qty': 3}, {'menu_item_id': 14, 'qty': 3}]},
    {'table': 4,  'items': [{'menu_item_id': 8,  'qty': 2}, {'menu_item_id': 11, 'qty': 2}, {'menu_item_id': 16, 'qty': 2}]},
    {'table': 5,  'items': [{'menu_item_id': 21, 'qty': 4}, {'menu_item_id': 4,  'qty': 2}, {'menu_item_id': 10, 'qty': 4}]},
    {'table': 6,  'items': [{'menu_item_id': 22, 'qty': 5}, {'menu_item_id': 9,  'qty': 2}, {'menu_item_id': 15, 'qty': 5}]},
    {'table': 7,  'items': [{'menu_item_id': 3,  'qty': 2}, {'menu_item_id': 6,  'qty': 2}, {'menu_item_id': 12, 'qty': 2}]},
    {'table': 8,  'items': [{'menu_item_id': 17, 'qty': 3}, {'menu_item_id': 18, 'qty': 3}, {'menu_item_id': 11, 'qty': 3}]},
    {'table': 9,  'items': [{'menu_item_id': 2,  'qty': 2}, {'menu_item_id': 5,  'qty': 2}, {'menu_item_id': 13, 'qty': 2}]},
    {'table': 10, 'items': [{'menu_item_id': 7,  'qty': 4}, {'menu_item_id': 20, 'qty': 4}, {'menu_item_id': 15, 'qty': 4}, {'menu_item_id': 10, 'qty': 4}]},
]

order_ids = []
for o in dine_in_orders:
    data = {
        'order_type': 'DINE_IN',
        'table': o['table'],
        'create_items': o['items'],
    }
    r = post('/api/orders/', data, token)
    if r and r.get('id'):
        order_ids.append({'id': r['id'], 'total': r.get('total', 0)})
        print(f'  + Stol #{o["table"]} — {r.get("total", "?")} so\'m (id={r["id"]})')

takeaway_orders = [
    {'customer_name': 'Akbar Sobirov',    'customer_phone': '+998901234567', 'items': [{'menu_item_id': 20, 'qty': 1}, {'menu_item_id': 21, 'qty': 2}]},
    {'customer_name': 'Zulfiya Hasanova', 'customer_phone': '+998907654321', 'items': [{'menu_item_id': 7,  'qty': 2}, {'menu_item_id': 12, 'qty': 1}]},
    {'customer_name': 'Mirzo Tursunov',   'customer_phone': '+998991112233', 'items': [{'menu_item_id': 17, 'qty': 2}, {'menu_item_id': 18, 'qty': 1}, {'menu_item_id': 11, 'qty': 2}]},
]

for o in takeaway_orders:
    data = {
        'order_type': 'TAKEAWAY',
        'customer_name': o['customer_name'],
        'customer_phone': o['customer_phone'],
        'create_items': o['items'],
    }
    r = post('/api/orders/', data, token)
    if r and r.get('id'):
        order_ids.append({'id': r['id'], 'total': r.get('total', 0)})
        print(f'  + Takeaway: {o["customer_name"]} — {r.get("total", "?")} so\'m (id={r["id"]})')

# =====================
# TO'LOVLAR - dastlabki 7 ta buyurtma
# =====================
print('\n=== TOLLOVLAR ===')
methods = ['cash', 'cash', 'cash', 'card', 'cash', 'card', 'cash']
for i, o in enumerate(order_ids[:7]):
    r = post('/api/payments/', {
        'order': o['id'],
        'method': methods[i],
        'amount': str(o['total']),
    }, token)
    if r and r.get('id'):
        m = 'Naqd' if r.get('method') == 'cash' else 'Karta'
        print(f'  + Buyurtma #{o["id"]} — {r.get("amount")} so\'m — {m}')

print('\n=== HAMMASI TAYYOR ===')
print(f'  Buyurtmalar: {len(order_ids)} ta (10 DINE_IN + 3 TAKEAWAY)')
print(f'  Tolangan: 7 ta')
print(f'  Kutilmoqda: {len(order_ids) - 7} ta')
