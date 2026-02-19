import urllib.request
import json

token = '7cf4c273679839b25bab261b2446894ced34925d'
username = 'cafeapi'

script_content = (
    "cd ~\n"
    "git clone https://github.com/AbduqodirovAbdulaziz/django_project_cafe_api.git cafe_api\n"
    "cd cafe_api\n"
    "python3 -m venv venv\n"
    "source venv/bin/activate\n"
    "pip install -r requirements.txt\n"
    "python manage.py migrate\n"
    "python manage.py collectstatic --noinput\n"
    "echo SETUP_DONE\n"
)

boundary = 'FormBoundary7MA4YWxkTrZu0gW'
body = (
    '--' + boundary + '\r\n'
    'Content-Disposition: form-data; name="content"; filename="setup.sh"\r\n'
    'Content-Type: text/plain\r\n'
    '\r\n'
    + script_content +
    '\r\n--' + boundary + '--\r\n'
)
data = body.encode('utf-8')

req = urllib.request.Request(
    'https://www.pythonanywhere.com/api/v0/user/' + username + '/files/path/home/' + username + '/setup.sh',
    data=data,
    headers={
        'Authorization': 'Token ' + token,
        'Content-Type': 'multipart/form-data; boundary=' + boundary
    },
    method='POST'
)

try:
    with urllib.request.urlopen(req) as r:
        print('Status:', r.status)
        print(r.read().decode())
except urllib.error.HTTPError as e:
    print('HTTPError:', e.code, e.read().decode())
except Exception as e:
    print('Error:', e)
