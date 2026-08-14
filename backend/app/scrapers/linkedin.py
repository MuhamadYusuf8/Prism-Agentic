"""
LinkedIn Scraper — Computer Science Field
Search: Serper.dev (Google Search JSON API, 2500 free queries)
Strategy: Extract all profile data from Google search snippets.
          Never visits linkedin.com directly (avoids HTTP 999 block).

Serper result format:
  title:   "Jason Kanggara - Software Engineer at Tokopedia | LinkedIn"
  link:    "https://id.linkedin.com/in/jasonkanggara"
  snippet: "Jakarta, Indonesia · 500+ connections · Software Engineer at Tokopedia..."
"""

import asyncio
import json
import re
import httpx
from dataclasses import dataclass, asdict, field
from typing import AsyncGenerator
import structlog

log = structlog.get_logger()

SERPER_URL = "https://google.serper.dev/search"

CS_SEARCH_QUERIES = [
    'site:linkedin.com/in "software engineer" Indonesia',
    'site:linkedin.com/in "software developer" Jakarta Indonesia',
    'site:linkedin.com/in "IT Manager" Indonesia',
    'site:linkedin.com/in "data engineer" Indonesia',
    'site:linkedin.com/in "backend engineer" Indonesia',
    'site:linkedin.com/in "full stack developer" Indonesia',
    'site:linkedin.com/in "sistem informasi" Indonesia',
    'site:linkedin.com/in "network engineer" Indonesia',
    'site:linkedin.com/in "DevOps engineer" Indonesia',
    'site:linkedin.com/in "mobile developer" Indonesia',
]

INDONESIAN_REGIONS = [
    "Jakarta Pusat", "Jakarta Selatan", "Jakarta Barat", "Jakarta Utara", "Jakarta Timur",
    "Greater Jakarta", "Jabodetabek",
    "Bekasi", "Cikarang", "Karawang", "Depok", "Bogor", "Bandung", "Cimahi",
    "Tangerang", "Tangerang Selatan", "Serpong",
    "Surabaya", "Yogyakarta", "Semarang", "Medan", "Palembang",
    "Makassar", "Malang", "Denpasar", "Bali", "Batam",
    "Jawa Barat", "Jawa Tengah", "Jawa Timur", "DKI Jakarta", "Banten",
    "Jakarta",
]

SKILLS_KEYWORDS = [
    "python", "java", "javascript", "typescript", "react", "node", "django",
    "golang", "kotlin", "php", "laravel", "vue", "angular", "docker",
    "kubernetes", "aws", "gcp", "azure", "sql", "mysql", "postgresql",
    "mongodb", "redis", "git", "linux", "flutter", "android", "ios",
    "machine learning", "deep learning", "tensorflow", "pytorch", "c++",
    "spring", "fastapi", "microservices", "kafka", "elasticsearch",
]


@dataclass
class LinkedInProfile:
    name: str
    job_title: str | None = None
    company: str | None = None
    location: str | None = None
    area: str | None = None
    linkedin_url: str | None = None
    education_level: str | None = None
    education_institution: str | None = None
    skills: list[str] = field(default_factory=list)
    connections: str | None = None
    summary: str | None = None
    industry: str = "Computer Science / IT"
    source: str = "linkedin"
    raw_data: dict = field(default_factory=dict)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _normalise_linkedin_url(url: str) -> str | None:
    if "linkedin.com/in/" not in url:
        return None
    try:
        clean = url.split("?")[0].split("#")[0].rstrip("/")
        slug = clean.split("linkedin.com/in/")[-1].strip("/")
        return f"https://www.linkedin.com/in/{slug}" if slug else None
    except Exception:
        return None


def _clean_linkedin_suffix(text: str) -> str:
    """Remove trailing LinkedIn/location noise from title parts."""
    text = re.sub(r"\s*[-|–]\s*LinkedIn.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*-\s*LinkedIn\s*(Singapore|Indonesia|Malaysia|Australia)?$", "", text, flags=re.IGNORECASE)
    return text.strip()


def _parse_title(title: str) -> tuple[str | None, str | None, str | None]:
    title = _clean_linkedin_suffix(title)

    if " - " not in title:
        return (title or None), None, None

    parts = title.split(" - ")
    name = parts[0].strip()

    # Remaining parts after name
    rest = " - ".join(parts[1:]).strip()
    rest = _clean_linkedin_suffix(rest)

    # "Software Engineer at Tokopedia"
    if " at " in rest.lower():
        idx = rest.lower().index(" at ")
        job = _clean_linkedin_suffix(rest[:idx].strip())
        company = _clean_linkedin_suffix(rest[idx + 4:].strip())
        return name, job, company

    # "Software Engineer @ Abnormal AI"
    if " @ " in rest:
        idx = rest.index(" @ ")
        job = _clean_linkedin_suffix(rest[:idx].strip())
        company = _clean_linkedin_suffix(rest[idx + 3:].strip())
        return name, job, company

    return name, _clean_linkedin_suffix(rest), None


def _extract_location(text: str) -> tuple[str | None, str | None]:
    """
    Extract location with priority:
    1. "Lokasi: City" or "Location: City" pattern from snippet
    2. "City, Province, Indonesia" pattern
    3. Any known Indonesian region name
    """
    # Priority 1: explicit Lokasi/Location label
    lokasi_match = re.search(
        r"(?:Lokasi|Location)\s*[:\·]\s*([\w\s,]+?)(?:\s*[·\|]|$)",
        text, re.IGNORECASE
    )
    if lokasi_match:
        raw = lokasi_match.group(1).strip().rstrip("·").strip()
        area = raw.split(",")[0].strip()
        if "indonesia" not in raw.lower():
            raw += ", Indonesia"
        return raw, area

    # Priority 2: "City, Province, Country" inline
    geo_match = re.search(
        r"((?:Jakarta\s*\w*|Bandung|Surabaya|Bekasi|Cikarang|Depok|Bogor|"
        r"Tangerang|Yogyakarta|Semarang|Medan|Malang|Bali|Denpasar|Batam|"
        r"Makassar|Palembang|Karawang)\s*(?:,\s*[\w\s]+)?(?:,\s*Indonesia)?)",
        text, re.IGNORECASE
    )
    if geo_match:
        raw = geo_match.group(1).strip().rstrip("·").strip()
        area = raw.split(",")[0].strip()
        if "indonesia" not in raw.lower():
            raw += ", Indonesia"
        return raw, area

    # Priority 3: any known region
    text_lower = text.lower()
    found = [r for r in INDONESIAN_REGIONS if r.lower() in text_lower]
    if not found and "indonesia" not in text_lower:
        return None, None
    area = found[0] if found else None
    parts = list(dict.fromkeys(found[:2]))
    if "indonesia" in text_lower and "Indonesia" not in parts:
        parts.append("Indonesia")
    return ", ".join(parts) if parts else None, area


def _infer_education(text: str) -> str | None:
    t = text.lower()
    # Check "Pendidikan: UniversityName" pattern common in Indonesian snippets
    if any(k in t for k in ["ph.d", "phd", "doktor", "s3", "doctoral"]):    return "S3"
    if any(k in t for k in ["magister", "master", "mba", "s2", "m.t.", "m.kom", "m.sc"]):  return "S2"
    if any(k in t for k in ["sarjana", "bachelor", "s.kom", "s.t.", "s.e.", "s1", "undergraduate"]): return "S1"
    if any(k in t for k in ["diploma", "d3", "d-3", "ahli madya", "d.3"]):  return "D3"
    return None


def _extract_skills(text: str) -> list[str]:
    """Extract skills from snippet — including from work history job titles."""
    text_lower = text.lower()
    found = [s.title() for s in SKILLS_KEYWORDS if s in text_lower]

    # Also extract from patterns like "Junior Java Developer", "iOS Engineer"
    job_tech = re.findall(
        r"\b(Python|Java(?:Script)?|TypeScript|React|Node\.?js|Go(?:lang)?|"
        r"Kotlin|PHP|Laravel|Vue|Angular|Flutter|iOS|Android|AWS|GCP|Azure|"
        r"Docker|Kubernetes|SQL|MongoDB|Redis|C\+\+|Swift|Rust)\b",
        text, re.IGNORECASE
    )
    for t in job_tech:
        if t.title() not in found:
            found.append(t.title())

    return list(dict.fromkeys(found))[:8]  # deduplicate, max 8


def _extract_connections(text: str) -> str | None:
    # Indonesian: "493 koneksi" or "500+ koneksi" or "500+ connections"
    m = re.search(r"(\d[\d,]*\+?)\s*(?:connections?|koneksi)", text, re.IGNORECASE)
    return m.group(0).strip() if m else None


def _extract_institution(text: str) -> str | None:
    # Indonesian snippets: "Pendidikan: Universitas XYZ"
    pendidikan = re.search(
        r"(?:Pendidikan|Education)\s*[:\·]\s*([\w\s]+?)(?:\s*[·\|·]|$)",
        text, re.IGNORECASE
    )
    if pendidikan:
        val = pendidikan.group(1).strip()
        if len(val) > 3:
            return val

    patterns = [
        r"Universitas [\w\s]{3,30}",
        r"Institut Teknologi [\w\s]{3,20}",
        r"University of [\w\s]{3,20}",
        r"Politeknik [\w\s]{3,20}",
        r"Sekolah Tinggi [\w\s]{3,25}",
        r"\b(ITB|Universitas Indonesia|UGM|ITS|UNDIP|UNPAD|BINUS|Gunadarma|"
        r"Telkom University|Duta Bangsa University|Tarumanagara|Brawijaya)\b",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(0).strip()
    return None


# ── Serper.dev search ──────────────────────────────────────────────────────────

async def _serper_search_profiles(
    client: httpx.AsyncClient,
    query: str,
    api_key: str,
    max_results: int = 10,
) -> list[LinkedInProfile]:
    """
    Call Serper.dev (Google Search JSON API) and extract LinkedIn profiles.
    Serper returns real Google results as structured JSON — no CAPTCHA.
    """
    profiles: list[LinkedInProfile] = []
    seen_urls: set[str] = set()

    try:
        resp = await client.post(
            SERPER_URL,
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json",
            },
            json={
                "q": query,
                "num": 10,
                "gl": "id",   # country: Indonesia
                "hl": "id",   # language: Indonesian
            },
            timeout=20,
        )

        if resp.status_code != 200:
            log.warning("serper_error", status=resp.status_code, body=resp.text[:200])
            return profiles

        data = resp.json()
        organic = data.get("organic", [])
        log.info("serper_search", query=query[:60], results=len(organic))

        for item in organic:
            if len(profiles) >= max_results:
                break

            url     = item.get("link", "")
            title   = item.get("title", "")
            snippet = item.get("snippet", "")

            if "linkedin.com/in/" not in url:
                continue

            linkedin_url = _normalise_linkedin_url(url)
            if not linkedin_url or linkedin_url in seen_urls:
                continue
            seen_urls.add(linkedin_url)

            name, job_title, company = _parse_title(title)
            if not name or len(name) < 2:
                continue

            # Google snippets for LinkedIn often contain:
            # "Jakarta, Indonesia · 500+ connections · Software Engineer at Tokopedia"
            full_text = f"{title} {snippet}"
            location, area          = _extract_location(full_text)
            education_level         = _infer_education(full_text)
            education_institution   = _extract_institution(full_text)
            skills                  = _extract_skills(full_text)
            connections             = _extract_connections(snippet)

            # Skip profiles explicitly located outside Indonesia
            # NULL location means undetermined — could still be Indonesian, so keep it
            if location and "indonesia" not in location.lower():
                log.debug("skipped_non_indonesian", name=name, location=location)
                continue

            # Extract company from snippet if not in title
            if not company and " at " in snippet:
                m = re.search(r"at\s+([A-Z][^\·\n·]{2,50})", snippet)
                if m:
                    company = m.group(1).strip().rstrip("·").strip()

            profiles.append(LinkedInProfile(
                name=name,
                job_title=job_title,
                company=company,
                location=location,
                area=area,
                linkedin_url=linkedin_url,
                education_level=education_level,
                education_institution=education_institution,
                skills=skills,
                connections=connections,
                summary=snippet[:300] if snippet else None,
                raw_data={
                    "title": title,
                    "snippet": snippet,
                    "search_engine": "serper",
                },
            ))

    except Exception as e:
        log.error("serper_search_failed", query=query[:60], error=str(e))

    return profiles


# ── SSE streaming generator ────────────────────────────────────────────────────

async def scrape_linkedin_cs_stream(
    search_queries: list[str] | None = None,
    max_profiles: int = 50,
) -> AsyncGenerator[dict, None]:
    from app.core.config import settings

    if not settings.SERPER_API_KEY:
        yield {"type": "error", "message": "SERPER_API_KEY not set. Get a free key at https://serper.dev"}
        return

    queries = search_queries or CS_SEARCH_QUERIES
    all_profiles: list[LinkedInProfile] = []
    seen_urls: set[str] = set()

    yield {"type": "start", "total_queries": len(queries), "max_profiles": max_profiles}

    async with httpx.AsyncClient() as client:
        for i, query in enumerate(queries):
            if len(all_profiles) >= max_profiles:
                break

            yield {"type": "query", "query": query, "index": i + 1, "total": len(queries)}

            batch = await _serper_search_profiles(
                client, query, settings.SERPER_API_KEY, max_results=10
            )
            new_count = 0

            for profile in batch:
                if len(all_profiles) >= max_profiles:
                    break
                key = profile.linkedin_url or profile.name
                if key in seen_urls:
                    continue
                seen_urls.add(key)
                all_profiles.append(profile)
                new_count += 1

                yield {
                    "type": "profile",
                    "profile": {
                        "name": profile.name,
                        "job_title": profile.job_title,
                        "company": profile.company,
                        "location": profile.location,
                        "area": profile.area,
                        "linkedin_url": profile.linkedin_url,
                        "education_level": profile.education_level,
                        "education_institution": profile.education_institution,
                        "skills": profile.skills,
                        "connections": profile.connections,
                        "summary": profile.summary,
                        "industry": profile.industry,
                        "source": profile.source,
                    },
                    "saved": len(all_profiles),
                    "total_queries": len(queries),
                }

            yield {
                "type": "query_done",
                "new_profiles": new_count,
                "total_so_far": len(all_profiles),
            }

            await asyncio.sleep(0.5)   # Serper is fast, light delay is enough

    yield {"type": "done", "total_saved": len(all_profiles)}


# ── Non-streaming (Celery) ─────────────────────────────────────────────────────

async def scrape_linkedin_cs_profiles(
    search_queries: list[str] | None = None,
    max_profiles: int = 50,
) -> list[dict]:
    profiles = []
    async for event in scrape_linkedin_cs_stream(search_queries, max_profiles):
        if event["type"] == "profile":
            profiles.append(event["profile"])
    return profiles


async def save_linkedin_profiles(
    profiles: list[dict],
    db,
    field: str | None = None,
) -> dict:
    """
    Upsert profiles into the DB, one transaction per profile.

    Returns:
        {"inserted": N, "updated": M, "failed": K, "duplicates": M, "total": len(profiles)}

    A profile whose linkedin_url already exists is reported as a duplicate and its
    row is updated with the fresh scraped data. Profiles without a linkedin_url
    are always inserted (they can't be deduplicated).
    """
    from sqlalchemy import text
    from app.core.database import AsyncSessionLocal

    inserted = 0
    updated = 0
    failed = 0
    for p in profiles:
        # Use a brand new session per insert so a failure never poisons the batch
        async with AsyncSessionLocal() as session:
            try:
                import uuid as _uuid
                result = await session.execute(
                    text("""
                        INSERT INTO leads (id, name, job_title, company, location, linkedin_url,
                                           education_level, industry, source, status, raw_data,
                                           headline, field, is_active, created_at, updated_at)
                        VALUES (:id, :name, :job_title, :company, :location, :linkedin_url,
                                :education_level, :industry, :source, 'new',
                                CAST(:raw_data AS jsonb), :headline, :field,
                                TRUE, NOW(), NOW())
                        ON CONFLICT (linkedin_url) WHERE linkedin_url IS NOT NULL DO UPDATE SET
                            name = EXCLUDED.name,
                            job_title = EXCLUDED.job_title,
                            company = EXCLUDED.company,
                            location = EXCLUDED.location,
                            education_level = EXCLUDED.education_level,
                            industry = EXCLUDED.industry,
                            raw_data = EXCLUDED.raw_data,
                            headline = EXCLUDED.headline,
                            field = COALESCE(EXCLUDED.field, leads.field),
                            updated_at = NOW()
                        RETURNING (xmax = 0) AS was_inserted
                    """),
                    {
                        "id": str(_uuid.uuid4()),
                        "name": p.get("name"),
                        "job_title": p.get("job_title"),
                        "company": p.get("company"),
                        "location": p.get("location"),
                        "linkedin_url": p.get("linkedin_url"),
                        "education_level": p.get("education_level"),
                        "industry": p.get("industry", "Computer Science / IT"),
                        "headline": p.get("headline"),
                        "field": field or p.get("field"),
                        "source": "linkedin",
                        "raw_data": json.dumps({
                            k: p.get(k) for k in
                            ["area", "education_institution", "skills",
                             "connections", "summary", "raw_data"]
                        }),
                    },
                )
                was_inserted = bool(result.scalar())
                if was_inserted:
                    inserted += 1
                else:
                    updated += 1
                await session.commit()
                log.info(
                    "lead_saved",
                    name=p.get("name"),
                    url=p.get("linkedin_url"),
                    inserted=was_inserted,
                )
            except Exception as e:
                await session.rollback()
                failed += 1
                log.warning("save_lead_failed", name=p.get("name"), error=str(e))

    log.info(
        "leads_saved_total",
        inserted=inserted,
        updated=updated,
        failed=failed,
        attempted=len(profiles),
    )
    return {
        "inserted": inserted,
        "updated": updated,
        "failed": failed,
        "duplicates": updated,
        "total": len(profiles),
    }
