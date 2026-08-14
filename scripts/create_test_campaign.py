"""
Create a test "Master of Informatics" campaign and send it to all leads with emails.
Since RESEND_API_KEY may be unset, emails are logged (status='logged') which still
populates the Email Records traffic table.

Usage: python scripts/create_test_campaign.py
"""
import sys, os, asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.stdout.reconfigure(encoding='utf-8')

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import AsyncSessionLocal
from app.models.campaign import Campaign
from app.models.lead import Lead
from app.services.email_service import send_email

CAMPAIGN_NAME = "Master of Informatics — Info Session"
CAMPAIGN_SUBJECT = "Master of Informatics at President University — By Coursework & By Research"

CAMPAIGN_BODY = """<html>
<body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
  <h2 style="color: #1d4ed8;">Welcome to the Master of Informatics Program</h2>
  <p>Dear {{name}},</p>
  <p>We are pleased to introduce the <strong>Master of Informatics (S2 Informatika)</strong> at
  <strong>President University</strong> — designed for professionals who want to advance their
  careers in the computing and information technology field.</p>

  <p>Our program offers <strong>two flexible pathways</strong>:</p>
  <ul>
    <li><strong>By Coursework</strong> — complete advanced coursework in areas such as machine
    learning, data science, cybersecurity, and software engineering, culminating in a capstone project.</li>
    <li><strong>By Research</strong> — work closely with our research supervisors to produce a
    thesis that contributes new knowledge to the field of informatics.</li>
  </ul>

  <p>Both pathways are built around our 10 core subjects, including Machine Learning,
  Big Data Analysis, Deep Learning, NLP & Conversational AI, and more.</p>

  <p><strong>Why join us?</strong></p>
  <ul>
    <li>Taught by experienced academics and industry practitioners</li>
    <li>Flexible schedule designed for working professionals</li>
    <li>Strong industry network and research opportunities</li>
  </ul>

  <p>We would love to tell you more. Reply to this email or contact our admissions team to
  schedule a chat.</p>

  <p>Best regards,<br/>
  <strong>Admissions Team</strong><br/>
  Master of Informatics Program<br/>
  President University</p>
</body>
</html>
"""


async def main():
    async with AsyncSessionLocal() as db:
        # 0) Remove any previous instance of this campaign to keep it idempotent
        existing = (await db.execute(
            select(Campaign).where(Campaign.name == CAMPAIGN_NAME)
        )).scalars().all()
        from sqlalchemy import text
        for old in existing:
            await db.execute(text("DELETE FROM email_logs WHERE campaign_id = :cid"), {"cid": old.id})
            await db.delete(old)
            print(f"🗑️  Removed previous campaign: {old.name}")
        await db.commit()

        # 1) Create the campaign
        campaign = Campaign(
            name=CAMPAIGN_NAME,
            description="Introductory email for the Master of Informatics program with two pathways: By Coursework and By Research.",
            target_type="all",
            email_template={
                "subject": CAMPAIGN_SUBJECT,
                "body": CAMPAIGN_BODY,
                "variables": ["name"],
            },
            follow_up={
                "enabled": False,
                "delay_days": 7,
                "max_follow_ups": 1,
                "template": {"subject": "Follow-up: Master of Informatics", "body": ""},
            },
            status="active",
        )
        db.add(campaign)
        await db.commit()
        await db.refresh(campaign)
        print(f"✅ Created campaign: {campaign.name} (id={campaign.id})")

        # Campaign is created as a draft. No emails are sent automatically —
        # use the 'Send to All' button in the Email page to send when ready.
        print(f"\n✅ Done — created campaign: {campaign.name}")
        print("Status: draft (no emails sent).")
        print("Use the 'Send to All' button in the Email page to send to all registered emails.")


if __name__ == "__main__":
    asyncio.run(main())
