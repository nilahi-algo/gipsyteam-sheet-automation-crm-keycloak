"""
Authentication helper for M365 Graph API using Himalaya App (Delegated Permissions)
Uses persistent token cache with refresh token support (no repeated sign-ins)
"""
import os
import json
import msal
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import InteractiveBrowserCredential, AuthenticationRecord, TokenCachePersistenceOptions
from azure.core.credentials import AccessToken

# Load environment variables
load_dotenv()

TENANT_ID = os.getenv("ENTRA_HIMALAYA_TENANT_ID")
CLIENT_ID = os.getenv("ENTRA_HIMALAYA_CLIENT_ID")
CACHE_DIR = Path.home() / ".azure-certs"
AUTH_RECORD_PATH = CACHE_DIR / "himalaya_auth_record.json"
TOKEN_CACHE_PATH = CACHE_DIR / "himalaya_token_cache.json"

# Scopes for email management
MAIL_SCOPES = [
    "User.Read",
    "Mail.Read",
    "Mail.Send",
    "Mail.ReadWrite",
    "MailboxSettings.Read"
]


class RefreshTokenCredential:
    """Credential that uses MSAL with persistent token cache for refresh token support"""
    
    def __init__(self, tenant_id: str, client_id: str, scopes: list):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.scopes = scopes
        self.cache = msal.SerializableTokenCache()
        
        # Ensure cache directory exists
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load existing cache
        if TOKEN_CACHE_PATH.exists():
            self.cache.deserialize(TOKEN_CACHE_PATH.read_text())
        
        # Create MSAL app
        self.app = msal.PublicClientApplication(
            client_id=self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            token_cache=self.cache
        )
    
    def _save_cache(self):
        """Save token cache to disk"""
        if self.cache.has_state_changed:
            TOKEN_CACHE_PATH.write_text(self.cache.serialize())
    
    def get_token(self, *scopes, **kwargs):
        """Get access token, using refresh token if available"""
        scopes_list = list(scopes) if scopes else self.scopes
        
        # Try to get token silently (using refresh token)
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(scopes_list, account=accounts[0])
            if result and "access_token" in result:
                print(f"Using cached token for {accounts[0]['username']}")
                self._save_cache()
                return AccessToken(result["access_token"], result["expires_in"])
        
        # No cached token, need interactive login
        print("Opening browser for authentication (first time only)...")
        result = self.app.acquire_token_interactive(
            scopes=scopes_list,
            prompt="select_account"
        )
        
        if "access_token" in result:
            print(f"Logged in as: {result.get('id_token_claims', {}).get('preferred_username', 'Unknown')}")
            self._save_cache()
            return AccessToken(result["access_token"], result["expires_in"])
        else:
            error = result.get("error_description", result.get("error", "Unknown error"))
            raise Exception(f"Authentication failed: {error}")


def get_credential():
    """Get authenticated credential with refresh token support"""
    return RefreshTokenCredential(TENANT_ID, CLIENT_ID, MAIL_SCOPES)


def clear_cache():
    """Clear the authentication cache"""
    cleared = False
    if AUTH_RECORD_PATH.exists():
        AUTH_RECORD_PATH.unlink()
        cleared = True
    if TOKEN_CACHE_PATH.exists():
        TOKEN_CACHE_PATH.unlink()
        cleared = True
    
    if cleared:
        print("Authentication cache cleared.")
    else:
        print("No cache to clear.")


def show_accounts():
    """Show cached accounts"""
    if not TOKEN_CACHE_PATH.exists():
        print("No cached accounts.")
        return
    
    cache = msal.SerializableTokenCache()
    cache.deserialize(TOKEN_CACHE_PATH.read_text())
    
    app = msal.PublicClientApplication(
        client_id=CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        token_cache=cache
    )
    
    accounts = app.get_accounts()
    if accounts:
        print("Cached accounts:")
        for acc in accounts:
            print(f"  - {acc['username']}")
    else:
        print("No cached accounts.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "clear":
            clear_cache()
        elif sys.argv[1] == "accounts":
            show_accounts()
        else:
            print("Usage: python auth.py [clear|accounts]")
    else:
        # Test authentication
        credential = get_credential()
        token = credential.get_token("https://graph.microsoft.com/.default")
        print("Authentication successful!")
