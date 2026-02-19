import urllib.request
import urllib.parse
import json

token = '7cf4c273679839b25bab261b2446894ced34925d'
username = 'cafeapi'

# Scheduled task yaratish (once - bir marta)
cmd = "bash /home/cafeapi/setup.sh > /home/cafeapi/setup_log.txt 2>&1"

data = urllib.parse.urlencode({
    'command': cmd,
    'enabled': 'true',
    'interval': 'daily',
    'hour': '0',
    'minute': '0',
    'description': 'Initial setup'
}).encode()

req = urllib.request.Request(
    'https://www.pythonanywhere.com/api/v0/user/' + username + '/schedule/',
    data=data,
    headers={'Authorization': 'Token ' + token},
    method='POST'
)

try:
    with urllib.request.urlopen(req) as r:
        result = json.loads(r.read().decode())
        print(json.dumps(result, indent=2))
except urllib.error.HTTPError as e:
    print('Error:', e.code, e.read().decode())
