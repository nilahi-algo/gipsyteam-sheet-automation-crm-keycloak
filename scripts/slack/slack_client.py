"""
Slack Client Helper
Uses Bot Token for workspace-wide access
"""
import os
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Load environment variables
load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")


def get_client():
    """Get Slack WebClient with Bot Token"""
    if not SLACK_BOT_TOKEN:
        raise ValueError("SLACK_BOT_TOKEN not found in environment")
    return WebClient(token=SLACK_BOT_TOKEN)


def test_connection():
    """Test the Slack connection"""
    client = get_client()
    try:
        # Test auth
        response = client.auth_test()
        print(f"[OK] Connected to Slack!")
        print(f"    Workspace: {response['team']}")
        print(f"    Bot User: {response['user']}")
        print(f"    Bot ID: {response['user_id']}")
        return response
    except SlackApiError as e:
        print(f"[ERROR] {e.response['error']}")
        return None


if __name__ == "__main__":
    test_connection()
