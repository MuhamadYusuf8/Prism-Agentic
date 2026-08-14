"""
Email Discovery Service — finds email addresses for scraped leads WITHOUT LinkedIn.

Strategies (tried in order):
  1. Serper web search  — query the lead's name + email patterns, extract from snippets
  2. Hunter.io API      — email-finder by domain + first/last name (requires HUNTER_API_KEY)
  3. Pattern guessing   — generate common email patterns from name + company domain

The best found email is returned along with a confidence score and the source.
"""

import re
import asyncio
import httpx
import structlog

from app.core.config import settings

log = structlog.get_logger()

SERPER_URL = "https://google.serper.dev/search"
HUNTER_URL = "https://api.hunter.io/v2/email-finder"

# Regex to match email addresses in text
EMAIL_RE = re.compile(
    r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"
)


def _extract_emails(text: str) -> list[str]:
    """Extract unique email addresses from a text blob."""
    if not text:
        return []
    found = set()
    for m in EMAIL_RE.finditer(text):
        email = m.group(0).strip(".,;:'\"()[]<>")
        if "." in email.split("@")[-1]:  # must have a TLD
            found.add(email.lower())
    return sorted(found)


def _build_serper_queries(first: str, last: str, company: str, domain: str | None) -> list[str]:
    """Build search queries to find the lead's email."""
    full = f"{first} {last}".strip()
    queries = [
        f'"{first} {last}" email',
        f'"{first} {last}" "@gmail.com" OR "@yahoo.com" OR "@hotmail.com"',
    ]
    if domain:
        queries.append(f'"{first} {last}" site:{domain} "@"')
        queries.append(f'"{first} {last}" {domain} email')
    elif company:
        queries.append(f'"{first} {last}" "{company}" email')
    return queries


async def _serper_email_search(
    client: httpx.AsyncClient,
    first: str,
    last: str,
    company: str,
    domain: str | None,
) -> list[dict]:
    """Search for the lead's email via Serper (Google Search)."""
    if not settings.SERPER_API_KEY:
        return []

    queries = _build_serper_queries(first, last, company, domain)
    candidates: dict[str, dict] = {}

    for query in queries[:3]:
        try:
            resp = await client.post(
                SERPER_URL,
                headers={
                    "X-API-KEY": settings.SERPER_API_KEY,
                    "Content-Type": "application/json",
                },
                json={"q": query, "num": 5, "gl": "id", "hl": "id"},
                timeout=20,
            )
            if resp.status_code != 200:
                continue

            data = resp.json()
            for item in data.get("organic", []):
                snippet = item.get("snippet", "")
                title = item.get("title", "")
                link = item.get("link", "")
                blob = f"{title} {snippet} {link}"
                emails = _extract_emails(blob)
                for email in emails:
                    cand = candidates.get(email, {"email": email, "sources": [], "count": 0})
                    if link not in cand["sources"]:
                        cand["sources"].append(link)
                    cand["count"] += 1
                    candidates[email] = cand

            await asyncio.sleep(0.3)
        except Exception as e:
            log.warning("serper_email_search_failed", query=query[:60], error=str(e))

    # Score: emails seen multiple times / with company context rank higher
    ranked = sorted(
        candidates.values(),
        key=lambda c: (c["count"], -len(c["email"])),
        reverse=True,
    )
    return ranked


async def _hunter_email_finder(
    client: httpx.AsyncClient,
    first: str,
    last: str,
    domain: str | None,
) -> dict | None:
    """Use Hunter.io email-finder API. Requires HUNTER_API_KEY in .env."""
    if not settings.HUNTER_API_KEY or not domain:
        return None

    try:
        resp = await client.get(
            HUNTER_URL,
            params={
                "domain": domain,
                "first_name": first,
                "last_name": last,
                "api_key": settings.HUNTER_API_KEY,
            },
            timeout=20,
        )
        if resp.status_code != 200:
            log.warning("hunter_failed", status=resp.status_code, body=resp.text[:200])
            return None

        data = resp.json().get("data", {})
        email = data.get("email")
        if not email:
            return None
        return {
            "email": email,
            "confidence": data.get("score", 50),
            "sources": [s.get("uri") for s in data.get("sources", []) if s.get("uri")],
            "count": 1,
            "source_api": "hunter",
        }
    except Exception as e:
        log.warning("hunter_error", error=str(e))
        return None


def _pattern_emails(first: str, last: str, domain: str | None) -> list[dict]:
    """Generate common email patterns from a name + domain."""
    if not domain:
        return []
    f = first.lower().strip()
    l = last.lower().strip()
    patterns = [
        f"{f}.{l}@{domain}",
        f"{f}{l}@{domain}",
        f"{f}@{domain}",
        f"{f[0]}.{l}@{domain}",
        f"{l}.{f}@{domain}",
        f"{f[0]}{l}@{domain}",
        f"{l}@{domain}",
    ]
    seen = set()
    result = []
    for email in patterns:
        if email not in seen and "@" in email and email.split("@")[1] == domain:
            seen.add(email)
            result.append({"email": email, "count": 0, "sources": [], "confidence": 10, "guessed": True})
    return result


def _parse_name(name: str) -> tuple[str, str]:
    """Split a full name into first/last (best effort)."""
    parts = [p for p in re.split(r"\s+", name.strip()) if p]
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], parts[0]
    # Last token is the surname (ignore middle names)
    return parts[0], parts[-1]


def _clean_domain(domain: str) -> str:
    """Normalize a company website into a bare email domain."""
    domain = domain.strip().lower()
    domain = re.sub(r"^https?://(www\.)?", "", domain)
    domain = domain.split("/")[0].split("?")[0]
    return domain


async def discover_email(
    name: str,
    company: str | None = None,
    website: str | None = None,
) -> dict:
    """
    Discover the best email for a person using all available strategies.

    Args:
        name: Full name of the lead
        company: Company name (used in search queries)
        website: Company website or domain

    Returns:
        {
            "email": str | None,
            "confidence": int (0-100),
            "source": "serper" | "hunter" | "pattern" | None,
            "candidates": [...],
        }
    """
    first, last = _parse_name(name)
    if not first:
        return {"email": None, "confidence": 0, "source": None, "candidates": []}

    domain = _clean_domain(website) if website else None

    async with httpx.AsyncClient(follow_redirects=True) as client:
        # Strategy 1: Serper search
        serper_results = await _serper_email_search(client, first, last, company or "", domain)

        # Strategy 2: Hunter.io
        hunter_result = await _hunter_email_finder(client, first, last, domain)

        # Strategy 3: Pattern guessing
        pattern_results = _pattern_emails(first, last, domain)

    candidates = []

    # Merge Serper candidates
    for cand in serper_results:
        cand["confidence"] = min(40 + cand["count"] * 15, 85)
        cand["source"] = "serper"
        candidates.append(cand)

    # Hunter result is highest priority if present
    if hunter_result:
        hunter_result["confidence"] = hunter_result.get("confidence", 50)
        hunter_result["source"] = "hunter"
        candidates.insert(0, hunter_result)

    # Pattern guesses last (lowest confidence)
    for cand in pattern_results:
        candidates.append(cand)

    if not candidates:
        return {"email": None, "confidence": 0, "source": None, "candidates": []}

    best = candidates[0]
    return {
        "email": best.get("email"),
        "confidence": best.get("confidence", 0),
        "source": best.get("source"),
        "candidates": candidates[:10],
    }
