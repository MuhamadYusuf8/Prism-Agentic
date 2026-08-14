"""
Send a tracked test email to the monitoring mailbox (default mit@president.ac.id).

The email includes an open-tracking pixel + link tracking, so once it is opened
the Email Monitoring module will show it as "opened" (and "clicked" if a link
is followed).

Usage:
    python scripts/send_test_to_mit.py [recipient] [subject]
"""
import sys, os, asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.stdout.reconfigure(encoding='utf-8')

from app.core.database import AsyncSessionLocal
from app.services.email_service import send_email

DEFAULT_RECIPIENT = "mit@president.ac.id"

BODY = """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #1a365d;">PRISM Email Monitoring — Test</h2>
    <p>Hello,</p>
    <p>This is a <strong>tracked test email</strong> from the PRISM recruitment platform.</p>
    <p>Opening this email fires the tracking pixel. Following
       <a href="https://president.ac.id/programs">this link</a> logs a click.</p>
    <p>You should now see this email appear under
       <strong>Email → Email Monitoring → Conversations</strong> with status <em>Opened</em>.</p>
    <p>Best regards,<br/>Admissions Office<br/>President University</p>
</body>
</html>
"""


async def main():
    to_email = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RECIPIENT
    subject = sys.argv[2] if len(sys.argv) > 2 else "PRISM Tracking Test — mit@president.ac.id"

    print(f"Sending tracked test email to: {to_email}")
    print(f"Subject: {subject}\n")

    async with AsyncSessionLocal() as db:
        result = await send_email(
            to_email=to_email,
            to_name="MIT Mailbox",
            subject=subject,
            body=BODY,
            db=db,
        )
        print("Result:", result)
        if result.get("success"):
            print("\n✅ Email logged/sent — check the Email Monitoring page (status updates on open).")
            if result.get("email_log_id"):
                print(f"   Email log ID: {result['email_log_id']}")
        else:
            print("\n⚠️  Send failed. Common cause: the sender domain (mit@president.ac.id) is")
            print("   not verified in Resend, or no SMTP is configured. The failed send is still")
            print("   tracked in Email Monitoring.")


if __name__ == "__main__":
    asyncio.run(main())
