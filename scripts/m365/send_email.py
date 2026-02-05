"""
Send Email Script using Microsoft Graph API
"""
import asyncio
import argparse
from dotenv import load_dotenv
from msgraph import GraphServiceClient
from msgraph.generated.users.item.send_mail.send_mail_post_request_body import SendMailPostRequestBody
from msgraph.generated.models.message import Message
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.recipient import Recipient
from msgraph.generated.models.email_address import EmailAddress
from auth import get_credential

# Load environment variables
load_dotenv()


async def send_email(to: str, subject: str, body: str, html: bool = False):
    """Send an email"""
    # Get authenticated credential
    credential = get_credential()
    
    # Create Graph client
    client = GraphServiceClient(credentials=credential, scopes=[
        "User.Read",
        "Mail.Send"
    ])
    
    # Create message
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
    
    # Send
    await client.me.send_mail.post(request_body)
    print(f"[OK] Email sent successfully!")
    print(f"   To: {to}")
    print(f"   Subject: {subject}")


async def main():
    parser = argparse.ArgumentParser(description="Send email via Microsoft Graph API")
    parser.add_argument("--to", "-t", required=True, help="Recipient email address")
    parser.add_argument("--subject", "-s", required=True, help="Email subject")
    parser.add_argument("--body", "-b", required=True, help="Email body")
    parser.add_argument("--html", action="store_true", help="Send as HTML email")
    
    args = parser.parse_args()
    
    await send_email(args.to, args.subject, args.body, args.html)


if __name__ == "__main__":
    asyncio.run(main())
