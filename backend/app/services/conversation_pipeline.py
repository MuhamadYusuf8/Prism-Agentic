"""
9-Stage Conversation Pipeline — ports from auto-reply-email-bot replyGenerator.js.

Tracks the full student recruitment journey from initial inquiry to LoA issuance.
Each stage has specific reply templates and follow-up messages.

Stages:
  1. INITIAL_INQUIRY  →  INFO_REQUESTED
  2. INFO_REQUESTED   →  INFO_RECEIVED
  3. INFO_RECEIVED    →  APPLICATION_SUBMITTED
  4. APPLICATION_SUBMITTED → DOCUMENTS_REVIEWED
  5. DOCUMENTS_REVIEWED → INTERVIEW_SCHEDULED
  6. INTERVIEW_SCHEDULED → INTERVIEW_COMPLETED
  7. INTERVIEW_COMPLETED → OFFER_MADE
  8. OFFER_MADE       →  LOA_ISSUED
  9. LOA_ISSUED       →  FOLLOW_UP (until enrolled)
"""

import re
from typing import Any

from app.models.lead import Lead, LeadStatus


# ── Stage Definitions ──────────────────────────────────────────────────────────

STAGES = {
    "INITIAL_INQUIRY": {
        "name": "Initial Inquiry",
        "order": 1,
        "next": "INFO_REQUESTED",
        "status": LeadStatus.NEW.value,
    },
    "INFO_REQUESTED": {
        "name": "Information Requested",
        "order": 2,
        "next": "INFO_RECEIVED",
        "status": LeadStatus.CONTACTED.value,
    },
    "INFO_RECEIVED": {
        "name": "Information Received",
        "order": 3,
        "next": "APPLICATION_SUBMITTED",
        "status": LeadStatus.INTERESTED.value,
    },
    "APPLICATION_SUBMITTED": {
        "name": "Application Submitted",
        "order": 4,
        "next": "DOCUMENTS_REVIEWED",
        "status": LeadStatus.APPLIED.value,
    },
    "DOCUMENTS_REVIEWED": {
        "name": "Documents Reviewed",
        "order": 5,
        "next": "INTERVIEW_SCHEDULED",
        "status": LeadStatus.APPLIED.value,
    },
    "INTERVIEW_SCHEDULED": {
        "name": "Interview Scheduled",
        "order": 6,
        "next": "INTERVIEW_COMPLETED",
        "status": LeadStatus.APPLIED.value,
    },
    "INTERVIEW_COMPLETED": {
        "name": "Interview Completed",
        "order": 7,
        "next": "OFFER_MADE",
        "status": LeadStatus.APPLIED.value,
    },
    "OFFER_MADE": {
        "name": "Offer Made",
        "order": 8,
        "next": "LOA_ISSUED",
        "status": LeadStatus.INTERESTED.value,
    },
    "LOA_ISSUED": {
        "name": "LoA Issued",
        "order": 9,
        "next": "FOLLOW_UP",
        "status": LeadStatus.ENROLLED.value,
    },
    "FOLLOW_UP": {
        "name": "Follow-up",
        "order": 10,
        "next": None,
        "status": LeadStatus.ENROLLED.value,
    },
}

# Map application statuses to stages
APPLICATION_STATUSES = {
    "inquiry": "INITIAL_INQUIRY",
    "info_requested": "INFO_REQUESTED",
    "info_received": "INFO_RECEIVED",
    "applied": "APPLICATION_SUBMITTED",
    "documents_reviewed": "DOCUMENTS_REVIEWED",
    "interview_scheduled": "INTERVIEW_SCHEDULED",
    "interview_completed": "INTERVIEW_COMPLETED",
    "offer": "OFFER_MADE",
    "loa": "LOA_ISSUED",
    "follow_up": "FOLLOW_UP",
}


# ── Intent Analysis ────────────────────────────────────────────────────────────

INTENT_PATTERNS = {
    "application": [
        r"\b(apply|application|applying|enroll|register|sign.?up)\b",
        r"\b(how do I apply|how to apply|application process)\b",
        r"\bi want to (study|join|apply)\b",
    ],
    "information": [
        r"\b(info|information|details|brochure|prospectus|catalog)\b",
        r"\b(tell me more|what are|how much|tuition|fee|cost|scholarship)\b",
        r"\b(requirement|prerequisite|qualification|criteria)\b",
        r"\b(program|course|major|degree|curriculum)\b",
        r"\b(deadline|intake|semester|academic year)\b",
    ],
    "document": [
        r"\b(document|transcript|diploma|certificate|transcript|id card|passport)\b",
        r"\b(submit|upload|send|attach)\b.*\b(document|file|form)\b",
    ],
    "interview": [
        r"\binterview\b",
        r"\b(schedule|book|arrange)\b.*\b(interview|meeting|call)\b",
    ],
    "follow_up": [
        r"\b(follow.?up|update|status|progress|how long)\b",
        r"\b(any news|any update|waiting|pending)\b",
    ],
    "interested": [
        r"\b(interested|keen|eager|excited|looking forward)\b",
        r"\b(yes|sure|absolutely|definitely)\b",
        r"\b(thank|thanks|great|awesome)\b",
    ],
    "not_interested": [
        r"\b(not interested|no thank|no thanks|decline|declined)\b",
        r"\b(not now|maybe later|not at this time)\b",
        r"\b(already|enrolled|accepted|committed)\b.*\b(other|another|different)\b",
    ],
    "unsubscribe": [
        r"\b(unsubscribe|opt.?out|remove|stop|quit)\b",
        r"\b(do not|don't|stop).*\b(email|contact|message)\b",
    ],
    "out_of_office": [
        r"\b(out of office|ooo|vacation|holiday|away|leave)\b",
        r"\b(back on|return on|will be back)\b",
    ],
}


def analyze_intent(text: str, subject: str | None = None) -> dict:
    """
    Analyze email content to determine intent.
    Returns intent type, confidence, and matched patterns.
    """
    combined = f"{subject or ''} {text}".lower()
    results = {}

    for intent, patterns in INTENT_PATTERNS.items():
        matches = []
        for pattern in patterns:
            found = re.findall(pattern, combined, re.IGNORECASE)
            matches.extend(found)
        if matches:
            results[intent] = len(matches)

    if not results:
        return {"intent": "unknown", "confidence": 0.0, "matched_patterns": []}

    # Find the intent with the most matches
    best_intent = max(results, key=results.get)
    total_matches = sum(results.values())
    confidence = min(results[best_intent] / max(total_matches, 1), 1.0)

    return {
        "intent": best_intent,
        "confidence": round(confidence, 2),
        "matched_patterns": list(results.keys()),
    }


# ── Stage Progression ──────────────────────────────────────────────────────────


def determine_next_stage(current_stage: str, intent: str) -> str:
    """
    Determine the next stage based on current stage and email intent.
    """
    stage_info = STAGES.get(current_stage)
    if not stage_info:
        return "INITIAL_INQUIRY"

    # Map intents to stage transitions
    intent_to_stage = {
        "application": "APPLICATION_SUBMITTED",
        "document": "DOCUMENTS_REVIEWED",
        "interview": "INTERVIEW_SCHEDULED",
        "interested": stage_info.get("next", current_stage),
        "not_interested": current_stage,  # Stay on same stage
        "unsubscribe": current_stage,  # Will be handled separately
        "follow_up": current_stage,  # Stay on same stage
    }

    return intent_to_stage.get(intent, stage_info.get("next", current_stage))


# ── Reply Templates ────────────────────────────────────────────────────────────


def get_initial_reply(name: str, analysis: dict) -> dict:
    """Generate initial reply for new inquiries."""
    return {
        "subject": "Thank You for Your Interest in President University",
        "body": f"""<p>Dear {name},</p>
<p>Thank you for reaching out to President University! We are delighted to hear about your interest in our programs.</p>
<p>To help us provide you with the most relevant information, could you please share:</p>
<ul>
<li>Your educational background (current/last degree and institution)</li>
<li>The program you are interested in</li>
<li>Any specific questions you may have</li>
</ul>
<p>We look forward to assisting you on your educational journey.</p>
<p>Best regards,<br/>Admissions Office<br/>President University</p>""",
        "stage": "INFO_REQUESTED",
    }


def get_application_reply(name: str) -> dict:
    """Generate reply when prospect wants to apply."""
    return {
        "subject": "Application Process — President University",
        "body": f"""<p>Dear {name},</p>
<p>Thank you for your interest in applying to President University! We are excited to guide you through the application process.</p>
<p>Please find below the steps to apply:</p>
<ol>
<li>Complete the online application form at our admissions portal</li>
<li>Prepare the required documents (transcripts, diploma, ID, passport photo)</li>
<li>Submit your application before the deadline</li>
<li>Wait for the document review confirmation</li>
</ol>
<p>Would you like us to send you a detailed checklist of required documents?</p>
<p>Best regards,<br/>Admissions Office<br/>President University</p>""",
        "stage": "APPLICATION_SUBMITTED",
    }


def get_document_request_reply(name: str) -> dict:
    """Generate reply when documents are requested."""
    return {
        "subject": "Required Documents for Application — President University",
        "body": f"""<p>Dear {name},</p>
<p>Thank you for moving forward with your application! Below is the complete list of documents you need to prepare:</p>
<ul>
<li>Academic transcripts (certified true copy)</li>
<li>Diploma or certificate of graduation</li>
<li>Valid ID / Passport</li>
<li>Passport-sized photograph</li>
<li>Statement of purpose</li>
<li>Recommendation letters (if applicable)</li>
</ul>
<p>Please submit these documents through our online portal or email them to admissions@president.ac.id.</p>
<p>Best regards,<br/>Admissions Office<br/>President University</p>""",
        "stage": "DOCUMENTS_REVIEWED",
    }


def get_interview_reply(name: str) -> dict:
    """Generate reply for interview scheduling."""
    return {
        "subject": "Interview Schedule — President University",
        "body": f"""<p>Dear {name},</p>
<p>Congratulations on progressing to the interview stage! We are impressed with your application and would like to get to know you better.</p>
<p>Please let us know your preferred date and time for a brief interview (approximately 30 minutes). We offer the following slots:</p>
<ul>
<li>Weekdays: 9:00 AM - 4:00 PM (WIB)</li>
<li>Virtual via Zoom or Google Meet</li>
</ul>
<p>Please confirm your availability and we will send you the meeting link.</p>
<p>Best regards,<br/>Admissions Office<br/>President University</p>""",
        "stage": "INTERVIEW_SCHEDULED",
    }


def get_offer_reply(name: str) -> dict:
    """Generate reply when an offer is made."""
    return {
        "subject": "Offer of Admission — President University",
        "body": f"""<p>Dear {name},</p>
<p>Congratulations! We are pleased to inform you that you have been offered admission to President University.</p>
<p>Your offer details:</p>
<ul>
<li>Program: As per your application</li>
<li>Intake: Upcoming semester</li>
</ul>
<p>To accept this offer, please:</p>
<ol>
<li>Review the offer letter attached</li>
<li>Sign and return the acceptance form</li>
<li>Pay the registration fee by the specified deadline</li>
</ol>
<p>We look forward to welcoming you to President University!</p>
<p>Best regards,<br/>Admissions Office<br/>President University</p>""",
        "stage": "OFFER_MADE",
    }


def get_loa_issued_reply(name: str) -> dict:
    """Generate reply when LoA is issued."""
    return {
        "subject": "Letter of Acceptance (LoA) — President University",
        "body": f"""<p>Dear {name},</p>
<p>We are delighted to inform you that your Letter of Acceptance (LoA) has been issued!</p>
<p>Your LoA is attached to this email. Please find the next steps below:</p>
<ol>
<li>Review your LoA carefully</li>
<li>Complete the enrollment process</li>
<li>Prepare for the academic year</li>
<li>Contact our student services for visa assistance (if applicable)</li>
</ol>
<p>Welcome to President University! We are excited to have you join our academic community.</p>
<p>Best regards,<br/>Admissions Office<br/>President University</p>""",
        "stage": "LOA_ISSUED",
    }


def get_follow_up_reply(name: str, follow_up_count: int = 1) -> dict:
    """Generate follow-up message based on count (escalating)."""
    follow_up_messages = [
        {
            "subject": "Following Up — President University Application",
            "body": f"""<p>Dear {name},</p>
<p>We hope this message finds you well. We wanted to follow up on your application to President University.</p>
<p>If you have any questions or need assistance, please don't hesitate to reach out. We are here to help!</p>
<p>Best regards,<br/>Admissions Office<br/>President University</p>""",
        },
        {
            "subject": "Reminder — Complete Your Application",
            "body": f"""<p>Dear {name},</p>
<p>This is a friendly reminder to complete your application to President University. Our admissions team is ready to assist you with any questions.</p>
<p>Don't miss this opportunity to join our vibrant academic community!</p>
<p>Best regards,<br/>Admissions Office<br/>President University</p>""",
        },
        {
            "subject": "Last Call — Application Deadline Approaching",
            "body": f"""<p>Dear {name},</p>
<p>We noticed that your application is still pending. The deadline for the upcoming intake is approaching soon.</p>
<p>Please complete your application as soon as possible to secure your place. Contact us if you need any assistance.</p>
<p>Best regards,<br/>Admissions Office<br/>President University</p>""",
        },
        {
            "subject": "We're Still Here to Help — President University",
            "body": f"""<p>Dear {name},</p>
<p>We understand that applying to university is a big decision. Our admissions counselors are available to answer any questions you may have.</p>
<p>Would you like to schedule a call with one of our representatives?</p>
<p>Best regards,<br/>Admissions Office<br/>President University</p>""",
        },
        {
            "subject": "Final Follow-Up — President University",
            "body": f"""<p>Dear {name},</p>
<p>This is our final follow-up regarding your application to President University. We would love to have you join us, but we understand if you have decided to pursue other options.</p>
<p>Please let us know if you are still interested or if you have any final questions.</p>
<p>Best regards,<br/>Admissions Office<br/>President University</p>""",
        },
    ]

    idx = min(follow_up_count - 1, len(follow_up_messages) - 1)
    return {
        **follow_up_messages[idx],
        "stage": "FOLLOW_UP",
        "follow_up_number": follow_up_count,
    }


def get_default_reply(name: str) -> dict:
    """Default reply when intent cannot be determined."""
    return {
        "subject": "Thank You for Contacting President University",
        "body": f"""<p>Dear {name},</p>
<p>Thank you for contacting President University Admissions Office.</p>
<p>We have received your message and will get back to you as soon as possible. If you have an urgent inquiry, please call our admissions hotline.</p>
<p>Best regards,<br/>Admissions Office<br/>President University</p>""",
        "stage": None,
    }


# ── Main Reply Generator ───────────────────────────────────────────────────────


def generate_reply(
    lead: Lead,
    current_stage: str | None = None,
    message_text: str = "",
    message_subject: str | None = None,
    follow_up_count: int = 0,
) -> dict:
    """
    Generate an appropriate reply based on the lead's current stage and message intent.
    """
    name = lead.name or "Prospective Student"
    analysis = analyze_intent(message_text, message_subject)
    intent = analysis["intent"]

    # Handle unsubscribe intent
    if intent == "unsubscribe":
        return {
            "subject": "Unsubscribe Confirmation",
            "body": f"""<p>Dear {name},</p>
<p>You have been unsubscribed from our mailing list. You will no longer receive emails from President University Admissions Office.</p>
<p>If you change your mind, you can resubscribe at any time by contacting us at admissions@president.ac.id.</p>
<p>Best regards,<br/>Admissions Office<br/>President University</p>""",
            "stage": None,
            "unsubscribe": True,
        }

    # Handle out of office
    if intent == "out_of_office":
        return {
            "subject": "Auto-Reply: Out of Office",
            "body": f"""<p>Thank you for your message.</p>
<p>We have noted that you are currently out of office. We will follow up with you upon your return.</p>
<p>Best regards,<br/>Admissions Office<br/>President University</p>""",
            "stage": current_stage,
            "out_of_office": True,
        }

    # Handle not interested
    if intent == "not_interested":
        return {
            "subject": "Thank You for Your Response",
            "body": f"""<p>Dear {name},</p>
<p>Thank you for letting us know. We respect your decision and wish you all the best in your future endeavors.</p>
<p>If you ever change your mind or have any questions in the future, please don't hesitate to reach out.</p>
<p>Best regards,<br/>Admissions Office<br/>President University</p>""",
            "stage": current_stage,
            "not_interested": True,
        }

    # Determine current stage
    stage = current_stage or "INITIAL_INQUIRY"

    # If follow-up, generate follow-up reply
    if follow_up_count > 0:
        return get_follow_up_reply(name, follow_up_count)

    # Generate reply based on stage and intent
    if stage == "INITIAL_INQUIRY" or stage is None:
        return get_initial_reply(name, analysis)

    if intent == "application":
        return get_application_reply(name)

    if intent == "document":
        return get_document_request_reply(name)

    if intent == "interview":
        return get_interview_reply(name)

    if intent == "information":
        # Stay in current stage, provide info
        return {
            "subject": "Information About Our Programs — President University",
            "body": f"""<p>Dear {name},</p>
<p>Thank you for your interest in learning more about President University's programs.</p>
<p>We offer a wide range of undergraduate and graduate programs designed to prepare you for a successful career. Our programs include Computer Science, Information Technology, Business Administration, and many more.</p>
<p>Would you like to schedule a consultation with one of our admissions counselors to discuss which program best fits your goals?</p>
<p>Best regards,<br/>Admissions Office<br/>President University</p>""",
            "stage": stage,
        }

    # Default: move to next stage if available
    stage_info = STAGES.get(stage)
    if stage_info and stage_info.get("next"):
        next_stage = stage_info["next"]
        if next_stage == "LOA_ISSUED":
            return get_loa_issued_reply(name)
        elif next_stage == "OFFER_MADE":
            return get_offer_reply(name)
        elif next_stage == "INTERVIEW_SCHEDULED":
            return get_interview_reply(name)

    return get_default_reply(name)


def get_follow_up_messages() -> list[dict]:
    """Get all follow-up message templates."""
    return [
        get_follow_up_reply("{{name}}", i + 1)
        for i in range(5)
    ]
