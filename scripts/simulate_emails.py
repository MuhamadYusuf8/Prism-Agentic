"""
Simulate email discovery — fill dummy emails for leads without one.
Email is generated from the scraped profile name (e.g. "Bagja Kurniawan"
→ "bagja.kurniawan@gmail.com").

Usage: python scripts/simulate_emails.py
"""
import sys, os, asyncio, re, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.stdout.reconfigure(encoding='utf-8')

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.lead import Lead

# Dummy email providers to simulate realistic-looking addresses
PROVIDERS = ["gmail.com", "yahoo.com", "outlook.com", "protonmail.com", "icloud.com"]


def name_to_email(name: str) -> str:
    """Generate a dummy email from a person's name."""
    name = name.strip()
    # Remove titles/suffixes like Dr., Ph.D, S.Kom, etc.
    name = re.sub(r"\b(dr|ph\.?d|m\.?sc|s\.?kom|s\.?t|s\.?e|ir|prof)\b\.?", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s+", " ", name).strip()

    # Take first + last meaningful word
    parts = [p for p in re.split(r"[\s\.\-]+", name) if p and re.search(r"[a-zA-Z]", p)]
    if not parts:
        return f"user{random.randint(1000, 9999)}@gmail.com"

    first = re.sub(r"[^a-zA-Z]", "", parts[0]).lower()
    last = re.sub(r"[^a-zA-Z]", "", parts[-1]).lower()

    if not first and not last:
        return f"user{random.randint(1000, 9999)}@gmail.com"

    provider = random.choice(PROVIDERS)

    # Randomize pattern for realism
    pattern = random.randint(0, 3)
    if pattern == 0 and first and last:
        local = f"{first}.{last}"
    elif pattern == 1 and first and last:
        local = f"{first}{last}"
    elif pattern == 2 and first:
        local = f"{first}"
    elif pattern == 3 and first and last:
        local = f"{first[0]}.{last}"
    else:
        local = first or last

    # Ensure uniqueness-ish
    local = re.sub(r"[^a-z0-9_.]", "", local)
    if len(local) < 3:
        local += f"{random.randint(10, 99)}"

    return f"{local}@{provider}"


async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Lead).where(Lead.email.is_(None)).order_by(Lead.created_at.desc())
        )
        leads = result.scalars().all()

        if not leads:
            print("All leads already have emails — nothing to fill.")
            return

        print(f"Filling dummy emails for {len(leads)} leads without email:\n")

        filled = 0
        for lead in leads:
            email = name_to_email(lead.name)
            lead.email = email
            print(f"  [{lead.name:35s}] → {email}")
            filled += 1

        await session.commit()
        print(f"\n✅ Filled {filled} dummy emails based on scraped profile names.")


if __name__ == "__main__":
    asyncio.run(main())
