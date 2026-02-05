"""
Simple test to verify M365 connection
"""
import os
import asyncio
from dotenv import load_dotenv
from msgraph import GraphServiceClient
from auth import get_credential

load_dotenv()

async def main():
    print("Getting credential...")
    credential = get_credential()
    
    print("Creating Graph client...")
    client = GraphServiceClient(credentials=credential, scopes=[
        "User.Read",
        "Mail.Read"
    ])
    
    print("Fetching user profile...")
    try:
        me = await client.me.get()
        print(f"[OK] Logged in as: {me.display_name} ({me.mail})")
    except Exception as e:
        print(f"[ERROR] Error getting profile: {e}")
        return
    
    print("\nFetching inbox messages...")
    try:
        from msgraph.generated.users.item.mail_folders.item.messages.messages_request_builder import MessagesRequestBuilder
        query = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
            top=5,
            orderby=["receivedDateTime desc"]
        )
        config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
            query_parameters=query
        )
        messages = await client.me.mail_folders.by_mail_folder_id("inbox").messages.get(request_configuration=config)
        print(f"[OK] Found {len(messages.value)} recent emails:")
        for msg in messages.value:
            sender = msg.from_.email_address.name if msg.from_ and msg.from_.email_address else "Unknown"
            subject = msg.subject[:50] if msg.subject else "(No subject)"
            print(f"   - {sender}: {subject}")
    except Exception as e:
        print(f"[ERROR] Error getting emails: {e}")

if __name__ == "__main__":
    asyncio.run(main())
