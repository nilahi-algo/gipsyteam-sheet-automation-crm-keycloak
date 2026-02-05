import requests
import json
from pathlib import Path

CLIENT_ID = '3110409670709.10443642909361'
CLIENT_SECRET = '50dda835146785f90c2222d5a7ca6459'
CODE = '3110409670709.10434728654068.d6943e18344280373dc0c728b6739af98ebefa8c517f43d2c4aea'

response = requests.post(
    'https://slack.com/api/oauth.v2.access',
    data={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': CODE
    }
)

data = response.json()
print(json.dumps(data, indent=2))

if data.get('ok'):
    # Save token
    CACHE_DIR = Path.home() / '.slack-tokens'
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    user_info = {
        'access_token': data.get('authed_user', {}).get('access_token'),
        'user_id': data.get('authed_user', {}).get('id'),
        'team': data.get('team', {}).get('name'),
        'team_id': data.get('team', {}).get('id')
    }
    
    (CACHE_DIR / 'user_token.json').write_text(json.dumps(user_info, indent=2))
    print('\n[OK] Token saved!')
    print('Team:', user_info.get('team'))
    print('User ID:', user_info.get('user_id'))
else:
    print('\n[ERROR]', data.get('error'))
