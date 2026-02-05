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

# Load environment variables
load_dotenv()


def get_client():
    """Get Slack WebClient with User Token"""
    token = get_user_token()
    if not token:
        print("[ERROR] No user token available. Run: python user_auth.py")
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
        
        # Find channel in user's channels
        response = client.users_conversations(types="public_channel,private_channel")
        channel_id = None
        for ch in response["channels"]:
            if ch["name"] == channel:
                channel_id = ch["id"]
                break
        
        if not channel_id:
            print(f"[ERROR] Channel #{channel} not found or you're not a member")
            return None
        
        # Get messages
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
        
        # Find channel
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
