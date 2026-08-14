"""
Cikarang Industrial Estate Scraper
Targets: MM2100, EJIP, KIIC, BIIE tenant directories
Uses httpx + BeautifulSoup (no JS rendering needed for these sites)
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
import structlog

log = structlog.get_logger()


@dataclass
class CompanyRecord:
    name: str
    estate: str
    industry: str | None = None
    location: str | None = None
    website: str | None = None
    source_url: str | None = None


# Each estate config: url + CSS selectors to try
ESTATE_CONFIGS = [
    {
        "estate": "MM2100",
        "url": "https://www.mm2100.com/tenant-list/",
        "selectors": [".tenant-name", ".company-name", "td:first-child", "li.tenant"],
    },
    {
        "estate": "EJIP",
        "url": "https://ejip.id/tenant/",
        "selectors": [".tenant-name", ".company-title", "h3", ".entry-title"],
    },
    {
        "estate": "KIIC",
        "url": "https://kiic.co.id/tenant/",
        "selectors": [".tenant-name", ".company", "td:first-child", ".title"],
    },
    {
        "estate": "BIIE",
        "url": "https://biie.co.id/tenant/",
        "selectors": [".tenant-name", ".company-name", "td:first-child"],
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
}


async def _scrape_estate(client: httpx.AsyncClient, config: dict) -> list[CompanyRecord]:
    """Scrape a single estate directory page."""
    estate = config["estate"]
    url = config["url"]
    records: list[CompanyRecord] = []

    try:
        response = await client.get(url, headers=HEADERS, timeout=20, follow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Try each selector until we find results
        for selector in config["selectors"]:
            elements = soup.select(selector)
            if elements:
                for el in elements:
                    name = el.get_text(strip=True)
                    if name and len(name) > 2:  # filter noise
                        records.append(
                            CompanyRecord(
                                name=name,
                                estate=estate,
                                source_url=url,
                            )
                        )
                if records:
                    log.info("estate_scraped", estate=estate, count=len(records), selector=selector)
                    break

        if not records:
            # Fallback: grab all table cells or list items with text > 5 chars
            fallback = soup.select("table td, ul li, ol li")
            for el in fallback:
                name = el.get_text(strip=True)
                if 5 < len(name) < 100 and not name.lower().startswith(("home", "about", "contact")):
                    records.append(CompanyRecord(name=name, estate=estate, source_url=url))
            log.info("estate_fallback", estate=estate, count=len(records))

    except httpx.HTTPStatusError as e:
        log.warning("http_error", estate=estate, status=e.response.status_code, url=url)
    except Exception as e:
        log.error("scrape_failed", estate=estate, error=str(e), url=url)

    return records


async def scrape_cikarang_companies() -> list[dict]:
    """Scrape all Cikarang industrial estate directories."""
    all_records: list[CompanyRecord] = []

    async with httpx.AsyncClient() as client:
        tasks = [_scrape_estate(client, cfg) for cfg in ESTATE_CONFIGS]
        results = await asyncio.gather(*tasks)
        for batch in results:
            all_records.extend(batch)

    # Deduplicate by name (case-insensitive)
    seen: set[str] = set()
    unique: list[CompanyRecord] = []
    for r in all_records:
        key = r.name.lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(r)

    log.info("cikarang_scrape_done", total=len(unique))
    return [asdict(r) for r in unique]


# ── Persist results to DB ─────────────────────────────────────────────────────

async def scrape_and_save(db) -> int:
    """Scrape Cikarang estates and upsert companies into the DB."""
    from sqlalchemy import text

    records = await scrape_cikarang_companies()
    saved = 0

    for r in records:
        await db.execute(
            text("""
                INSERT INTO companies (name, estate, location, raw_data)
                VALUES (:name, :estate, :location, :raw_data::jsonb)
                ON CONFLICT DO NOTHING
            """),
            {
                "name": r["name"],
                "estate": r["estate"],
                "location": "Cikarang",
                "raw_data": str(r),
            },
        )
        saved += 1

    await db.commit()
    log.info("companies_saved", count=saved)
    return saved
