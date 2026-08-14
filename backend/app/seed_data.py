"""
Comprehensive seed script — generates dummy data for Master candidate pipeline only.

This script populates:
  - 60 leads with full profiling data (scores, tags, matched programs, education, experience)
  - 6 email campaigns with templates, follow-up configs, and stats
  - 2 clusters (master CS, master business)
  - 200+ email logs with open/click/reply tracking
  - 40+ replies with intent classification and auto-responses
  - Settings defaults

Usage:
    cd backend && python -m app.seed_data

Requires a running PostgreSQL database with tables created.
"""

import asyncio
import os
import uuid
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func

from app.core.database import AsyncSessionLocal, engine, Base
import bcrypt as _bcrypt
from app.models.lead import Lead, LeadStatus, LeadSource
from app.models.campaign import Campaign
from app.models.email_log import EmailLog
from app.models.reply import Reply
from app.models.cluster import Cluster
from app.models.user import User

# ── Helpers ──────────────────────────────────────────────────────────────────────

random.seed(42)


def utcnow():
    return datetime.now(timezone.utc)


def days_ago(n):
    return utcnow() - timedelta(days=n)


def rand_date(start_days: int, end_days: int):
    """Return a random datetime between start_days and end_days ago."""
    lo = min(start_days, end_days)
    hi = max(start_days, end_days)
    return utcnow() - timedelta(days=random.randint(lo, hi))


def pick(arr):
    return random.choice(arr)


def pick_n(arr, n):
    return random.sample(arr, min(n, len(arr)))


def rand_float(lo, hi, decimals=1):
    return round(random.uniform(lo, hi), decimals)


# ── Static Data ──────────────────────────────────────────────────────────────────

FIRST_NAMES = [
    "Ahmad", "Budi", "Citra", "Dewi", "Eko", "Fitri", "Gilang", "Hana",
    "Irfan", "Joko", "Kartika", "Lukman", "Maya", "Nanda", "Oscar",
    "Putri", "Qori", "Rizky", "Sari", "Teguh", "Umar", "Vina",
    "Wahyu", "Xaverius", "Yuni", "Zainal", "Agus", "Bambang", "Cahyo",
    "Dian", "Edi", "Fajar", "Gita", "Hendra", "Indah", "Jati",
    "Kurnia", "Lestari", "Mulyadi", "Novi", "Oki", "Pramono",
]

LAST_NAMES = [
    "Pratama", "Wijaya", "Kusuma", "Santoso", "Saputra", "Hidayat",
    "Nugroho", "Wibowo", "Siregar", "Nasution", "Suryadi", "Setiawan",
    "Hartono", "Gunawan", "Susanto", "Liem", "Tan", "Widodo",
    "Rahardjo", "Purnomo", "Utomo", "Handayani", "Mulyani", "Anggraini",
]

INSTITUTIONS = [
    ("Universitas Indonesia", "UI"),
    ("Institut Teknologi Bandung", "ITB"),
    ("Universitas Gadjah Mada", "UGM"),
    ("Institut Teknologi Sepuluh Nopember", "ITS"),
    ("Universitas Brawijaya", "UB"),
    ("Universitas Padjadjaran", "Unpad"),
    ("Universitas Diponegoro", "Undip"),
    ("Universitas Airlangga", "Unair"),
    ("Universitas Telkom", "Tel-U"),
    ("BINUS University", "BINUS"),
    ("President University", "PresUniv"),
    ("Universitas Pelita Harapan", "UPH"),
    ("Universitas Kristen Petra", "UKP"),
    ("Universitas Atma Jaya", "UAJ"),
    ("Universitas Gunadarma", "Gunadarma"),
]

MAJORS = [
    "Informatics Engineering",
    "Computer Science",
    "Information Systems",
    "Data Science",
    "Software Engineering",
    "Electrical Engineering",
    "Mechanical Engineering",
    "Civil Engineering",
    "Industrial Engineering",
    "Business Management",
    "Accounting",
    "Marketing",
    "International Relations",
    "Communication Science",
    "Visual Communication Design",
    "Architecture",
    "Law",
    "Psychology",
    "Economics",
    "Mathematics",
]

DEGREE_LEVELS = ["master"]

SKILLS_POOL = [
    "Python", "JavaScript", "TypeScript", "Java", "C++", "Go", "Rust",
    "React", "Node.js", "Django", "Flask", "FastAPI", "Spring Boot",
    "PostgreSQL", "MongoDB", "Redis", "Docker", "Kubernetes",
    "AWS", "GCP", "Azure", "Machine Learning", "Deep Learning",
    "NLP", "Computer Vision", "Data Analysis", "SQL", "NoSQL",
    "Git", "Linux", "Agile", "Scrum", "REST API", "GraphQL",
    "TensorFlow", "PyTorch", "Pandas", "NumPy", "Tableau",
    "Public Speaking", "Leadership", "Project Management",
    "Digital Marketing", "SEO", "Content Writing", "Social Media",
    "UI/UX Design", "Figma", "Adobe XD", "Photoshop", "Illustrator",
    "AutoCAD", "SolidWorks", "MATLAB", "R", "SPSS", "STATA",
]

PROGRAMS = [
    "S2 Ilmu Komputer (Master of Computer Science)",
    "S2 Manajemen (Master of Management)",
    "S2 Teknik Industri (Master of Industrial Engineering)",
    "MBA Eksekutif (Executive MBA)",
]

COMPANIES = [
    "Gojek", "Tokopedia", "Shopee", "Traveloka", "Bukalapak",
    "Google", "Microsoft", "Amazon", "Meta", "Apple",
    "Bank Mandiri", "BCA", "BNI", "BRI", "Telkom Indonesia",
    "Pertamina", "PLN", "Unilever Indonesia", "Indofood", "Astra",
    "Samsung", "IBM", "Oracle", "Cisco", "Deloitte",
    "McKinsey & Company", "Boston Consulting Group", "Accenture",
]

JOB_TITLES = [
    "Software Engineer", "Data Scientist", "Product Manager",
    "Business Analyst", "UI/UX Designer", "DevOps Engineer",
    "Frontend Developer", "Backend Developer", "Full Stack Developer",
    "Machine Learning Engineer", "Data Analyst", "System Analyst",
    "IT Consultant", "Network Engineer", "Security Analyst",
    "Marketing Manager", "Financial Analyst", "Accountant",
    "Civil Engineer", "Mechanical Engineer", "Electrical Engineer",
]

HEADLINES = [
    "Software Engineer at {company}",
    "Data Scientist | AI Enthusiast",
    "Recent Graduate in {major}",
    "Full Stack Developer with {years}+ years experience",
    "Master's Student in {major}",
    "Tech Enthusiast & Lifelong Learner",
    "Aspiring Data Scientist",
    "Business Professional | MBA Candidate",
    "Creative Designer | Visual Communication",
    "Engineering Student | Passionate about Innovation",
]

LOCATIONS = [
    "Jakarta", "Bandung", "Surabaya", "Yogyakarta", "Semarang",
    "Medan", "Makassar", "Denpasar", "Palembang", "Malang",
    "Bekasi", "Tangerang", "Depok", "Bogor", "Batam",
]

SOURCES = ["linkedin_serper", "linkedin_puppeteer", "csv_import", "cikarang", "manual"]

STATUSES = ["new", "scraped", "profiled", "clustered", "contacted",
            "interested", "not_interested", "applied", "enrolled", "unsubscribed"]

INTENTS = ["interested", "not_interested", "request_info", "unsubscribe", "out_of_office", "neutral"]
SENTIMENTS = ["positive", "negative", "neutral"]


# ── Generate Leads ───────────────────────────────────────────────────────────────

def generate_lead(index: int) -> dict:
    first = pick(FIRST_NAMES)
    last = pick(LAST_NAMES)
    name = f"{first} {last}"
    email = f"{first.lower()}.{last.lower()}{random.randint(1, 99)}@example.com"
    inst_name, inst_abbr = pick(INSTITUTIONS)
    major = pick(MAJORS)
    degree = pick(DEGREE_LEVELS)
    company = pick(COMPANIES)
    job = pick(JOB_TITLES)
    years_exp = random.randint(0, 15)
    location = pick(LOCATIONS)
    source = pick(SOURCES)
    status = pick(STATUSES)
    is_cs = major in ["Informatics Engineering", "Computer Science", "Information Systems",
                       "Data Science", "Software Engineering", "Mathematics"]
    profile_score = rand_float(20, 98) if is_cs else rand_float(10, 70)
    priority = random.randint(1, 100)
    data_quality = pick(["high", "medium", "low"])

    # Education entries — all leads have a bachelor background + master degree
    edu_entries = [
        {
            "institution": inst_name,
            "degree": "Bachelor",
            "field": major,
            "start_year": 2016 - random.randint(0, 2),
            "end_year": 2020 - random.randint(0, 2),
            "gpa": rand_float(2.8, 4.0, 2),
        },
        {
            "institution": pick(INSTITUTIONS)[0],
            "degree": "Master",
            "field": major,
            "start_year": 2021 - random.randint(0, 1),
            "end_year": 2023 - random.randint(0, 1),
            "gpa": rand_float(3.0, 4.0, 2),
        },
    ]

    # Experience entries
    exp_entries = []
    num_exp = random.randint(0, 3)
    for i in range(num_exp):
        exp_entries.append({
            "title": pick(JOB_TITLES),
            "company": pick(COMPANIES),
            "start_date": f"{2020 - i}-0{random.randint(1, 6):02d}",
            "end_date": f"{2023 - i}-{random.randint(7, 12):02d}" if i > 0 else "Present",
            "description": f"Worked on various projects involving {pick(SKILLS_POOL)} and {pick(SKILLS_POOL)}.",
            "duration_years": rand_float(0.5, 4, 1),
        })

    # Skills
    num_skills = random.randint(3, 10)
    skills = pick_n(SKILLS_POOL, num_skills)

    # Matched programs
    num_programs = random.randint(1, 3)
    matched = []
    for _ in range(num_programs):
        prog = pick(PROGRAMS)
        matched.append({
            "name": prog,
            "confidence": rand_float(50, 99, 1),
            "type": degree,
        })

    # Tags
    tags = []
    if is_cs:
        tags.append("tech")
    if profile_score > 70:
        tags.append("high-potential")
    tags.append("postgraduate")
    if source == "linkedin_serper":
        tags.append("sourced")
    if status == "interested":
        tags.append("warm-lead")
    if data_quality == "high":
        tags.append("complete-profile")
    tags.extend(pick_n(["active-job-seeker", "career-changer", "international", "scholarship-seeking",
                         "entrepreneur", "research-oriented", "industry-experienced"], random.randint(0, 2)))

    # Communication history
    comm = {
        "emails_sent": [],
        "interested": status == "interested",
        "interested_at": str(days_ago(random.randint(5, 30))) if status == "interested" else None,
        "last_contacted_at": str(days_ago(random.randint(1, 14))) if status in ["contacted", "interested", "applied"] else None,
    }

    created = rand_date(60, 1)

    return {
        "name": name,
        "email": email,
        "phone": f"+62{random.randint(811, 899)}-{random.randint(1000, 9999)}-{random.randint(100, 999)}",
        "linkedin_url": f"https://linkedin.com/in/{first.lower()}.{last.lower()}{random.randint(1, 99)}",
        "headline": pick(HEADLINES).format(company=company, major=major, years=years_exp),
        "summary": f"Experienced professional with background in {major}. "
                   f"Skilled in {', '.join(skills[:3])}. "
                   f"Looking for opportunities in {pick(['tech', 'business', 'education', 'research'])}.",
        "company": company if random.random() > 0.3 else None,
        "job_title": job if random.random() > 0.3 else None,
        "industry": pick(["Technology", "Education", "Finance", "Manufacturing", "Consulting", "Healthcare"]),
        "location": location,
        "skills": skills,
        "education": edu_entries,
        "experience": exp_entries,
        "source": source,
        "status": status,
        "is_active": True,
        "profile_score": profile_score,
        "profile_type": degree,
        "priority_score": priority,
        "is_computer_science_related": is_cs,
        "matched_programs": matched,
        "recommended_program": matched[0]["name"] if matched else None,
        "tags": tags,
        "data_quality": data_quality,
        "communication": comm,
        "notes": f"Auto-generated seed lead #{index + 1}. {pick(['Follow up for enrollment.', 'Good candidate for CS program.', 'Consider for scholarship.', 'Schedule campus visit.', 'Send program brochure.'])}",
        "created_at": created,
        "updated_at": created,
        "profiled_at": created + timedelta(hours=random.randint(1, 24)) if status not in ["new", "scraped"] else None,
        "last_contacted_at": days_ago(random.randint(1, 14)) if status in ["contacted", "interested", "applied", "enrolled"] else None,
    }


# ── Generate Campaigns ───────────────────────────────────────────────────────────

def generate_campaign(index: int) -> dict:
    names = [
        "S2 Ilmu Komputer - Beasiswa Parsial",
        "MBA Eksekutif - Early Bird",
        "S2 Manajemen - January Intake",
        "S2 Teknik Industri - Open Day Follow Up",
        "MBA Eksekutif - Campus Visit",
        "S2 Ilmu Komputer - Webinar Series",
    ]
    descriptions = [
        "Reaching out to IT graduates for master's scholarship opportunities.",
        "Promoting the upcoming MBA program with early bird pricing.",
        "Targeting business enthusiasts for the January intake.",
        "Follow-up campaign for industrial engineering open day attendees.",
        "Inviting prospective MBA students to campus visit days.",
        "Webinar series on advanced computing.",
    ]
    target_types = ["master", "master", "master", "master", "master", "master"]
    statuses = ["active", "active", "paused", "draft", "active", "completed"]

    name = names[index]
    desc = descriptions[index]
    ttype = target_types[index]
    status = statuses[index]

    template = {
        "subject": pick([
            f"Join {name} at President University",
            f"Your future starts here: {name}",
            f"Special invitation: {name}",
            f"Discover {name} - Apply Now",
            f"Exclusive opportunity: {name}",
        ]),
        "body": f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #1a365d; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1 style="margin: 0;">President University</h1>
        <p style="margin: 5px 0 0; opacity: 0.9;">{name}</p>
    </div>
    <div style="padding: 20px; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 8px 8px;">
        <p>Dear {{name}},</p>
        <p>We are excited to invite you to learn more about <strong>{name}</strong> at President University.</p>
        <p>Our program offers world-class education with experienced faculty members and industry partnerships that prepare you for a successful career.</p>
        <p style="text-align: center; margin: 25px 0;">
            <a href="{{tracking_url}}" style="background: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                Learn More & Apply
            </a>
        </p>
        <p>Key highlights:</p>
        <ul>
            <li>Accredited program with international standards</li>
            <li>Industry partnerships with leading companies</li>
            <li>Scholarship opportunities available</li>
            <li>Modern campus facilities</li>
        </ul>
        <p>If you have any questions, please don't hesitate to reply to this email.</p>
        <p>Best regards,<br>Admissions Team<br>President University</p>
    </div>
    <div style="text-align: center; padding: 15px; color: #718096; font-size: 12px;">
        <p>President University | Jababeka Education Park | Cikarang, Indonesia</p>
        <p><a href="{{unsubscribe_url}}" style="color: #718096;">Unsubscribe</a></p>
    </div>
</body>
</html>""",
        "variables": ["name", "tracking_url", "unsubscribe_url"],
    }

    follow_up = {
        "enabled": random.random() > 0.3,
        "delay_days": random.choice([3, 5, 7]),
        "max_follow_ups": random.randint(1, 3),
        "template": {
            "subject": f"Follow-up: {name}",
            "body": f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="padding: 20px;">
        <p>Dear {{name}},</p>
        <p>We wanted to follow up on our previous email about <strong>{name}</strong> at President University.</p>
        <p>Have you had a chance to review the program details? We'd be happy to answer any questions you may have.</p>
        <p style="text-align: center; margin: 25px 0;">
            <a href="{{tracking_url}}" style="background: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                Schedule a Call
            </a>
        </p>
        <p>Best regards,<br>Admissions Team<br>President University</p>
    </div>
</body>
</html>""",
        },
    }

    schedule = {
        "start_date": str(days_ago(random.randint(10, 30))),
        "end_date": str(days_ago(random.randint(-30, -5))),
        "timezone": "Asia/Jakarta",
        "send_window": {"start": "08:00", "end": "17:00"},
    }

    # Stats based on status
    total_targeted = random.randint(30, 150)
    sent = total_targeted if status != "draft" else 0
    opened = int(sent * rand_float(0.3, 0.7, 2)) if sent > 0 else 0
    clicked = int(opened * rand_float(0.2, 0.5, 2)) if opened > 0 else 0
    replied = int(opened * rand_float(0.05, 0.2, 2)) if opened > 0 else 0
    interested = int(replied * rand_float(0.3, 0.7, 2)) if replied > 0 else 0

    stats = {
        "total_targeted": total_targeted,
        "emails_sent": sent,
        "emails_opened": opened,
        "emails_clicked": clicked,
        "replies_received": replied,
        "interested": interested,
        "unsubscribed": random.randint(0, 5),
        "bounced": random.randint(0, 3),
    }

    created = days_ago(random.randint(15, 45))
    launched = created + timedelta(days=random.randint(1, 5)) if status != "draft" else None
    completed = launched + timedelta(days=random.randint(14, 30)) if status == "completed" else None

    return {
        "name": name,
        "description": desc,
        "target_type": ttype,
        "target_clusters": [],
        "email_template": template,
        "follow_up": follow_up,
        "schedule": schedule,
        "stats": stats,
        "status": status,
        "created_at": created,
        "updated_at": created,
        "launched_at": launched,
        "completed_at": completed,
    }


# ── Generate Clusters ────────────────────────────────────────────────────────────

def generate_clusters() -> list[dict]:
    return [
        {
            "name": "Master CS & Engineering",
            "description": "High-potential master candidates in computer science and engineering fields.",
            "type": "master",
            "characteristics": {
                "average_score": 85.0,
                "common_skills": ["Python", "Machine Learning", "Data Analysis", "SQL", "Research"],
                "common_interests": ["Software Development", "AI/ML", "Data Science", "Research"],
                "common_education_fields": ["Computer Science", "Informatics Engineering", "Data Science", "Information Systems"],
                "average_experience": 3.2,
                "top_locations": [{"name": "Jakarta", "count": 14}, {"name": "Bandung", "count": 9}, {"name": "Surabaya", "count": 6}],
            },
            "member_count": 30,
            "is_active": True,
            "created_at": days_ago(20),
            "updated_at": days_ago(20),
        },
        {
            "name": "Master Business & Management",
            "description": "Master candidates interested in business and management programs.",
            "type": "master",
            "characteristics": {
                "average_score": 72.0,
                "common_skills": ["Leadership", "Public Speaking", "Project Management", "Marketing", "Excel"],
                "common_interests": ["Entrepreneurship", "Business Strategy", "Marketing"],
                "common_education_fields": ["Business Management", "Accounting", "Marketing", "Economics"],
                "average_experience": 4.1,
                "top_locations": [{"name": "Jakarta", "count": 11}, {"name": "Tangerang", "count": 5}, {"name": "Surabaya", "count": 4}],
            },
            "member_count": 24,
            "is_active": True,
            "created_at": days_ago(15),
            "updated_at": days_ago(15),
        },
    ]


# ── Generate Email Logs ──────────────────────────────────────────────────────────

def generate_email_logs(leads: list, campaigns: list) -> list[dict]:
    logs = []
    log_id = 0

    for campaign in campaigns:
        if campaign["status"] == "draft":
            continue

        # Pick a subset of leads for this campaign
        target_leads = pick_n(leads, min(campaign["stats"]["emails_sent"], len(leads)))
        sent_count = len(target_leads)

        for i, lead in enumerate(target_leads):
            log_id += 1
            sent_at = campaign["launched_at"] or days_ago(10)
            sent_at = sent_at + timedelta(hours=random.randint(0, 48))

            # Some emails get opened
            opened = random.random() < 0.55
            opened_at = sent_at + timedelta(hours=random.randint(1, 72)) if opened else None

            # Some opened emails get clicked
            clicked = opened and random.random() < 0.4
            clicked_at = (opened_at + timedelta(hours=random.randint(1, 24))) if clicked else None

            # Some emails get replies
            replied = opened and random.random() < 0.15
            replied_at = (opened_at + timedelta(hours=random.randint(2, 120))) if replied else None

            status = "sent"
            if replied:
                status = "replied"
            elif random.random() < 0.02:
                status = "bounced"
            elif random.random() < 0.01:
                status = "failed"

            logs.append({
                "campaign_id": campaign.get("_id"),
                "lead_id": lead.get("_id"),
                "recipient_email": lead["email"],
                "recipient_name": lead["name"],
                "subject": campaign["email_template"]["subject"].replace("{{name}}", lead["name"]),
                "body": campaign["email_template"]["body"],
                "tracking_id": f"trk_{uuid.uuid4().hex[:12]}",
                "status": status,
                "opened_at": opened_at,
                "opened_count": 1 if opened else 0,
                "clicked_at": clicked_at,
                "clicked_count": 1 if clicked else 0,
                "replied_at": replied_at,
                "is_follow_up": False,
                "follow_up_number": 0,
                "extra_data": {
                    "campaign_name": campaign["name"],
                    "lead_name": lead["name"],
                    "source": "seed",
                },
                "sent_at": sent_at,
                "created_at": sent_at,
            })

    return logs


# ── Generate Replies ─────────────────────────────────────────────────────────────

def generate_replies(email_logs: list) -> list[dict]:
    replies = []
    reply_templates = {
        "interested": [
            "I'm very interested in this program! Can you send me more details about the application process?",
            "Thank you for reaching out. I would like to apply for this program. What are the next steps?",
            "This looks like a great opportunity. I'm definitely interested in enrolling.",
            "I've been looking for a program like this. Please send me the application link.",
        ],
        "request_info": [
            "Could you provide more information about the tuition fees and scholarship options?",
            "What are the entry requirements for international students?",
            "Can you tell me more about the curriculum and faculty?",
            "Is there an option to study part-time while working?",
            "What is the duration of the program and when does it start?",
        ],
        "not_interested": [
            "Thank you, but I'm not interested at this time.",
            "I've already enrolled in another program. Please remove me from your mailing list.",
            "Not interested, thanks.",
            "I appreciate the offer, but I've decided to pursue a different path.",
        ],
        "unsubscribe": [
            "Please unsubscribe me from your emails.",
            "Stop sending me emails. I'm not interested.",
            "Unsubscribe",
        ],
        "out_of_office": [
            "I am currently out of the office and will have limited access to email. I will respond to your message when I return.",
            "Thank you for your email. I am on leave until next week and will reply to your message upon my return.",
        ],
    }

    for log in email_logs:
        if log["status"] != "replied" or not log["replied_at"]:
            continue

        intent = pick(INTENTS)
        sentiment = "positive" if intent == "interested" else "negative" if intent in ["not_interested", "unsubscribe"] else "neutral"
        template = pick(reply_templates.get(intent, reply_templates["request_info"]))

        replies.append({
            "email_log_id": log.get("_id"),
            "lead_id": log["lead_id"],
            "campaign_id": log["campaign_id"],
            "from_email": log["recipient_email"],
            "subject": f"Re: {log['subject']}",
            "body": f"<p>{template}</p>",
            "body_text": template,
            "intent": intent,
            "confidence": rand_float(0.7, 0.99, 2),
            "sentiment": sentiment,
            "auto_response_sent": intent in ["interested", "request_info"],
            "auto_response_at": log["replied_at"] + timedelta(minutes=random.randint(5, 60)) if intent in ["interested", "request_info"] else None,
            "auto_response_body": f"Thank you for your {'interest' if intent == 'interested' else 'message'}! Our admissions team will get back to you shortly." if intent in ["interested", "request_info"] else None,
            "raw_data": {"headers": {"message_id": f"<{uuid.uuid4().hex}@example.com>"}},
            "received_at": log["replied_at"],
            "created_at": log["replied_at"],
        })

    return replies


# ── Main Seed Function ───────────────────────────────────────────────────────────

async def seed():
    print("=" * 60)
    print("  PRISM — Seed Data Generator")
    print("=" * 60)

    # Create tables if they don't exist
    print("\n📦 Ensuring tables exist...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("   ✅ Tables ready.")

    async with AsyncSessionLocal() as db:
        # ── Seed Admin User (always runs, before skip check) ──────────────────────
        print("\n🔐 Ensuring admin user...")
        existing_user = await db.scalar(select(User).where(User.email == "admin@president.ac.id"))
        if not existing_user:
            admin_user = User(
                name="Admin PRISM",
                email="admin@president.ac.id",
                password_hash=_bcrypt.hashpw(b"admin123", _bcrypt.gensalt(rounds=12)).decode(),
                role="admin",
                is_active=True,
            )
            db.add(admin_user)
            await db.flush()
            print("   ✅ Admin user created (admin@president.ac.id / admin123).")
        else:
            print("   ✅ Admin user already exists.")

        # Check if data already exists
        existing = await db.scalar(select(func.count(Lead.id)))
        if existing and existing > 0:
            print(f"\n⚠️  Database already has {existing} leads. Skipping seed.")
            print("   Run with FORCE_SEED=1 to re-seed.")
            force = os.environ.get("FORCE_SEED")
            if not force:
                await db.commit()
                return

        # ── Seed Leads ────────────────────────────────────────────────────────────
        print("\n👤 Generating leads...")
        lead_dicts = [generate_lead(i) for i in range(60)]
        leads = []
        for ld in lead_dicts:
            lead = Lead(**ld)
            db.add(lead)
            leads.append(ld)
            ld["_id"] = lead.id
        await db.flush()
        print(f"   ✅ {len(leads)} leads created.")

        # ── Seed Clusters ─────────────────────────────────────────────────────────
        print("\n🔷 Generating clusters...")
        cluster_dicts = generate_clusters()
        clusters = []
        for cd in cluster_dicts:
            cluster = Cluster(**cd)
            db.add(cluster)
            clusters.append(cd)
            cd["_id"] = cluster.id
        await db.flush()
        print(f"   ✅ {len(clusters)} clusters created.")

        # Assign some leads to clusters
        for i, lead_dict in enumerate(leads):
            if i < 30:
                lead_dict["cluster_id"] = clusters[0]["_id"]
            else:
                lead_dict["cluster_id"] = clusters[1]["_id"]
        for ld in lead_dicts:
            if ld.get("cluster_id"):
                lead = await db.get(Lead, ld["_id"])
                if lead:
                    lead.cluster_id = ld["cluster_id"]
        await db.flush()

        # ── Seed Campaigns ────────────────────────────────────────────────────────
        print("\n📧 Generating campaigns...")
        campaign_dicts = [generate_campaign(i) for i in range(6)]
        campaigns = []
        for cd in campaign_dicts:
            campaign = Campaign(**cd)
            db.add(campaign)
            campaigns.append(cd)
            cd["_id"] = campaign.id
        await db.flush()
        print(f"   ✅ {len(campaigns)} campaigns created.")

        # ── Seed Email Logs ───────────────────────────────────────────────────────
        print("\n📨 Generating email logs...")
        email_log_dicts = generate_email_logs(leads, campaigns)
        email_logs = []
        for eld in email_log_dicts:
            el = EmailLog(**eld)
            db.add(el)
            email_logs.append(eld)
            eld["_id"] = el.id
        await db.flush()
        print(f"   ✅ {len(email_logs)} email logs created.")

        # ── Seed Replies ──────────────────────────────────────────────────────────
        print("\n💬 Generating replies...")
        reply_dicts = generate_replies(email_logs)
        for rd in reply_dicts:
            reply = Reply(**rd)
            db.add(reply)
        await db.flush()
        print(f"   ✅ {len(reply_dicts)} replies created.")

        # ── Commit ────────────────────────────────────────────────────────────────
        await db.commit()
        print("\n" + "=" * 60)
        print("  🎉 Seed complete!")
        print("=" * 60)
        print(f"\n  📊 Summary:")
        print(f"     Leads:      {len(leads)}")
        print(f"     Campaigns:  {len(campaigns)}")
        print(f"     Clusters:   {len(clusters)}")
        print(f"     Email Logs: {len(email_logs)}")
        print(f"     Replies:    {len(reply_dicts)}")
        print()


if __name__ == "__main__":
    import os
    asyncio.run(seed())