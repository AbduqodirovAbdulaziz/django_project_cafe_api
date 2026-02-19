import urllib.request
import urllib.parse
import json
import time

token = '7cf4c273679839b25bab261b2446894ced34925d'
username = 'cafeapi'

# Yangi console yaratish
data = urllib.parse.urlencode({
    'executable': 'bash',
    'arguments': '/home/cafeapi/setup.sh',
    'working_directory': '/home/cafeapi'
}).encode()

req = urllib.request.Request(
    'https://www.pythonanywhere.com/api/v0/user/' + username + '/consoles/',
    data=data,
    headers={'Authorization': 'Token ' + token},
    method='POST'
)

with urllib.request.urlopen(req) as r:
    result = json.loads(r.read().decode())
    console_id = result['id']
    print('Console ID:', console_id)

# 60 soniya kutamiz
print('Setup bajarilmoqda, 60 soniya kutilmoqda...')
time.sleep(60)

# Output olish
req2 = urllib.request.Request(
    'https://www.pythonanywhere.com/api/v0/user/' + username + '/consoles/' + str(console_id) + '/get_latest_output/',
    headers={'Authorization': 'Token ' + token},
    method='GET'
)
with urllib.request.urlopen(req2) as r:
    out = json.loads(r.read().decode())
    print('OUTPUT:')
    print(out.get('output', ''))
