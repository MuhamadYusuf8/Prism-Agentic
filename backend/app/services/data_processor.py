"""
Data Processor — ports from student-recruitment-automation_duplicateZ dataProcessor.js.

Handles data cleaning, validation, normalization, deduplication, and merging.
"""

import re
import uuid
from typing import Any
from email_validator import validate_email, EmailNotValidError

from app.models.lead import Lead, DataQuality


# ── Email Validation ───────────────────────────────────────────────────────────

def is_valid_email(email: str | None) -> bool:
    """Validate email format."""
    if not email:
        return False
    try:
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


# ── Phone Cleaning ─────────────────────────────────────────────────────────────

def clean_phone(phone: str | None) -> str | None:
    """Clean and normalize phone number."""
    if not phone:
        return None
    # Remove non-digit characters except +
    cleaned = re.sub(r"[^\d+]", "", phone)
    # Ensure minimum length
    if len(cleaned) < 8:
        return None
    return cleaned


# ── Name Normalization ─────────────────────────────────────────────────────────

def normalize_name(name: str | None) -> str | None:
    """Normalize name: strip whitespace, capitalize properly."""
    if not name:
        return None
    name = name.strip()
    if not name:
        return None
    # Remove extra whitespace
    name = re.sub(r"\s+", " ", name)
    # Title case
    name = name.title()
    return name


# ── Location Parsing ───────────────────────────────────────────────────────────

def parse_location(location: str | None) -> str | None:
    """Parse and normalize location string."""
    if not location:
        return None
    location = location.strip()
    if not location:
        return None
    # Remove common prefixes
    location = re.sub(r"^(location|based in|located in|area|region):?\s*", "", location, flags=re.IGNORECASE)
    return location.strip()


# ── Degree Normalization ───────────────────────────────────────────────────────

DEGREE_MAP = {
    "bachelor": "Bachelor",
    "bachelor's": "Bachelor",
    "bachelor's degree": "Bachelor",
    "b.sc": "Bachelor",
    "b.sc.": "Bachelor",
    "bs": "Bachelor",
    "b.s.": "Bachelor",
    "s1": "Bachelor",
    "sarjana": "Bachelor",
    "undergraduate": "Bachelor",
    "master": "Master",
    "master's": "Master",
    "master's degree": "Master",
    "m.sc": "Master",
    "m.sc.": "Master",
    "ms": "Master",
    "m.s.": "Master",
    "s2": "Master",
    "magister": "Master",
    "postgraduate": "Master",
    "post graduate": "Master",
    "phd": "PhD",
    "ph.d": "PhD",
    "ph.d.": "PhD",
    "doctor": "PhD",
    "doctorate": "PhD",
    "doctoral": "PhD",
    "s3": "PhD",
    "high school": "High School",
    "sma": "High School",
    "smk": "High School",
    "associate": "Associate",
    "associate's": "Associate",
    "a.a.": "Associate",
    "diploma": "Diploma",
    "d3": "Diploma",
    "d4": "Diploma",
}


def normalize_degree(degree: str | None) -> str | None:
    """Normalize degree string to standard values."""
    if not degree:
        return None
    degree_lower = degree.strip().lower()
    return DEGREE_MAP.get(degree_lower, degree.strip())


# ── Student Validation ─────────────────────────────────────────────────────────

def validate_student(data: dict) -> dict:
    """
    Validate student data. Returns dict with 'valid' bool and 'errors' list.
    Requires at minimum: name + (email or source).
    """
    errors = []
    name = data.get("name")
    email = data.get("email")
    source = data.get("source")

    if not name:
        errors.append("Name is required")
    if not email and not source:
        errors.append("Either email or source is required")
    if email and not is_valid_email(email):
        errors.append(f"Invalid email format: {email}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


# ── Data Cleaning ──────────────────────────────────────────────────────────────

def clean_student(data: dict) -> dict:
    """Clean and normalize student data fields."""
    cleaned = dict(data)

    # Name
    if "name" in cleaned:
        cleaned["name"] = normalize_name(cleaned["name"])

    # Email
    if "email" in cleaned:
        email = cleaned["email"]
        if email:
            cleaned["email"] = email.strip().lower()

    # Phone
    if "phone" in cleaned:
        cleaned["phone"] = clean_phone(cleaned["phone"])

    # Location
    if "location" in cleaned:
        cleaned["location"] = parse_location(cleaned["location"])

    # Education level
    if "education_level" in cleaned:
        cleaned["education_level"] = normalize_degree(cleaned["education_level"])

    # LinkedIn URL
    if "linkedin_url" in cleaned:
        url = cleaned["linkedin_url"]
        if url:
            url = url.strip()
            # Ensure it's a valid LinkedIn URL
            if "linkedin.com/in/" not in url:
                cleaned["linkedin_url"] = None
            else:
                cleaned["linkedin_url"] = url

    # Source
    if "source" in cleaned:
        cleaned["source"] = cleaned["source"].strip().lower().replace(" ", "_")

    return cleaned


# ── Deduplication ──────────────────────────────────────────────────────────────

def find_duplicates(leads: list[Lead]) -> list[list[Lead]]:
    """
    Find duplicate leads based on email or LinkedIn URL.
    Returns groups of duplicate leads.
    """
    email_map: dict[str, list[Lead]] = {}
    linkedin_map: dict[str, list[Lead]] = {}
    seen: set[uuid.UUID] = set()
    duplicate_groups: list[list[Lead]] = []

    for lead in leads:
        # Group by email
        if lead.email:
            email_lower = lead.email.lower()
            if email_lower not in email_map:
                email_map[email_lower] = []
            email_map[email_lower].append(lead)

        # Group by LinkedIn URL
        if lead.linkedin_url:
            url = lead.linkedin_url.strip().lower()
            if url not in linkedin_map:
                linkedin_map[url] = []
            linkedin_map[url].append(lead)

    # Find groups with duplicates
    for group in email_map.values():
        if len(group) > 1:
            group_ids = {l.id for l in group}
            if not group_ids.intersection(seen):
                duplicate_groups.append(group)
                seen.update(group_ids)

    for group in linkedin_map.values():
        if len(group) > 1:
            group_ids = {l.id for l in group}
            if not group_ids.intersection(seen):
                duplicate_groups.append(group)
                seen.update(group_ids)

    return duplicate_groups


def merge_duplicates(duplicate_group: list[Lead]) -> Lead:
    """
    Merge a group of duplicate leads into a single lead.
    The lead with the most complete data (most fields filled) is kept as primary.
    """
    if not duplicate_group:
        raise ValueError("Empty duplicate group")

    if len(duplicate_group) == 1:
        return duplicate_group[0]

    # Score each lead by data completeness
    def completeness_score(lead: Lead) -> int:
        score = 0
        for field in [
            "name", "email", "phone", "linkedin_url", "headline", "summary",
            "company", "job_title", "location", "education_level",
        ]:
            if getattr(lead, field, None):
                score += 1
        if lead.skills:
            score += len(lead.skills)
        if lead.education:
            score += len(lead.education)
        if lead.experience:
            score += len(lead.experience)
        return score

    # Sort by completeness (best first)
    sorted_leads = sorted(duplicate_group, key=completeness_score, reverse=True)
    primary = sorted_leads[0]

    # Merge data from other leads into primary
    for secondary in sorted_leads[1:]:
        for field in [
            "name", "email", "phone", "linkedin_url", "headline", "summary",
            "company", "job_title", "industry", "location", "education_level",
            "notes",
        ]:
            primary_val = getattr(primary, field, None)
            secondary_val = getattr(secondary, field, None)
            if not primary_val and secondary_val:
                setattr(primary, field, secondary_val)

        # Merge skills (union)
        if secondary.skills:
            if not primary.skills:
                primary.skills = []
            existing_skills = {s.lower() for s in primary.skills}
            for skill in secondary.skills:
                if skill.lower() not in existing_skills:
                    primary.skills.append(skill)
                    existing_skills.add(skill.lower())

        # Merge education (union by institution + degree)
        if secondary.education:
            if not primary.education:
                primary.education = []
            existing_edu = {
                (e.get("institution", "").lower(), e.get("degree", "").lower())
                for e in primary.education if isinstance(e, dict)
            }
            for edu in secondary.education:
                if isinstance(edu, dict):
                    key = (edu.get("institution", "").lower(), edu.get("degree", "").lower())
                    if key not in existing_edu:
                        primary.education.append(edu)
                        existing_edu.add(key)

        # Merge experience (union by company + title)
        if secondary.experience:
            if not primary.experience:
                primary.experience = []
            existing_exp = {
                (e.get("company", "").lower(), e.get("title", "").lower())
                for e in primary.experience if isinstance(e, dict)
            }
            for exp in secondary.experience:
                if isinstance(exp, dict):
                    key = (exp.get("company", "").lower(), exp.get("title", "").lower())
                    if key not in existing_exp:
                        primary.experience.append(exp)
                        existing_exp.add(key)

        # Merge tags (union)
        if secondary.tags:
            if not primary.tags:
                primary.tags = []
            existing_tags = set(primary.tags)
            for tag in secondary.tags:
                if tag not in existing_tags:
                    primary.tags.append(tag)
                    existing_tags.add(tag)

        # Merge raw_data
        if secondary.raw_data:
            if not primary.raw_data:
                primary.raw_data = {}
            primary.raw_data.update(secondary.raw_data)

    return primary


async def process_and_deduplicate(
    new_leads: list[Lead],
    existing_leads: list[Lead],
) -> tuple[list[Lead], list[Lead]]:
    """
    Process new leads: clean, validate, deduplicate against existing leads.
    Returns (unique_leads, duplicates_found).
    """
    duplicates_found = []

    # Clean each lead
    for lead in new_leads:
        # SQLAlchemy model fields are set directly, but we can clean string fields
        if lead.name:
            lead.name = normalize_name(lead.name) or lead.name
        if lead.email:
            lead.email = lead.email.strip().lower()
        if lead.phone:
            lead.phone = clean_phone(lead.phone)
        if lead.location:
            lead.location = parse_location(lead.location)
        if lead.education_level:
            lead.education_level = normalize_degree(lead.education_level)

    # Deduplicate against existing leads
    all_leads = existing_leads + new_leads
    duplicate_groups = find_duplicates(all_leads)

    # Identify which new leads are duplicates
    duplicate_ids: set[uuid.UUID] = set()
    for group in duplicate_groups:
        existing_in_group = [l for l in group if l in existing_leads]
        new_in_group = [l for l in group if l in new_leads]
        if existing_in_group and new_in_group:
            for nl in new_in_group:
                duplicate_ids.add(nl.id)
                duplicates_found.append(nl)

    # Return unique new leads
    unique_leads = [l for l in new_leads if l.id not in duplicate_ids]
    return unique_leads, duplicates_found
