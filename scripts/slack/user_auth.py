"""
Slack User OAuth Authentication
Each user authenticates with their own account - only sees their own channels
"""
import os
import json
import webbrowser
from pathlib import Path
from urllib.parse import urlencode
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv("SLACK_CLIENT_ID", "3110409670709.10443642909361")
CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET", "50dda835146785f90c2222d5a7ca6459")

# Token cache location
CACHE_DIR = Path.home() / ".slack-tokens"
TOKEN_FILE = CACHE_DIR / "user_token.json"

# User scopes
USER_SCOPES = [
    "channels:read",
    "channels:history",
    "chat:write",
    "users:read"
]


def get_auth_url():
    """Generate the OAuth authorization URL"""
    params = {
        "client_id": CLIENT_ID,
        "user_scope": ",".join(USER_SCOPES),
        "redirect_uri": "https://localhost:8080/callback"
    }
    return f"https://slack.com/oauth/v2/authorize?{urlencode(params)}"


def exchange_code_for_token(code: str):
    """Exchange authorization code for access token"""
    response = requests.post(
        "https://slack.com/api/oauth.v2.access",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code
        }
    )
    
    data = response.json()
    if not data.get("ok"):
        raise Exception(f"Token exchange failed: {data.get('error')}")
    
    return data


def save_token(token_data: dict):
    """Save token to cache"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Extract user token info
    user_info = {
        "access_token": token_data.get("authed_user", {}).get("access_token"),
        "user_id": token_data.get("authed_user", {}).get("id"),
        "team": token_data.get("team", {}).get("name"),
        "team_id": token_data.get("team", {}).get("id")
    }
    
    TOKEN_FILE.write_text(json.dumps(user_info, indent=2))
    print(f"[OK] Token saved to {TOKEN_FILE}")
    return user_info


def load_token():
    """Load token from cache"""
    if TOKEN_FILE.exists():
        data = json.loads(TOKEN_FILE.read_text())
        if data.get("access_token"):
            return data
    return None


def clear_token():
    """Clear cached token"""
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
        print("[OK] Token cache cleared")
    else:
        print("No cached token found")


def authenticate():
    """Run the OAuth flow"""
    print("=" * 60)
    print("Slack User OAuth Authentication")
    print("=" * 60)
    
    # Check for existing token
    existing = load_token()
    if existing:
        print(f"\nExisting token found for team: {existing.get('team')}")
        choice = input("Use existing token? (y/n): ").strip().lower()
        if choice == 'y':
            return existing
        print("Starting new authentication...\n")
    
    # Generate auth URL
    auth_url = get_auth_url()
    
    print("\n1. Opening browser for Slack authorization...")
    print("   If browser doesn't open, visit this URL:\n")
    print(f"   {auth_url}\n")
    
    webbrowser.open(auth_url)
    
    print("2. Sign in with your Slack account and click 'Allow'")
    print("3. You'll be redirected to a page that won't load (that's OK)")
    print("4. Copy the 'code' parameter from the URL\n")
    print("   Example URL: https://localhost/callback?code=XXXXX...")
    print("   Copy everything after 'code=' until the next '&' or end\n")
    
    code = input("Paste the code here: ").strip()
    
    if not code:
        print("[ERROR] No code provided")
        return None
    
    print("\n5. Exchanging code for token...")
    try:
        token_data = exchange_code_for_token(code)
        user_info = save_token(token_data)
        
        print("\n" + "=" * 60)
        print("[OK] Authentication successful!")
        print(f"    Team: {user_info.get('team')}")
        print(f"    User ID: {user_info.get('user_id')}")
        print("=" * 60)
        
        return user_info
    except Exception as e:
        print(f"[ERROR] {e}")
        return None


def get_user_token():
    """Get user token (load from cache or authenticate)"""
    token = load_token()
    if token and token.get("access_token"):
        return token.get("access_token")
    
    print("No cached token found. Starting authentication...")
    result = authenticate()
    if result:
        return result.get("access_token")
    return None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "clear":
            clear_token()
        elif sys.argv[1] == "status":
            token = load_token()
            if token:
                print(f"Cached token for team: {token.get('team')}")
                print(f"User ID: {token.get('user_id')}")
            else:
                print("No cached token")
        else:
            print("Usage: python user_auth.py [clear|status]")
    else:
        authenticate()
