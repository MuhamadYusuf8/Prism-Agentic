"""
Reply Monitor & Auto-Responder — ports from student-recruitment-automation_duplicateZ.

Monitors IMAP inbox for replies, classifies intent, and sends auto-responses.
Combines replyMonitor.js (IMAP polling + classification) and autoResponder.js
(response templates + sending).
"""

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.lead import Lead, LeadStatus
from app.models.email_log import EmailLog
from app.models.reply import Reply
from app.services.conversation_pipeline import generate_reply, analyze_intent


# ── Sentiment Analysis ─────────────────────────────────────────────────────────

POSITIVE_WORDS = [
    "great", "excellent", "amazing", "wonderful", "fantastic", "good", "best",
    "love", "perfect", "beautiful", "awesome", "outstanding", "superb",
    "brilliant", "terrific", "marvelous", "splendid", "magnificent",
    "thank", "thanks", "grateful", "appreciate", "pleased", "happy",
    "excited", "interested", "keen", "eager", "looking forward",
    "yes", "sure", "absolutely", "definitely", "certainly",
]

NEGATIVE_WORDS = [
    "bad", "terrible", "awful", "horrible", "poor", "worst", "hate",
    "disappointed", "frustrated", "angry", "annoyed", "upset",
    "not interested", "no thank", "decline", "reject", "unsubscribe",
    "stop", "leave me alone", "do not contact", "spam",
]

NEUTRAL_WORDS = [
    "ok", "okay", "fine", "alright", "maybe", "perhaps", "possibly",
    "consider", "think", "will see", "let me know", "get back",
    "later", "sometime", "eventually",
]


def classify_sentiment(text: str) -> str:
    """Classify sentiment of reply text as positive/negative/neutral."""
    text_lower = text.lower()

    positive_count = sum(1 for word in POSITIVE_WORDS if word in text_lower)
    negative_count = sum(1 for word in NEGATIVE_WORDS if word in text_lower)
    neutral_count = sum(1 for word in NEUTRAL_WORDS if word in text_lower)

    if positive_count > negative_count and positive_count > neutral_count:
        return "positive"
    elif negative_count > positive_count and negative_count > neutral_count:
        return "negative"
    else:
        return "neutral"


# ── Intent Classification ──────────────────────────────────────────────────────

INTENT_KEYWORDS = {
    "interested": [
        "interested", "keen", "eager", "excited", "looking forward",
        "yes", "sure", "absolutely", "definitely", "count me in",
        "i want to", "i would like", "please send", "sign me up",
    ],
    "not_interested": [
        "not interested", "no thank", "no thanks", "decline", "rejected",
        "not for me", "not now", "maybe later", "not at this time",
    ],
    "request_info": [
        "tell me more", "more information", "details please", "brochure",
        "what about", "how much", "tuition", "fee", "cost", "scholarship",
        "requirement", "prerequisite", "deadline", "intake",
    ],
    "unsubscribe": [
        "unsubscribe", "opt out", "opt-out", "remove me", "stop email",
        "do not email", "don't email", "leave me alone", "spam",
        "remove from list", "take me off",
    ],
    "out_of_office": [
        "out of office", "ooo", "vacation", "holiday", "away",
        "on leave", "will be back", "return on",
    ],
}


def classify_intent(text: str, subject: str | None = None) -> dict:
    """
    Classify reply intent using keyword matching.
    Returns intent, confidence, and matched keywords.
    """
    combined = f"{subject or ''} {text}".lower()
    results = {}

    for intent, keywords in INTENT_KEYWORDS.items():
        matches = [kw for kw in keywords if kw in combined]
        if matches:
            results[intent] = len(matches)

    if not results:
        return {"intent": "other", "confidence": 0.0, "matched_keywords": []}

    best_intent = max(results, key=results.get)
    total_matches = sum(results.values())
    confidence = min(results[best_intent] / max(total_matches, 1), 1.0)

    return {
        "intent": best_intent,
        "confidence": round(confidence, 2),
        "matched_keywords": list(results.keys()),
    }


# ── Auto-Response Templates ────────────────────────────────────────────────────

AUTO_RESPONSE_TEMPLATES = {
    "interested": {
        "subject": "Great to Hear! Next Steps — President University",
        "body": """<p>Dear {{name}},</p>
<p>We are delighted to hear about your interest! Let us guide you through the next steps.</p>
<p>Here's what to do next:</p>
<ol>
<li>Complete the online application form</li>
<li>Prepare your documents (transcripts, diploma, ID)</li>
<li>Submit your application</li>
</ol>
<p>Would you like us to send you a detailed application checklist?</p>
<p>Best regards,<br/>Admissions Office<br/>President University</p>""",
    },
    "request_info": {
        "subject": "Information You Requested — President University",
        "body": """<p>Dear {{name}},</p>
<p>Thank you for your interest in learning more about President University.</p>
<p>We offer a wide range of programs including:</p>
<ul>
<li>Bachelor of Computer Science</li>
<li>Bachelor of Information Technology</li>
<li>Bachelor of Business Administration</li>
<li>Master of Computer Science</li>
<li>Master of Data Science</li>
</ul>
<p>For detailed information about tuition fees, scholarships, and admission requirements, please visit our website or contact our admissions team.</p>
<p>Best regards,<br/>Admissions Office<br/>President University</p>""",
    },
    "not_interested": {
        "subject": "Thank You for Your Response",
        "body": """<p>Dear {{name}},</p>
<p>Thank you for letting us know. We respect your decision and wish you all the best in your future endeavors.</p>
<p>If you ever change your mind or have any questions in the future, please don't hesitate to reach out.</p>
<p>Best regards,<br/>Admissions Office<br/>President University</p>""",
    },
    "unsubscribe": {
        "subject": "Unsubscribe Confirmation",
        "body": """<p>Dear {{name}},</p>
<p>You have been unsubscribed from our mailing list. You will no longer receive emails from President University Admissions Office.</p>
<p>If you change your mind, you can resubscribe at any time by contacting us at admissions@president.ac.id.</p>
<p>Best regards,<br/>Admissions Office<br/>President University</p>""",
    },
    "out_of_office": {
        "subject": "Auto-Reply: Out of Office",
        "body": """<p>Thank you for your message.</p>
<p>We have noted that you are currently out of office. We will follow up with you upon your return.</p>
<p>Best regards,<br/>Admissions Office<br/>President University</p>""",
    },
    "default": {
        "subject": "Thank You for Your Message — President University",
        "body": """<p>Dear {{name}},</p>
<p>Thank you for your message. We have received it and will get back to you as soon as possible.</p>
<p>If you have an urgent inquiry, please call our admissions hotline.</p>
<p>Best regards,<br/>Admissions Office<br/>President University</p>""",
    },
}


def personalize_template(template: str, name: str) -> str:
    """Replace {{name}} placeholder in template."""
    return template.replace("{{name}}", name or "Prospective Student")


# ── Reply Processing ───────────────────────────────────────────────────────────


async def process_reply(
    from_email: str,
    subject: str | None,
    body: str,
    body_text: str | None,
    db: AsyncSession,
) -> dict:
    """
    Process an incoming reply: classify intent, find associated lead,
    create reply record, and optionally send auto-response.
    """
    # Find the lead by email
    result = await db.execute(
        select(Lead).where(Lead.email == from_email)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        return {"success": False, "error": "No matching lead found"}

    # Find the most recent email log for this lead
    email_log_result = await db.execute(
        select(EmailLog)
        .where(EmailLog.lead_id == lead.id)
        .order_by(EmailLog.sent_at.desc().nulls_last())
        .limit(1)
    )
    email_log = email_log_result.scalar_one_or_none()

    # Classify intent
    intent_result = classify_intent(body, subject)
    sentiment = classify_sentiment(body)

    # Create reply record
    reply = Reply(
        email_log_id=email_log.id if email_log else None,
        lead_id=lead.id,
        campaign_id=email_log.campaign_id if email_log else None,
        from_email=from_email,
        subject=subject,
        body=body,
        body_text=body_text,
        intent=intent_result["intent"],
        confidence=intent_result["confidence"],
        sentiment=sentiment,
    )
    db.add(reply)

    # Update lead communication tracking
    if lead.communication is None:
        lead.communication = {}

    # Update the specific email log's replied status
    if email_log:
        email_log.replied_at = datetime.now(timezone.utc)

    # Update lead status based on intent
    if intent_result["intent"] == "interested":
        lead.status = LeadStatus.INTERESTED.value
        if lead.communication:
            lead.communication["interested"] = True
            lead.communication["interested_at"] = datetime.now(timezone.utc).isoformat()
    elif intent_result["intent"] == "not_interested":
        lead.status = LeadStatus.NOT_INTERESTED.value
    elif intent_result["intent"] == "unsubscribe":
        lead.status = LeadStatus.UNSUBSCRIBED.value
        lead.is_active = False

    lead.last_contacted_at = datetime.now(timezone.utc)

    # Generate and send auto-response
    auto_response_sent = False
    auto_response_body = None

    if intent_result["intent"] not in ("out_of_office",):
        template = AUTO_RESPONSE_TEMPLATES.get(
            intent_result["intent"], AUTO_RESPONSE_TEMPLATES["default"]
        )
        auto_response_body = personalize_template(template["body"], lead.name or "")

        # Send auto-response via Resend if configured
        if settings.RESEND_API_KEY:
            try:
                import resend
                resend.api_key = settings.RESEND_API_KEY

                params = {
                    "from": settings.EMAIL_FROM,
                    "to": [from_email],
                    "subject": template["subject"],
                    "html": auto_response_body,
                }

                resend.Emails.send(params)
                auto_response_sent = True
            except Exception:
                pass

    # Update reply with auto-response info
    reply.auto_response_sent = auto_response_sent
    reply.auto_response_at = datetime.now(timezone.utc) if auto_response_sent else None
    reply.auto_response_body = auto_response_body

    await db.commit()

    return {
        "success": True,
        "reply_id": str(reply.id),
        "lead_id": str(lead.id),
        "intent": intent_result["intent"],
        "confidence": intent_result["confidence"],
        "sentiment": sentiment,
        "auto_response_sent": auto_response_sent,
    }


async def get_reply_stats(db: AsyncSession) -> dict:
    """Get aggregate reply statistics."""
    from sqlalchemy import func

    total = await db.scalar(select(func.count(Reply.id)))
    by_intent = await db.execute(
        select(Reply.intent, func.count(Reply.id))
        .group_by(Reply.intent)
    )
    auto_responded = await db.scalar(
        select(func.count(Reply.id)).where(Reply.auto_response_sent == True)
    )

    return {
        "total_replies": total or 0,
        "by_intent": {row[0]: row[1] for row in by_intent},
        "auto_responded": auto_responded or 0,
    }
