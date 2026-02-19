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

# Token
auth = post('/api/auth/login/', {'username': 'cafe_manager', 'password': 'CafeManager@2026#Secure'})
token = auth['access']
print('Token olindi!')

# Kategoriya IDlar
cat_ids = {
    'Salatlar': 1, "Sho'rvalar": 2, 'Asosiy taomlar': 3,
    'Ichimliklar': 4, 'Desertlar': 5, 'Fastfood': 6, 'Milliy taomlar': 7
}

# Taomlar
print('\n=== TAOMLAR ===')
menu_items = [
    # Salatlar
    {'name': 'Aralash salat', 'category': 1, 'price': '18000', 'description': 'Yangi sabzavotlardan tayyorlangan salat', 'is_available': True},
    {'name': 'Grek salatı', 'category': 1, 'price': '22000', 'description': 'Feta pishloq va zaytun bilan', 'is_available': True},
    {'name': 'Toshkent salatı', 'category': 1, 'price': '20000', 'description': 'Mol go\'shti va turp bilan', 'is_available': True},

    # Sho'rvalar
    {'name': 'Mastava', 'category': 2, 'price': '25000', 'description': 'Guruchli o\'zbek sho\'rvasi', 'is_available': True},
    {'name': 'Lagmon', 'category': 2, 'price': '30000', 'description': 'Qo\'lda tortilgan qozon lagmon', 'is_available': True},
    {'name': 'Moshurhurda', 'category': 2, 'price': '22000', 'description': 'Mosh va guruchdan tayyorlangan', 'is_available': True},

    # Asosiy taomlar
    {'name': 'Kabob', 'category': 3, 'price': '45000', 'description': 'Qo\'y go\'shtidan tayyorlangan kabob (6 dona)', 'is_available': True},
    {'name': 'Tovuq grilli', 'category': 3, 'price': '55000', 'description': 'Butun tovuq grillda pishirilgan', 'is_available': True},
    {'name': 'Qovurma go\'sht', 'category': 3, 'price': '50000', 'description': 'Sabzavotlar bilan qovurilgan mol go\'shti', 'is_available': True},

    # Ichimliklar
    {'name': 'Ko\'k choy', 'category': 4, 'price': '8000', 'description': 'Chinni choynak, 500ml', 'is_available': True},
    {'name': 'Qora choy', 'category': 4, 'price': '8000', 'description': 'Limon bilan, 500ml', 'is_available': True},
    {'name': 'Limonad', 'category': 4, 'price': '15000', 'description': 'Tabiiy mevalardan tayyorlangan', 'is_available': True},
    {'name': 'Kompot', 'category': 4, 'price': '10000', 'description': 'Quritilgan mevalardan, 1L', 'is_available': True},

    # Desertlar
    {'name': 'Chak-chak', 'category': 5, 'price': '20000', 'description': 'An\'anaviy o\'zbek shirinligi', 'is_available': True},
    {'name': 'Tort', 'category': 5, 'price': '35000', 'description': 'Kunlik yangi tort (1 bo\'lak)', 'is_available': True},
    {'name': 'Muzqaymoq', 'category': 5, 'price': '18000', 'description': 'Krema muzqaymoq (2 shar)', 'is_available': True},

    # Fastfood
    {'name': 'Burger', 'category': 6, 'price': '32000', 'description': 'Mol go\'shti kotletasi, pomidor, karam', 'is_available': True},
    {'name': 'Qovurilgan kartoshka', 'category': 6, 'price': '15000', 'description': 'Sous bilan, 200g', 'is_available': True},
    {'name': 'Hot-dog', 'category': 6, 'price': '22000', 'description': 'Sosiska va sabzavotlar bilan', 'is_available': True},

    # Milliy taomlar
    {'name': 'Osh (palov)', 'category': 7, 'price': '35000', 'description': 'An\'anaviy o\'zbek palovi, 1 porsiya', 'is_available': True},
    {'name': 'Somsa', 'category': 7, 'price': '12000', 'description': 'Tandirda pishirilgan go\'shtli somsa (2 dona)', 'is_available': True},
    {'name': 'Manti', 'category': 7, 'price': '28000', 'description': 'Bug\'da pishirilgan manti (5 dona)', 'is_available': True},
]

for item in menu_items:
    r = post('/api/menu-items/', item, token)
    if r and r.get('id'):
        print(f'  + {item["name"]} - {item["price"]} so\'m (id={r["id"]})')

# Stollar
print('\n=== STOLLAR ===')
tables = [
    {'number': 1, 'capacity': 2, 'location': 'Ichki zal'},
    {'number': 2, 'capacity': 2, 'location': 'Ichki zal'},
    {'number': 3, 'capacity': 4, 'location': 'Ichki zal'},
    {'number': 4, 'capacity': 4, 'location': 'Ichki zal'},
    {'number': 5, 'capacity': 4, 'location': 'Ichki zal'},
    {'number': 6, 'capacity': 6, 'location': 'Ichki zal'},
    {'number': 7, 'capacity': 6, 'location': 'Tashqi terrassa'},
    {'number': 8, 'capacity': 4, 'location': 'Tashqi terrassa'},
    {'number': 9, 'capacity': 4, 'location': 'Tashqi terrassa'},
    {'number': 10, 'capacity': 8, 'location': 'VIP xona'},
]

for table in tables:
    r = post('/api/tables/', table, token)
    if r and r.get('id'):
        print(f'  + Stol #{table["number"]} - {table["capacity"]} kishi - {table["location"]} (id={r["id"]})')

print('\n=== HAMMASI TAYYOR ===')
