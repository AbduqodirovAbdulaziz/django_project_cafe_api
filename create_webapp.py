import urllib.request
import urllib.parse
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

token = '7cf4c273679839b25bab261b2446894ced34925d'
username = 'cafeapi'

data = urllib.parse.urlencode({
    'domain_name': 'cafeapi.pythonanywhere.com',
    'python_version': 'python313',
    'source_directory': '/home/cafeapi/cafe_api',
    'working_directory': '/home/cafeapi/cafe_api',
    'virtualenv_path': '/home/cafeapi/cafe_api/venv',
}).encode()

req = urllib.request.Request(
    'https://www.pythonanywhere.com/api/v0/user/' + username + '/webapps/',
    data=data,
    headers={'Authorization': 'Token ' + token},
    method='POST'
)

try:
    with urllib.request.urlopen(req) as r:
        result = json.loads(r.read().decode())
        print('Web App yaratildi:')
        print(json.dumps(result, indent=2))
except urllib.error.HTTPError as e:
    print('Error:', e.code, e.read().decode())
