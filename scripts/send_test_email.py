"""
Send the Master of Informatics campaign email to a specific test address.
Usage: python scripts/send_test_email.py <email> [name]
"""
import sys, os, asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.stdout.reconfigure(encoding='utf-8')

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.campaign import Campaign
from app.services.email_service import send_email


async def main():
    to_email = sys.argv[1] if len(sys.argv) > 1 else "fasik3310@gmail.com"
    to_name = sys.argv[2] if len(sys.argv) > 2 else "Test Recipient"

    async with AsyncSessionLocal() as db:
        campaign = (await db.execute(
            select(Campaign).where(Campaign.name.ilike("%Master of Informatics%"))
        )).scalars().first()

        if not campaign:
            print("No Master of Informatics campaign found. Run create_test_campaign.py first.")
            return

        template = campaign.email_template or {}
        subject = template.get("subject", campaign.name)
        body = template.get("body", "").replace("{{name}}", to_name)

        print(f"Sending to: {to_email}")
        print(f"Subject: {subject}")

        result = await send_email(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            body=body,
            campaign_id=campaign.id,
            db=db,
        )

        print(f"\nResult: {result}")
        if result.get("success"):
            print("✅ Email sent/logged successfully — check your inbox or the Email Records tab.")


if __name__ == "__main__":
    asyncio.run(main())
