"""
Email Management Script using Microsoft Graph API
Uses Himalaya App with Delegated Permissions (Interactive Login)
"""
import os
import sys
import asyncio
import argparse
from datetime import datetime
from dotenv import load_dotenv
from msgraph import GraphServiceClient
from auth import get_credential

# Load environment variables
load_dotenv()

USER_EMAIL = os.getenv("USER_EMAIL", "me")


async def list_folders(client: GraphServiceClient):
    """List all mail folders"""
    folders = await client.me.mail_folders.get()
    
    print("\n[FOLDERS] Mail Folders:")
    print("-" * 60)
    print(f"{'Folder':<30} {'Unread':>10} {'Total':>10}")
    print("-" * 60)
    
    for folder in folders.value:
        print(f"{folder.display_name:<30} {folder.unread_item_count:>10} {folder.total_item_count:>10}")
        
        # Get child folders
        if folder.child_folder_count > 0:
            try:
                child_folders = await client.me.mail_folders.by_mail_folder_id(folder.id).child_folders.get()
                for child in child_folders.value:
                    print(f"  > {child.display_name:<26} {child.unread_item_count:>10} {child.total_item_count:>10}")
            except:
                pass
    
    return folders


async def list_emails(client: GraphServiceClient, count: int = 10, folder: str = "inbox"):
    """List recent emails from a folder"""
    from msgraph.generated.users.item.mail_folders.item.messages.messages_request_builder import MessagesRequestBuilder
    
    query = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
        top=count,
        orderby=["receivedDateTime desc"]
    )
    config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
        query_parameters=query
    )
    
    messages = await client.me.mail_folders.by_mail_folder_id(folder).messages.get(request_configuration=config)
    
    print(f"\n[INBOX] Last {count} emails in {folder}:")
    print("-" * 80)
    
    for i, msg in enumerate(messages.value, 1):
        received = msg.received_date_time.strftime("%Y-%m-%d %H:%M") if msg.received_date_time else "N/A"
        sender = msg.from_.email_address.name if msg.from_ and msg.from_.email_address else "Unknown"
        subject = msg.subject[:50] if msg.subject else "(No subject)"
        read_status = "[READ]" if msg.is_read else "[NEW]"
        
        print(f"{i:>2}. {read_status} {received} | {sender[:20]:<20} | {subject}")
    
    return messages


async def read_email(client: GraphServiceClient, message_id: str):
    """Read a specific email by ID"""
    message = await client.me.messages.by_message_id(message_id).get()
    
    print("\n" + "=" * 80)
    print(f"From: {message.from_.email_address.name} <{message.from_.email_address.address}>")
    print(f"To: {', '.join([r.email_address.address for r in message.to_recipients])}")
    print(f"Subject: {message.subject}")
    print(f"Date: {message.received_date_time}")
    print("=" * 80)
    print(message.body.content if message.body else "(No body)")
    print("=" * 80)
    
    return message


async def send_email(client: GraphServiceClient, to: str, subject: str, body: str, html: bool = False):
    """Send an email"""
    from msgraph.generated.users.item.send_mail.send_mail_post_request_body import SendMailPostRequestBody
    from msgraph.generated.models.message import Message
    from msgraph.generated.models.item_body import ItemBody
    from msgraph.generated.models.body_type import BodyType
    from msgraph.generated.models.recipient import Recipient
    from msgraph.generated.models.email_address import EmailAddress
    
    message = Message(
        subject=subject,
        body=ItemBody(
            content_type=BodyType.Html if html else BodyType.Text,
            content=body
        ),
        to_recipients=[
            Recipient(email_address=EmailAddress(address=to))
        ]
    )
    
    request_body = SendMailPostRequestBody(message=message, save_to_sent_items=True)
    
    await client.me.send_mail.post(request_body)
    print(f"[OK] Email sent successfully to {to}")


async def get_me(client: GraphServiceClient):
    """Get current user info"""
    me = await client.me.get()
    print(f"\n[USER] Logged in as: {me.display_name} ({me.mail})")
    return me


async def main():
    parser = argparse.ArgumentParser(description="Manage Microsoft 365 Email")
    parser.add_argument("command", choices=["folders", "list", "read", "send", "me"],
                       help="Command to execute")
    parser.add_argument("--count", "-n", type=int, default=10, help="Number of emails to list")
    parser.add_argument("--folder", "-f", default="inbox", help="Folder to list emails from")
    parser.add_argument("--id", help="Message ID for read command")
    parser.add_argument("--to", help="Recipient email for send command")
    parser.add_argument("--subject", "-s", help="Email subject for send command")
    parser.add_argument("--body", "-b", help="Email body for send command")
    parser.add_argument("--html", action="store_true", help="Send as HTML email")
    
    args = parser.parse_args()
    
    # Get authenticated credential
    credential = get_credential()
    
    # Create Graph client
    client = GraphServiceClient(credentials=credential, scopes=[
        "User.Read",
        "Mail.Read",
        "Mail.Send",
        "Mail.ReadWrite"
    ])
    
    # Execute command
    if args.command == "folders":
        await list_folders(client)
    elif args.command == "list":
        await list_emails(client, args.count, args.folder)
    elif args.command == "read":
        if not args.id:
            print("Error: --id is required for read command")
            sys.exit(1)
        await read_email(client, args.id)
    elif args.command == "send":
        if not all([args.to, args.subject, args.body]):
            print("Error: --to, --subject, and --body are required for send command")
            sys.exit(1)
        await send_email(client, args.to, args.subject, args.body, args.html)
    elif args.command == "me":
        await get_me(client)


if __name__ == "__main__":
    asyncio.run(main())
