import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

token = '7cf4c273679839b25bab261b2446894ced34925d'
username = 'cafeapi'

# Mavjud web app ma'lumotlarini olish
req = urllib.request.Request(
    'https://www.pythonanywhere.com/api/v0/user/' + username + '/webapps/',
    headers={'Authorization': 'Token ' + token},
    method='GET'
)

with urllib.request.urlopen(req) as r:
    result = json.loads(r.read().decode())
    print(json.dumps(result, indent=2))
