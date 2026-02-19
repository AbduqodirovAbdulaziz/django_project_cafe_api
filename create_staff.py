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
        print('Error', e.code, e.read().decode()[:300])
        return None

# Token
auth = post('/api/auth/login/', {'username': 'cafe_manager', 'password': 'CafeManager@2026#Secure'})
token = auth['access']
print('Token olindi!')

# Xodimlar
xodimlar = [
    # Oshpazlar
    {'first_name': 'Jasur',     'last_name': 'Toshmatov',  'username': 'oshpaz_jasur',   'role': 'cook'},
    {'first_name': 'Bobur',     'last_name': 'Rahimov',    'username': 'oshpaz_bobur',   'role': 'cook'},
    {'first_name': 'Sardor',    'last_name': 'Yusupov',    'username': 'oshpaz_sardor',  'role': 'cook'},
    {'first_name': 'Dilshod',   'last_name': 'Nazarov',    'username': 'oshpaz_dilshod', 'role': 'cook'},
    {'first_name': 'Ulugbek',   'last_name': 'Karimov',    'username': 'oshpaz_ulugbek', 'role': 'cook'},
    {'first_name': 'Mansur',    'last_name': 'Holiqov',    'username': 'oshpaz_mansur',  'role': 'cook'},
    # Ofitsiantlar
    {'first_name': 'Malika',    'last_name': 'Ergasheva',  'username': 'ofitsiant_malika',  'role': 'waiter'},
    {'first_name': 'Nilufar',   'last_name': 'Qodirova',   'username': 'ofitsiant_nilufar', 'role': 'waiter'},
    {'first_name': 'Shahlo',    'last_name': 'Mirzayeva',  'username': 'ofitsiant_shahlo',  'role': 'waiter'},
]

print('\n=== XODIMLAR YARATILMOQDA ===')
for x in xodimlar:
    data = {
        'username': x['username'],
        'first_name': x['first_name'],
        'last_name': x['last_name'],
        'password': 'Cafe@2026#' + x['first_name'],
        'role': x['role'],
    }
    r = post('/api/auth/register/', data, token)
    if r and r.get('id'):
        print(f"  + {x['first_name']} {x['last_name']} | {x['username']} | parol: Cafe@2026#{x['first_name']}")
    else:
        print(f"  - {x['first_name']} xato!")

print('\n=== TAYYOR ===')
