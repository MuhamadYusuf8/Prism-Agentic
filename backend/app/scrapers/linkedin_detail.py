"""
LinkedIn Detail Scraper — Phase 2 of the two-phase scraping pipeline.

Phase 1 (serper/linkedin.py) discovers profile URLs from Google search snippets.
Phase 2 (this module) visits each profile URL with an authenticated LinkedIn session
to extract full profile data: skills, education, experience, headline, summary, etc.

Authentication: uses the `li_at` session cookie from a logged-in LinkedIn account.
Set LINKEDIN_LI_AT in .env or provide it via the Settings page.

Strategy A — LinkedIn Internal API (preferred):
  The web UI calls internal REST APIs returning structured JSON.
  When authenticated with li_at, these endpoints return full profile data.

Strategy B — HTML Parsing (fallback):
  If the API is blocked, parse the public profile page HTML.
"""

import asyncio
import json
import re
import httpx
import random
import structlog
from typing import Any

log = structlog.get_logger()

# ── Headers ───────────────────────────────────────────────────────────────────

BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

LINKEDIN_API_BASE = "https://www.linkedin.com/voyager/api"


def _extract_username(url: str) -> str | None:
    """Extract the LinkedIn username/slug from a profile URL."""
    m = re.search(r"linkedin\.com/in/([^/?#]+)", url)
    return m.group(1).strip("/") if m else None


def _extract_profile_urn(html: str) -> str | None:
    """Extract the profile URN (e.g. 'urn:li:person:abc123') from the page HTML."""
    m = re.search(r'"urn:li:person:([^"]+)"', html)
    if m:
        return f"urn:li:person:{m.group(1)}"
    # Alternative pattern
    m = re.search(r'"(?:urn:li:person|com\.linkedin\.voyager\.identity\.shared\.Profile)\[([^\]]+)\]"', html)
    if m:
        return f"urn:li:person:{m.group(1)}"
    return None


def _extract_csrf_token(headers: dict, cookie: str) -> str | None:
    """Extract CSRF token from the li_at cookie or response headers."""
    # JSESSIONID is often the CSRF token for LinkedIn
    for c in cookie.split(";"):
        c = c.strip()
        if c.startswith("JSESSIONID"):
            val = c.split("=", 1)[1].strip()
            return val.strip('"')
    # Fallback: check headers
    for key in ["csrf-token", "x-csrf-token", "Csrf-Token"]:
        val = headers.get(key)
        if val:
            return val
    return None


# ── Strategy A: LinkedIn Internal API ─────────────────────────────────────────

async def _fetch_api_profile(
    client: httpx.AsyncClient,
    username: str,
    cookie: str,
    csrf_token: str,
) -> dict | None:
    """
    Fetch full profile data from LinkedIn's internal Voyager API.
    Returns a dict with skills, education, experience, etc.
    """
    profile_urn = f"urn:li:person:{username}" if ":" not in username else username

    api_headers = {
        **BASE_HEADERS,
        "Cookie": cookie,
        "Csrf-Token": csrf_token,
    }

    # Voyager profile endpoint
    url = f"{LINKEDIN_API_BASE}/identity/profiles/{profile_urn}/profileView"

    try:
        resp = await client.get(url, headers=api_headers, timeout=15)
        if resp.status_code != 200:
            log.warning("api_profile_failed", username=username, status=resp.status_code)
            return None

        data = resp.json()

        # Navigate the Voyager response to extract relevant sections
        result = {}

        # Extract headline
        headline = data.get("headline", "")
        if isinstance(headline, dict):
            headline = headline.get("text", "")
        result["headline"] = str(headline) if headline else None

        # Extract summary/about
        summary = data.get("summary", "")
        if isinstance(summary, dict):
            summary = summary.get("text", "")
        result["summary"] = str(summary) if summary else None

        # Extract skills from the miniSkills section
        skills = []
        skill_components = data.get("skillComponents", []) or data.get("skills", []) or []
        for skill in skill_components:
            if isinstance(skill, dict):
                name = skill.get("name", {}).get("text", "") if isinstance(skill.get("name"), dict) else skill.get("name", "")
                if name:
                    skills.append(name)
        # Also check for miniSkills
        mini_skills = data.get("miniSkills", []) or []
        for skill in mini_skills:
            if isinstance(skill, dict):
                name = skill.get("name", "") or skill.get("name", {}).get("text", "")
                if name and name not in skills:
                    skills.append(name)
        result["skills"] = skills if skills else None

        # Extract education
        education = []
        edu_components = data.get("educationComponents", []) or data.get("education", []) or []
        for edu in edu_components:
            if not isinstance(edu, dict):
                continue
            school = edu.get("schoolName", "") or edu.get("school", {})
            if isinstance(school, dict):
                school = school.get("text", "")
            degree = edu.get("degreeName", "") or edu.get("degree", {})
            if isinstance(degree, dict):
                degree = degree.get("text", "")
            field = edu.get("fieldOfStudy", "") or edu.get("field", {})
            if isinstance(field, dict):
                field = field.get("text", "")
            entry = {
                "institution": str(school) if school else None,
                "degree": str(degree) if degree else None,
                "field": str(field) if field else None,
            }
            # Remove None values
            entry = {k: v for k, v in entry.items() if v}
            if entry.get("institution"):
                education.append(entry)
        result["education"] = education if education else None

        # Extract experience
        experience = []
        exp_components = data.get("experienceComponents", []) or data.get("position", []) or data.get("experience", []) or []
        for exp in exp_components:
            if not isinstance(exp, dict):
                continue
            company = exp.get("companyName", "") or exp.get("company", {})
            if isinstance(company, dict):
                company = company.get("text", "")
            title = exp.get("title", "") or exp.get("jobTitle", {})
            if isinstance(title, dict):
                title = title.get("text", "")
            entry = {
                "company": str(company) if company else None,
                "title": str(title) if title else None,
            }
            entry = {k: v for k, v in entry.items() if v}
            if entry.get("company") or entry.get("title"):
                experience.append(entry)
        result["experience"] = experience if experience else None

        # Extract location
        location = data.get("locationName", "") or ""
        result["location"] = str(location) if location else None

        # Extract industry
        industry = data.get("industryName", "") or ""
        result["industry"] = str(industry) if industry else None

        return result

    except Exception as e:
        log.warning("api_profile_error", username=username, error=str(e))
        return None


# ── Strategy B: HTML Parsing (Fallback) ───────────────────────────────────────

async def _fetch_html_profile(
    client: httpx.AsyncClient,
    username: str,
    cookie: str,
) -> dict | None:
    """
    Fallback: fetch the public profile page and parse skills/education from HTML.
    Works even when the API is blocked.
    """
    url = f"https://www.linkedin.com/in/{username}/"
    headers = {**BASE_HEADERS, "Cookie": cookie}

    try:
        resp = await client.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            log.warning("html_profile_failed", username=username, status=resp.status_code)
            return None

        html = resp.text
        result = {}

        # Extract headline from title tag
        title_match = re.search(r"<title>(.*?)</title>", html, re.DOTALL)
        if title_match:
            title_text = title_match.group(1).replace(" | LinkedIn", "").strip()
            parts = title_text.split(" - ", 1)
            result["headline"] = parts[1].strip() if len(parts) > 1 else None

        # Extract skills from the skills section
        skills = []
        # Look for JSON-LD or data embedded in the page
        skills_section = re.search(
            r'(?:skill|Skill|SKILL).{0,100}?section.{0,500}?'
            r'(?:<li[^>]*>.*?<\/li>\s*)+',
            html[:50000], re.DOTALL | re.IGNORECASE
        )
        if skills_section:
            skill_items = re.findall(r'<li[^>]*>(.*?)<\/li>', skills_section.group(0), re.DOTALL)
            for item in skill_items:
                skill = re.sub(r'<[^>]+>', '', item).strip()
                if skill and len(skill) < 100:
                    skills.append(skill)

        # Also try to find skills in the embedded JSON data
        json_matches = re.findall(
            r'"skills"[^\[\]]*\[([^\]]*)\]', html, re.IGNORECASE
        )
        for match in json_matches:
            items = re.findall(r'"([^"]+)"', match)
            for item in items:
                if item and len(item) < 100 and item not in skills:
                    skills.append(item)

        result["skills"] = skills if skills else None

        # Extract education from embedded JSON
        education = []
        edu_matches = re.findall(
            r'"education"[^\[\]]*\[([^\]]*)\]', html, re.IGNORECASE
        )
        for match in edu_matches:
            schools = re.findall(r'"schoolName"[^"]*"([^"]+)"', match)
            degrees = re.findall(r'"degreeName"[^"]*"([^"]+)"', match)
            for i, school in enumerate(schools):
                entry = {"institution": school}
                if i < len(degrees):
                    entry["degree"] = degrees[i]
                education.append(entry)

        result["education"] = education if education else None

        # Extract summary/about
        summary_match = re.search(
            r'(?:About|Tentang|Summary).{0,50}?<p[^>]*>(.*?)</p>',
            html[:30000], re.DOTALL | re.IGNORECASE
        )
        if summary_match:
            summary = re.sub(r'<[^>]+>', '', summary_match.group(1)).strip()
            result["summary"] = summary if summary else None

        return result

    except Exception as e:
        log.warning("html_profile_error", username=username, error=str(e))
        return None


# ── Public API ────────────────────────────────────────────────────────────────

async def enrich_linkedin_profile(
    profile_url: str,
    li_at_cookie: str,
) -> dict:
    """
    Enrich a single LinkedIn profile by scraping its full details.

    Args:
        profile_url: Full LinkedIn profile URL (e.g., https://www.linkedin.com/in/username)
        li_at_cookie: The `li_at` session cookie value

    Returns:
        dict with extracted fields: skills, education, experience, headline, summary, etc.
        Returns an empty dict if the profile could not be scraped.
    """
    username = _extract_username(profile_url)
    if not username:
        log.warning("invalid_profile_url", url=profile_url)
        return {}

    cookie = f"li_at={li_at_cookie};"

    async with httpx.AsyncClient(follow_redirects=True) as client:
        # Step 1: Fetch the profile page once to get the URN and CSRF token
        headers = {**BASE_HEADERS, "Cookie": cookie}
        try:
            init_resp = await client.get(
                f"https://www.linkedin.com/in/{username}/",
                headers=headers,
                timeout=15,
            )
            if init_resp.status_code == 999:
                log.warning("linkedin_blocked", username=username, status=999)
                return {}
            if init_resp.status_code == 401 or init_resp.status_code == 302:
                log.warning("linkedin_session_expired", username=username)
                return {}

            html = init_resp.text
            csrf_token = _extract_csrf_token(dict(init_resp.headers), cookie)

            # Step 2: Try Strategy A — Internal API
            if csrf_token:
                profile_data = await _fetch_api_profile(
                    client, username, cookie, csrf_token
                )
                if profile_data:
                    profile_data["linkedin_url"] = profile_url
                    return profile_data

            # Step 3: Fallback to Strategy B — HTML parsing
            log.info("fallback_to_html_parse", username=username)
            profile_data = await _fetch_html_profile(client, username, cookie)
            if profile_data:
                profile_data["linkedin_url"] = profile_url
                return profile_data

        except httpx.TimeoutException:
            log.warning("profile_timeout", username=username)
        except Exception as e:
            log.warning("profile_error", username=username, error=str(e))

    return {}


async def batch_enrich_profiles(
    profile_urls: list[str],
    li_at_cookie: str,
    delay_range: tuple[float, float] = (3.0, 5.0),
) -> list[dict]:
    """
    Enrich multiple LinkedIn profiles sequentially with random delays.

    Args:
        profile_urls: List of LinkedIn profile URLs
        li_at_cookie: The `li_at` session cookie value
        delay_range: Min/max seconds to wait between requests

    Returns:
        List of enriched profile dicts (one per URL, empty dict if failed)
    """
    results = []
    total = len(profile_urls)

    for i, url in enumerate(profile_urls):
        log.info("enriching_profile", url=url, current=i + 1, total=total)

        data = await enrich_linkedin_profile(url, li_at_cookie)

        results.append({
            "profile_url": url,
            "data": data,
            "success": bool(data),
            "progress": {"current": i + 1, "total": total},
        })

        # Apply random delay between requests (avoid rate limiting)
        if i < total - 1:
            delay = random.uniform(*delay_range)
            log.debug("rate_limit_delay", seconds=round(delay, 1))
            await asyncio.sleep(delay)

    return results
