"""
Test connection to Microsoft Graph API using Himalaya App
"""
import asyncio
from dotenv import load_dotenv
from msgraph import GraphServiceClient
from auth import get_credential

# Load environment variables
load_dotenv()


async def test_connection():
    """Test the M365 connection"""
    print("Testing Microsoft Graph API connection...")
    print("-" * 50)
    
    # Get authenticated credential
    credential = get_credential()
    
    # Create Graph client
    client = GraphServiceClient(credentials=credential, scopes=[
        "User.Read",
        "Mail.Read",
        "Mail.Send"
    ])
    
    # Test 1: Get current user
    print("\n1. Testing user profile access...")
    try:
        me = await client.me.get()
        print(f"   ✅ Logged in as: {me.display_name} ({me.mail})")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 2: List mail folders
    print("\n2. Testing mail folder access...")
    try:
        folders = await client.me.mail_folders.get()
        print(f"   ✅ Found {len(folders.value)} mail folders")
        for folder in folders.value[:5]:
            print(f"      - {folder.display_name}: {folder.unread_item_count} unread")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 3: List recent emails
    print("\n3. Testing email access...")
    try:
        messages = await client.me.mail_folders.by_mail_folder_id("inbox").messages.get(
            query_params={"$top": 5, "$orderby": "receivedDateTime desc"}
        )
        print(f"   ✅ Found {len(messages.value)} recent emails")
        for msg in messages.value[:3]:
            sender = msg.from_.email_address.name if msg.from_ and msg.from_.email_address else "Unknown"
            subject = msg.subject[:40] if msg.subject else "(No subject)"
            print(f"      - {sender[:15]}: {subject}...")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ All tests passed! Connection is working.")
    print("=" * 50)
    return True


if __name__ == "__main__":
    asyncio.run(test_connection())
