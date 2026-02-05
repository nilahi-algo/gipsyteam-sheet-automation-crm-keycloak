# Slack User OAuth Setup for Cursor AI

This document provides instructions for Cursor AI to set up Slack integration with User OAuth (personal access to your own Slack channels).

---

## Overview

This setup allows you to:
- Read messages from channels YOU are a member of
- Send messages as yourself
- List your channels and users
- **Your access is personal** - you only see channels you're part of

---

## Prerequisites

- Python 3.10+ installed
- Cursor AI
- A Slack account in the AlgoSoftware workspace

---

## Slack App Credentials (Already Configured)

```
SLACK_CLIENT_ID=3110409670709.10443642909361
SLACK_CLIENT_SECRET=50dda835146785f90c2222d5a7ca6459
SLACK_APP_ID=A0AD1JWSRAM
REDIRECT_URI=https://localhost:8080/callback
```

The Slack App "cursor intergration" is already set up with:
- **User Token Scopes**: `channels:read`, `channels:history`, `chat:write`, `users:read`, `groups:read`, `groups:history`
- **Redirect URL**: `https://localhost:8080/callback`

> **Note about Redirect URL**: Slack requires HTTPS for redirect URLs. We use `https://localhost:8080/callback` which will show "site can't be reached" after authorization - this is expected. The authorization code is in the URL which we copy manually.

---

## Setup Instructions for Cursor AI

### Step 1: Create the scripts folder

Create a folder for Slack scripts:
```
scripts/slack/
```

### Step 2: Create requirements.txt

Create `scripts/slack/requirements.txt`:
```
slack-sdk>=3.27.0
python-dotenv>=1.0.0
requests>=2.28.0
```

### Step 3: Create .env file

Create `scripts/slack/.env`:
```
# Slack App Credentials
SLACK_CLIENT_ID=3110409670709.10443642909361
SLACK_CLIENT_SECRET=50dda835146785f90c2222d5a7ca6459
SLACK_APP_ID=A0AD1JWSRAM
```

### Step 4: Create quick_auth.py

Create `scripts/slack/quick_auth.py`:
```python
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
    print("https://slack.com/oauth/v2/authorize?client_id=3110409670709.10443642909361&user_scope=channels:read,channels:history,chat:write,users:read,groups:read,groups:history&redirect_uri=https://localhost:8080/callback")
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
```

### Step 5: Create user_auth.py

Create `scripts/slack/user_auth.py`:
```python
"""
Slack User OAuth Authentication
Each user authenticates with their own account - only sees their own channels
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = Path.home() / '.slack-tokens'
TOKEN_FILE = CACHE_DIR / 'user_token.json'


def load_token():
    """Load token from cache"""
    if TOKEN_FILE.exists():
        data = json.loads(TOKEN_FILE.read_text())
        if data.get("access_token"):
            return data
    return None


def get_user_token():
    """Get user token (load from cache)"""
    token = load_token()
    if token and token.get("access_token"):
        return token.get("access_token")
    return None


def clear_token():
    """Clear cached token"""
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
        print("[OK] Token cache cleared")
    else:
        print("No cached token found")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        clear_token()
    else:
        token = load_token()
        if token:
            print(f"Cached token for team: {token.get('team')}")
            print(f"User ID: {token.get('user_id')}")
        else:
            print("No cached token. Run quick_auth.py to authenticate.")
```

### Step 6: Create manage_slack_user.py

Create `scripts/slack/manage_slack_user.py`:
```python
"""
Slack Management Script - User Token Version
Each user only sees channels they are a member of
"""
import os
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from user_auth import get_user_token, load_token

load_dotenv()


def get_client():
    """Get Slack WebClient with User Token"""
    token = get_user_token()
    if not token:
        print("[ERROR] No user token available. Run: python quick_auth.py <CODE>")
        sys.exit(1)
    return WebClient(token=token)


def list_my_channels(client: WebClient):
    """List channels the user is a member of"""
    try:
        response = client.users_conversations(types="public_channel,private_channel")
        channels = response["channels"]
        
        print("\n[MY CHANNELS] Channels you are a member of:")
        print("-" * 60)
        print(f"{'Channel':<30} {'Members':>10} {'Type':<10}")
        print("-" * 60)
        
        for channel in sorted(channels, key=lambda x: x["name"]):
            name = f"#{channel['name']}"
            members = channel.get("num_members", 0)
            ch_type = "Private" if channel.get("is_private") else "Public"
            print(f"{name:<30} {members:>10} {ch_type:<10}")
        
        print("-" * 60)
        print(f"Total: {len(channels)} channels")
        return channels
    except SlackApiError as e:
        print(f"[ERROR] {e.response['error']}")
        return None


def list_messages(client: WebClient, channel: str, count: int = 10):
    """List recent messages from a channel"""
    try:
        if channel.startswith("#"):
            channel = channel[1:]
        
        response = client.users_conversations(types="public_channel,private_channel")
        channel_id = None
        for ch in response["channels"]:
            if ch["name"] == channel:
                channel_id = ch["id"]
                break
        
        if not channel_id:
            print(f"[ERROR] Channel #{channel} not found or you're not a member")
            return None
        
        messages_response = client.conversations_history(channel=channel_id, limit=count)
        messages = messages_response["messages"]
        
        print(f"\n[MESSAGES] Last {count} messages in #{channel}:")
        print("-" * 80)
        
        for msg in messages:
            user_id = msg.get("user", "Unknown")
            try:
                user_info = client.users_info(user=user_id)
                username = user_info["user"]["real_name"]
            except:
                username = user_id
            
            timestamp = datetime.fromtimestamp(float(msg["ts"])).strftime("%Y-%m-%d %H:%M")
            text = msg.get("text", "")[:60]
            print(f"{timestamp} | {username:<20} | {text}")
        
        return messages
    except SlackApiError as e:
        print(f"[ERROR] {e.response['error']}")
        return None


def send_message(client: WebClient, channel: str, message: str):
    """Send a message to a channel"""
    try:
        if channel.startswith("#"):
            channel = channel[1:]
        
        response = client.users_conversations(types="public_channel,private_channel")
        channel_id = None
        for ch in response["channels"]:
            if ch["name"] == channel:
                channel_id = ch["id"]
                break
        
        if not channel_id:
            print(f"[ERROR] Channel #{channel} not found or you're not a member")
            return None
        
        response = client.chat_postMessage(channel=channel_id, text=message)
        print(f"[OK] Message sent to #{channel}")
        return response
    except SlackApiError as e:
        print(f"[ERROR] {e.response['error']}")
        return None


def show_me(client: WebClient):
    """Show current user info"""
    try:
        response = client.auth_test()
        print(f"\n[USER] Logged in as:")
        print(f"    Name: {response['user']}")
        print(f"    User ID: {response['user_id']}")
        print(f"    Team: {response['team']}")
        return response
    except SlackApiError as e:
        print(f"[ERROR] {e.response['error']}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Manage Slack (User Token - Personal Access)")
    parser.add_argument("command", choices=["channels", "messages", "send", "me"],
                       help="Command to execute")
    parser.add_argument("--channel", "-c", help="Channel name")
    parser.add_argument("--count", "-n", type=int, default=10, help="Number of items")
    parser.add_argument("--message", "-m", help="Message to send")
    
    args = parser.parse_args()
    client = get_client()
    
    if args.command == "me":
        show_me(client)
    elif args.command == "channels":
        list_my_channels(client)
    elif args.command == "messages":
        if not args.channel:
            print("Error: --channel is required")
            sys.exit(1)
        list_messages(client, args.channel, args.count)
    elif args.command == "send":
        if not args.channel or not args.message:
            print("Error: --channel and --message are required")
            sys.exit(1)
        send_message(client, args.channel, args.message)


if __name__ == "__main__":
    main()
```

### Step 7: Install dependencies

```bash
cd scripts/slack
python -m pip install slack-sdk python-dotenv requests
```

### Step 8: Authenticate the User

**This is the OAuth flow - follow these steps:**

1. **Open the authorization URL in browser:**
   ```
   https://slack.com/oauth/v2/authorize?client_id=3110409670709.10443642909361&user_scope=channels:read,channels:history,chat:write,users:read,groups:read,groups:history&redirect_uri=https://localhost:8080/callback
   ```

2. **Sign in with your Slack account** (use your work email)

3. **Click "Allow"** to authorize the app

4. **You'll be redirected to a page that won't load** - this is expected!
   - The URL will look like: `https://localhost:8080/callback?code=XXXXX...&state=`
   - **Copy the code** from the URL (everything after `code=` until `&state`)

5. **Run the authentication command:**
   ```bash
   cd scripts/slack
   python quick_auth.py YOUR_CODE_HERE
   ```

6. **Verify it worked:**
   ```bash
   python manage_slack_user.py me
   ```

---

## Usage Examples

After authentication, you can use these commands:

```bash
cd scripts/slack

# Show who you're logged in as
python manage_slack_user.py me

# List all channels you're a member of
python manage_slack_user.py channels

# Read last 10 messages from a channel
python manage_slack_user.py messages --channel general -n 10

# Send a message to a channel
python manage_slack_user.py send --channel general --message "Hello from automation!"
```

---

## Troubleshooting

### "invalid_code" error
- Authorization codes expire in ~10 minutes
- Get a new code by visiting the authorization URL again

### "missing_scope" error
- The app may not have the required permissions
- Contact the admin to verify User Token Scopes are configured

### "channel not found" error
- You can only access channels you are a member of
- Join the channel in Slack first

### Redirect URL Issues
- Slack requires HTTPS for redirect URLs (http:// won't work)
- The "site can't be reached" error is expected - just copy the code from the URL
- Make sure to copy the code before `&state` in the URL

---

## Token Information

- **Token location:** `~/.slack-tokens/user_token.json`
- **Token expiry:** Never (Slack tokens don't expire)
- **Token invalidation:** Only if app is uninstalled or access is revoked

To clear your token and re-authenticate:
```bash
python user_auth.py clear
```

---

## Security Notes

- Your token is stored locally in your home directory
- Only YOU can access channels you're a member of
- The token acts as YOU - messages sent appear from your account
- Never share your token with others
