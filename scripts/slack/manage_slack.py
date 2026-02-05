"""
Slack Management Script
Workspace-wide automation using Bot Token
"""
import os
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Load environment variables
load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")


def get_client():
    """Get Slack WebClient"""
    return WebClient(token=SLACK_BOT_TOKEN)


def list_users(client: WebClient, include_bots: bool = False):
    """List all users in the workspace"""
    try:
        response = client.users_list()
        users = response["members"]
        
        print("\n[USERS] Workspace Users:")
        print("-" * 70)
        print(f"{'Name':<25} {'Email':<30} {'Status':<10}")
        print("-" * 70)
        
        count = 0
        for user in users:
            if user.get("deleted"):
                continue
            if not include_bots and user.get("is_bot"):
                continue
            if user.get("id") == "USLACKBOT":
                continue
                
            name = user.get("real_name", user.get("name", "Unknown"))
            email = user.get("profile", {}).get("email", "N/A")
            status = "Active" if not user.get("deleted") else "Deleted"
            
            print(f"{name:<25} {email:<30} {status:<10}")
            count += 1
        
        print("-" * 70)
        print(f"Total: {count} users")
        return users
    except SlackApiError as e:
        print(f"[ERROR] {e.response['error']}")
        return None


def list_channels(client: WebClient, include_private: bool = False):
    """List all channels"""
    try:
        # Public channels
        response = client.conversations_list(types="public_channel")
        channels = response["channels"]
        
        if include_private:
            private_response = client.conversations_list(types="private_channel")
            channels.extend(private_response["channels"])
        
        print("\n[CHANNELS] Workspace Channels:")
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
        # Get channel ID if name provided
        if channel.startswith("#"):
            channel = channel[1:]
        
        # Find channel by name - search all types including private
        channel_id = None
        for channel_type in ["public_channel", "private_channel"]:
            try:
                channels_response = client.conversations_list(types=channel_type)
                for ch in channels_response["channels"]:
                    if ch["name"] == channel:
                        channel_id = ch["id"]
                        break
                if channel_id:
                    break
            except:
                continue
        
        if not channel_id:
            print(f"[ERROR] Channel #{channel} not found or bot not added to it")
            return None
        
        # Get messages
        response = client.conversations_history(channel=channel_id, limit=count)
        messages = response["messages"]
        
        print(f"\n[MESSAGES] Last {count} messages in #{channel}:")
        print("-" * 80)
        
        for msg in messages:
            # Get user info
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
        # Handle channel name
        if channel.startswith("#"):
            channel = channel[1:]
        
        # Find channel by name
        channels_response = client.conversations_list(types="public_channel,private_channel")
        channel_id = None
        for ch in channels_response["channels"]:
            if ch["name"] == channel:
                channel_id = ch["id"]
                break
        
        if not channel_id:
            print(f"[ERROR] Channel #{channel} not found")
            return None
        
        response = client.chat_postMessage(channel=channel_id, text=message)
        print(f"[OK] Message sent to #{channel}")
        return response
    except SlackApiError as e:
        print(f"[ERROR] {e.response['error']}")
        return None


def send_dm(client: WebClient, user_email: str, message: str):
    """Send a direct message to a user by email"""
    try:
        # Find user by email
        response = client.users_lookupByEmail(email=user_email)
        user_id = response["user"]["id"]
        user_name = response["user"]["real_name"]
        
        # Open DM channel
        dm_response = client.conversations_open(users=[user_id])
        dm_channel = dm_response["channel"]["id"]
        
        # Send message
        client.chat_postMessage(channel=dm_channel, text=message)
        print(f"[OK] DM sent to {user_name} ({user_email})")
        return True
    except SlackApiError as e:
        print(f"[ERROR] {e.response['error']}")
        return None


def test_connection(client: WebClient):
    """Test the connection"""
    try:
        response = client.auth_test()
        print(f"\n[OK] Connected to Slack!")
        print(f"    Workspace: {response['team']}")
        print(f"    Bot User: {response['user']}")
        return response
    except SlackApiError as e:
        print(f"[ERROR] {e.response['error']}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Manage Slack Workspace")
    parser.add_argument("command", choices=["users", "channels", "messages", "send", "dm", "test"],
                       help="Command to execute")
    parser.add_argument("--channel", "-c", help="Channel name (e.g., general)")
    parser.add_argument("--count", "-n", type=int, default=10, help="Number of items")
    parser.add_argument("--message", "-m", help="Message to send")
    parser.add_argument("--email", "-e", help="User email for DM")
    parser.add_argument("--include-bots", action="store_true", help="Include bots in user list")
    parser.add_argument("--include-private", action="store_true", help="Include private channels")
    
    args = parser.parse_args()
    
    client = get_client()
    
    if args.command == "test":
        test_connection(client)
    elif args.command == "users":
        list_users(client, args.include_bots)
    elif args.command == "channels":
        list_channels(client, args.include_private)
    elif args.command == "messages":
        if not args.channel:
            print("Error: --channel is required for messages command")
            sys.exit(1)
        list_messages(client, args.channel, args.count)
    elif args.command == "send":
        if not args.channel or not args.message:
            print("Error: --channel and --message are required for send command")
            sys.exit(1)
        send_message(client, args.channel, args.message)
    elif args.command == "dm":
        if not args.email or not args.message:
            print("Error: --email and --message are required for dm command")
            sys.exit(1)
        send_dm(client, args.email, args.message)


if __name__ == "__main__":
    main()
