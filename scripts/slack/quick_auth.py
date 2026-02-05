"""Quick OAuth - paste code as argument"""
import sys
import requests
import json
from pathlib import Path

CLIENT_ID = '3110409670709.10443642909361'
CLIENT_SECRET = '50dda835146785f90c2222d5a7ca6459'

if len(sys.argv) < 2:
    print("Usage: python quick_auth.py <CODE>")
    print("\nGet the code by visiting:")
    print("https://slack.com/oauth/v2/authorize?client_id=3110409670709.10443642909361&user_scope=channels:read,channels:history,chat:write,users:read&redirect_uri=https://localhost:8080/callback")
    print("\nAfter allowing, copy the code from the URL and run:")
    print("python quick_auth.py YOUR_CODE_HERE")
    sys.exit(1)

CODE = sys.argv[1]

print("Exchanging code for token...")
response = requests.post(
    'https://slack.com/api/oauth.v2.access',
    data={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': CODE,
        'redirect_uri': 'https://localhost:8080/callback'
    }
)

data = response.json()

if data.get('ok'):
    CACHE_DIR = Path.home() / '.slack-tokens'
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    user_info = {
        'access_token': data.get('authed_user', {}).get('access_token'),
        'user_id': data.get('authed_user', {}).get('id'),
        'team': data.get('team', {}).get('name'),
        'team_id': data.get('team', {}).get('id')
    }
    
    (CACHE_DIR / 'user_token.json').write_text(json.dumps(user_info, indent=2))
    print('[OK] Token saved!')
    print('Team:', user_info.get('team'))
    print('User ID:', user_info.get('user_id'))
else:
    print('[ERROR]', data.get('error'))
    print(json.dumps(data, indent=2))
