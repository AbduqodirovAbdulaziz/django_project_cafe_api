import urllib.request
import urllib.parse
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

token = '7cf4c273679839b25bab261b2446894ced34925d'
username = 'cafeapi'
domain = 'cafeapi.pythonanywhere.com'

# 1. Web app sozlamalarini yangilash
data = urllib.parse.urlencode({
    'source_directory': '/home/cafeapi/cafe_api',
    'working_directory': '/home/cafeapi/cafe_api',
    'virtualenv_path': '/home/cafeapi/cafe_api/venv',
}).encode()

req = urllib.request.Request(
    'https://www.pythonanywhere.com/api/v0/user/' + username + '/webapps/' + domain + '/',
    data=data,
    headers={'Authorization': 'Token ' + token},
    method='PATCH'
)
with urllib.request.urlopen(req) as r:
    print('Web app yangilandi:', r.status)

# 2. WSGI fayl yozish
wsgi_content = """
import sys
import os

path = '/home/cafeapi/cafe_api'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
"""

boundary = 'FormBoundary7MA4YWxkTrZu0gW'
body = (
    '--' + boundary + '\r\n'
    'Content-Disposition: form-data; name="content"; filename="wsgi.py"\r\n'
    'Content-Type: text/plain\r\n'
    '\r\n'
    + wsgi_content +
    '\r\n--' + boundary + '--\r\n'
)

req2 = urllib.request.Request(
    'https://www.pythonanywhere.com/api/v0/user/' + username + '/files/path/var/www/cafeapi_pythonanywhere_com_wsgi.py',
    data=body.encode('utf-8'),
    headers={
        'Authorization': 'Token ' + token,
        'Content-Type': 'multipart/form-data; boundary=' + boundary
    },
    method='POST'
)
try:
    with urllib.request.urlopen(req2) as r:
        print('WSGI fayl yuklandi:', r.status)
except urllib.error.HTTPError as e:
    print('WSGI error:', e.code, e.read().decode())

# 3. Static files sozlash
static_data = urllib.parse.urlencode({
    'url': '/static/',
    'path': '/home/cafeapi/cafe_api/staticfiles',
}).encode()

req3 = urllib.request.Request(
    'https://www.pythonanywhere.com/api/v0/user/' + username + '/webapps/' + domain + '/static_files/',
    data=static_data,
    headers={'Authorization': 'Token ' + token},
    method='POST'
)
try:
    with urllib.request.urlopen(req3) as r:
        print('Static files sozlandi:', r.status)
except urllib.error.HTTPError as e:
    print('Static error:', e.code, e.read().decode())

# 4. Media files sozlash
media_data = urllib.parse.urlencode({
    'url': '/media/',
    'path': '/home/cafeapi/cafe_api/media',
}).encode()

req4 = urllib.request.Request(
    'https://www.pythonanywhere.com/api/v0/user/' + username + '/webapps/' + domain + '/static_files/',
    data=media_data,
    headers={'Authorization': 'Token ' + token},
    method='POST'
)
try:
    with urllib.request.urlopen(req4) as r:
        print('Media files sozlandi:', r.status)
except urllib.error.HTTPError as e:
    print('Media error:', e.code, e.read().decode())

# 5. Reload
req5 = urllib.request.Request(
    'https://www.pythonanywhere.com/api/v0/user/' + username + '/webapps/' + domain + '/reload/',
    data=b'',
    headers={'Authorization': 'Token ' + token},
    method='POST'
)
with urllib.request.urlopen(req5) as r:
    print('Reload:', r.status)
    print('DONE - https://' + domain)
