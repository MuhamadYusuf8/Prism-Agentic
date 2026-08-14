"""
Profiling Engine — ports CS relevance scoring from student-intake-agent-2
and weighted scoring from student-recruitment-automation_duplicateZ.

Combines both approaches:
- intake-agent-2: keyword-based CS relevance (0-100), education analysis,
  interest extraction, program matching
- recruit-Z: weighted scoring (academic 35%, engagement 20%, program fit 30%,
  data completeness 15%), tag generation, data quality assessment
"""

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead, LeadStatus, ProfileType, DataQuality


# ── CS Relevance Keywords (from intake-agent-2) ────────────────────────────────

CS_KEYWORDS = [
    "computer science", "software engineering", "computer engineering",
    "information technology", "information systems", "data science",
    "data analytics", "machine learning", "artificial intelligence",
    "deep learning", "cybersecurity", "network security", "cloud computing",
    "devops", "web development", "mobile development", "full stack",
    "frontend", "backend", "database", "sql", "python", "java",
    "javascript", "typescript", "react", "node.js", "docker",
    "kubernetes", "aws", "azure", "gcp", "algorithm", "data structure",
    "programming", "coding", "software developer", "software engineer",
    "it support", "system analyst", "network engineer",
]


MASTER_KEYWORDS = [
    "master", "graduate", "s2", "magister", "m.sc", "master's degree",
    "master degree", "postgraduate", "post graduate",
]

INTEREST_PATTERNS = [
    (r"\bai\b|\bartificial intelligence\b", "Artificial Intelligence"),
    (r"\bmachine learning\b|\bdeep learning\b", "Machine Learning / Deep Learning"),
    (r"\bdata science\b|\bdata analytics\b|\bbig data\b", "Data Science / Analytics"),
    (r"\bweb\b.*\bdev\b|\bfrontend\b|\bbackend\b|\bfull.?stack\b", "Web Development"),
    (r"\bmobile\b.*\bdev\b|\bandroid\b|\bios\b|\bflutter\b|\breact native\b", "Mobile Development"),
    (r"\bcyber\b|\bsecurity\b|\bsecurity\b", "Cybersecurity"),
    (r"\bcloud\b|\baws\b|\bazure\b|\bgcp\b", "Cloud Computing"),
    (r"\bdevops\b|\bci/cd\b|\bdocker\b|\bkubernetes\b", "DevOps"),
    (r"\bblockchain\b|\bcrypto\b|\bweb3\b", "Blockchain / Web3"),
    (r"\biot\b|\binternet of things\b", "Internet of Things (IoT)"),
    (r"\bgaming\b|\bgame dev\b|\bunity\b|\bunreal\b", "Game Development"),
    (r"\bdata engineer\b|\betl\b|\bdata pipeline\b", "Data Engineering"),
    (r"\bproduct manager\b|\bproduct owner\b|\btech lead\b", "Product / Tech Leadership"),
    (r"\bui/ux\b|\buser experience\b|\buser interface\b", "UI/UX Design"),
]

# ── Target Programs — President University Graduate Programs ──────────────────────
# These are the OFFICIAL program names at President University Pascasarjana.
# Each program has weighted keywords for matching candidate profiles.

TARGET_PROGRAMS = [
    # ── S2 Ilmu Komputer ──────────────────────────────────────────────────────
    {
        "name": "S2 Ilmu Komputer (Master of Computer Science)",
        "type": "master",
        "field": "computer_science",
        "keywords": [
            "computer science", "software engineering", "programming",
            "artificial intelligence", "machine learning", "data science",
            "deep learning", "neural network", "cybersecurity", "network security",
            "software developer", "software engineer", "it", "informatika",
            "ilmu komputer", "teknologi informasi",
        ],
    },
    # ── S2 Manajemen ─────────────────────────────────────────────────────────
    {
        "name": "S2 Manajemen (Master of Management)",
        "type": "master",
        "field": "management",
        "keywords": [
            "management", "manajemen", "business", "marketing", "pemasaran",
            "finance", "keuangan", "human resource", "sdm", "sumber daya manusia",
            "strategy", "strategi", "leadership", "kepemimpinan", "organization",
            "retail", "sales", "bisnis", "manajer", "supervisor", "direktur",
            "brand", "customer", "operasional",
        ],
    },
    # ── S2 Teknik Industri ────────────────────────────────────────────────────
    {
        "name": "S2 Teknik Industri (Master of Industrial Engineering)",
        "type": "master",
        "field": "industrial_engineering",
        "keywords": [
            "industrial engineering", "teknik industri", "operations", "operasional",
            "supply chain", "rantai pasok", "manufacturing", "produksi", "pabrik",
            "quality", "kualitas", "lean", "six sigma", "kaizen", "logistics",
            "logistik", "warehouse", "gudang", "process improvement", "erp",
            "plant", "engineer", "insinyur",
        ],
    },
    # ── MBA Eksekutif ────────────────────────────────────────────────────────
    {
        "name": "MBA Eksekutif (Executive MBA)",
        "type": "master",
        "field": "management",
        "keywords": [
            "executive", "eksekutif", "director", "direktur", "vp", "vice president",
            "ceo", "coo", "cfo", "general manager", "gm", "senior manager",
            "mba", "business administration", "corporate", "korporat",
            "entrepreneur", "wirausaha", "business owner", "pemilik usaha",
            "investment", "investasi", "venture",
        ],
    },
]


def _get_text_to_analyze(lead: Lead) -> str:
    """Combine all text fields from a lead for keyword analysis."""
    parts = [
        lead.headline or "",
        lead.summary or "",
        lead.job_title or "",
        lead.education_level or "",
        lead.notes or "",
    ]
    if lead.skills:
        parts.extend(lead.skills)
    if lead.education:
        for edu in lead.education:
            if isinstance(edu, dict):
                parts.extend([str(v) for v in edu.values() if v])
    if lead.experience:
        for exp in lead.experience:
            if isinstance(exp, dict):
                parts.extend([str(v) for v in exp.values() if v])
    return " ".join(parts).lower()


# ── CS Relevance Scoring (from intake-agent-2 profilingService.js) ─────────────

def analyze_cs_relevance(lead: Lead) -> dict:
    """
    Analyze CS relevance based on headline, summary, skills, education, experience.
    Returns a score 0-100 and whether it's CS-related.
    """
    text = _get_text_to_analyze(lead)
    if not text:
        return {"score": 0, "is_cs_related": False, "matched_keywords": []}

    matched_keywords = [kw for kw in CS_KEYWORDS if kw in text]
    score = min(len(matched_keywords) * 8, 100)

    return {
        "score": score,
        "is_cs_related": score >= 30,
        "matched_keywords": matched_keywords,
    }


# ── Education Analysis (from intake-agent-2) ───────────────────────────────────

def analyze_education(lead: Lead) -> dict:
    """
    Determine if the lead is master-level or unknown.
    """
    text = _get_text_to_analyze(lead)
    result = {
        "type": ProfileType.UNKNOWN.value,
        "matched_programs": [],
        "confidence": 0.0,
    }

    master_score = sum(1 for kw in MASTER_KEYWORDS if kw in text)

    if master_score > 0:
        result["type"] = ProfileType.MASTER.value
        result["confidence"] = min(master_score * 20, 100) / 100

    return result


# ── Interest Extraction (from intake-agent-2) ──────────────────────────────────

def extract_interests(lead: Lead) -> list[str]:
    """Extract interests from lead data using pattern matching."""
    text = _get_text_to_analyze(lead)
    interests = []
    for pattern, label in INTEREST_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            interests.append(label)
    return interests


# ── Program Matching (from intake-agent-2) ─────────────────────────────────────

def determine_program_match(lead: Lead, profile_type: str) -> list[dict]:
    """
    Match lead to target programs based on profile type and keyword analysis.
    """
    text = _get_text_to_analyze(lead)
    matches = []

    for program in TARGET_PROGRAMS:
        # Filter by profile type
        if profile_type != ProfileType.UNKNOWN.value and program["type"] != profile_type:
            continue

        matched_keywords = [kw for kw in program["keywords"] if kw in text]
        if matched_keywords:
            confidence = min(len(matched_keywords) * 20, 100)
            matches.append({
                "name": program["name"],
                "type": program["type"],
                "confidence": confidence,
                "matched_keywords": matched_keywords,
            })

    # Sort by confidence descending
    matches.sort(key=lambda x: x["confidence"], reverse=True)
    return matches


# ── Weighted Scoring (from recruit-Z profileGenerator.js) ──────────────────────

WEIGHTS = {
    "academic_score": 0.35,
    "engagement_potential": 0.20,
    "program_fit": 0.30,
    "data_completeness": 0.15,
}


def calculate_academic_score(lead: Lead) -> float:
    """
    Calculate academic score based on education level and CS relevance.
    0-100 scale.
    """
    text = _get_text_to_analyze(lead)
    score = 0.0

    # Education level points
    if lead.education_level:
        edu_lower = lead.education_level.lower()
        if any(kw in edu_lower for kw in MASTER_KEYWORDS):
            score += 30
        else:
            score += 10

    # CS relevance bonus
    cs = analyze_cs_relevance(lead)
    score += cs["score"] * 0.4

    # Skills bonus
    if lead.skills and len(lead.skills) > 0:
        score += min(len(lead.skills) * 2, 20)

    return min(score, 100)


def calculate_engagement_potential(lead: Lead) -> float:
    """
    Calculate engagement potential based on profile completeness
    and professional activity indicators.
    """
    score = 0.0

    # Has LinkedIn URL
    if lead.linkedin_url:
        score += 15

    # Has headline
    if lead.headline:
        score += 10

    # Has summary
    if lead.summary:
        score += 15

    # Has skills
    if lead.skills and len(lead.skills) > 0:
        score += min(len(lead.skills) * 5, 20)

    # Has experience
    if lead.experience and len(lead.experience) > 0:
        score += min(len(lead.experience) * 5, 20)

    # Has education
    if lead.education and len(lead.education) > 0:
        score += 10

    # Has phone
    if lead.phone:
        score += 10

    return min(score, 100)


def calculate_program_fit(lead: Lead) -> float:
    """
    Calculate program fit based on CS relevance and matched programs.
    """
    cs = analyze_cs_relevance(lead)
    education = analyze_education(lead)
    matches = determine_program_match(lead, education["type"])

    score = cs["score"] * 0.5

    if matches:
        best_match = matches[0]
        score += best_match["confidence"] * 0.5

    return min(score, 100)


def calculate_data_completeness(lead: Lead) -> float:
    """
    Calculate data completeness score based on how many fields are filled.
    """
    fields = [
        ("name", lead.name),
        ("email", lead.email),
        ("phone", lead.phone),
        ("linkedin_url", lead.linkedin_url),
        ("headline", lead.headline),
        ("summary", lead.summary),
        ("company", lead.company),
        ("job_title", lead.job_title),
        ("location", lead.location),
        ("education_level", lead.education_level),
        ("skills", lead.skills and len(lead.skills) > 0),
        ("education", lead.education and len(lead.education) > 0),
        ("experience", lead.experience and len(lead.experience) > 0),
    ]

    filled = sum(1 for _, value in fields if value)
    return (filled / len(fields)) * 100


def assess_data_quality(lead: Lead) -> str:
    """
    Assess data quality as high/medium/low based on completeness and key fields.
    """
    completeness = calculate_data_completeness(lead)

    if completeness >= 70 and lead.email:
        return DataQuality.HIGH.value
    elif completeness >= 40 or lead.email:
        return DataQuality.MEDIUM.value
    else:
        return DataQuality.LOW.value


# ── Tag Generation (from recruit-Z) ────────────────────────────────────────────

def generate_tags(lead: Lead, scores: dict | None = None) -> list[str]:
    """Generate auto-tags based on lead data."""
    tags = []
    text = _get_text_to_analyze(lead)

    if scores and scores.get("is_cs_related"):
        tags.append("cs_related")

    if lead.education_level:
        edu_lower = lead.education_level.lower()
        if any(kw in edu_lower for kw in MASTER_KEYWORDS):
            tags.append("master")

    if lead.headline:
        tags.append("has_headline")
    if lead.summary:
        tags.append("has_summary")
    if lead.skills and len(lead.skills) > 0:
        tags.append("has_skills")
    if lead.linkedin_url:
        tags.append("has_linkedin")

    interests = extract_interests(lead)
    for interest in interests:
        tag = interest.lower().replace(" / ", "_").replace(" ", "_").replace("/", "_")
        tags.append(f"interest_{tag}")

    return tags


# ── Main Profiling Pipeline ────────────────────────────────────────────────────

async def profile_lead(lead: Lead, db: AsyncSession) -> Lead:
    """
    Run the full profiling pipeline on a single lead.
    Updates the lead in-place and commits to DB.
    """
    # 1. CS Relevance
    cs = analyze_cs_relevance(lead)
    lead.is_computer_science_related = cs["is_cs_related"]

    # 2. Education Analysis
    education = analyze_education(lead)
    lead.profile_type = education["type"]

    # 3. Program Matching
    matches = determine_program_match(lead, education["type"])
    lead.matched_programs = matches
    if matches:
        lead.recommended_program = matches[0]["name"]

    # 4. Weighted Scoring
    academic = calculate_academic_score(lead)
    engagement = calculate_engagement_potential(lead)
    program_fit = calculate_program_fit(lead)
    completeness = calculate_data_completeness(lead)

    weighted_score = (
        academic * WEIGHTS["academic_score"]
        + engagement * WEIGHTS["engagement_potential"]
        + program_fit * WEIGHTS["program_fit"]
        + completeness * WEIGHTS["data_completeness"]
    )

    lead.profile_score = round(weighted_score, 2)
    lead.priority_score = int(weighted_score)

    # 5. Data Quality
    lead.data_quality = assess_data_quality(lead)

    # 6. Tags
    lead.tags = generate_tags(lead, {"is_cs_related": cs["is_cs_related"]})

    # 7. Update status
    lead.status = LeadStatus.PROFILED.value
    lead.profiled_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(lead)
    return lead


async def profile_batch(lead_ids: list[uuid.UUID], db: AsyncSession) -> dict:
    """
    Profile multiple leads by ID.
    Returns summary of profiling results.
    """
    result = await db.execute(select(Lead).where(Lead.id.in_(lead_ids)))
    leads = result.scalars().all()

    results = {"total": len(leads), "profiled": 0, "errors": []}
    for lead in leads:
        try:
            await profile_lead(lead, db)
            results["profiled"] += 1
        except Exception as e:
            results["errors"].append({"id": str(lead.id), "error": str(e)})

    return results


async def get_profiling_stats(db: AsyncSession) -> dict:
    """Get aggregate profiling statistics."""
    total = await db.scalar(select(func.count(Lead.id)))
    profiled = await db.scalar(
        select(func.count(Lead.id)).where(Lead.status == LeadStatus.PROFILED.value)
    )
    cs_related = await db.scalar(
        select(func.count(Lead.id)).where(Lead.is_computer_science_related == True)
    )
    avg_score = await db.scalar(
        select(func.avg(Lead.profile_score)).where(Lead.profile_score.isnot(None))
    )

    # Count by profile type
    master_count = await db.scalar(
        select(func.count(Lead.id)).where(Lead.profile_type == ProfileType.MASTER.value)
    )

    return {
        "total_leads": total or 0,
        "profiled": profiled or 0,
        "cs_related": cs_related or 0,
        "average_score": round(avg_score, 2) if avg_score else 0,
        "by_type": {
            "master": master_count or 0,
            "other": (total or 0) - (master_count or 0),
        },
    }
