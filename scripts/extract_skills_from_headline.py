"""
Extract tech skills from lead headline/job_title/summary and store them in the skills field.
Also runs syllabus matching to get confidence scores for the Relevance column.

Usage: python scripts/extract_skills_from_headline.py
"""
import sys, os, asyncio, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.stdout.reconfigure(encoding='utf-8')

from sqlalchemy import select, text
from app.core.database import AsyncSessionLocal
from app.models.lead import Lead
from app.services.syllabus_matcher import compute_syllabus_match

# Extended skill keywords to extract from text
SKILL_KEYWORDS = [
    # Languages
    "python", "java", "javascript", "typescript", "golang", "go", "kotlin",
    "swift", "rust", "c++", "c#", "csharp", "php", "ruby", "scala", "r",
    "matlab", "sql", "html", "css", "sass", "less",
    # Frontend
    "react", "vue", "angular", "svelte", "next.js", "nuxt", "jquery",
    "tailwind", "bootstrap", "redux", "webpack", "vite",
    # Backend
    "node.js", "nodejs", "node", "express", "django", "flask", "fastapi",
    "spring", "spring boot", "laravel", "rails", "asp.net", "graphql",
    "rest api", "grpc", "microservices",
    # Data & ML
    "machine learning", "deep learning", "tensorflow", "pytorch", "keras",
    "scikit-learn", "scikit", "pandas", "numpy", "data science", "data analysis",
    "data engineering", "data pipeline", "etl", "spark", "pyspark", "hadoop",
    "nlp", "computer vision", "opencv", "llm", "langchain", "openai", "gpt",
    "rag", "chatbot", "conversational ai",
    # Cloud & DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
    "terraform", "ansible", "jenkins", "ci/cd", "devops", "linux", "git",
    "github actions", "gitlab",
    # Database
    "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "bigquery", "snowflake", "sqlite", "mariadb",
    # Mobile
    "flutter", "android", "ios", "react native", "xamarin",
    # Other
    "blockchain", "web3", "cybersecurity", "security", "networking",
    "agile", "scrum", "product management", "ui/ux", "figma", "photoshop",
    "tableau", "power bi", "looker",
]

# Compile regexes
SKILL_REGEXES = [(re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE), kw) for kw in SKILL_KEYWORDS]


def extract_skills_from_text(text: str) -> list[str]:
    """Extract known skill keywords from any text."""
    if not text:
        return []
    found = set()
    text_lower = text.lower()
    for regex, kw in SKILL_REGEXES:
        if regex.search(text_lower):
            # Normalize casing
            found.add(kw.title() if kw.islower() else kw)
    return sorted(found, key=lambda x: x.lower())


async def main():
    # Ensure new DB columns exist (if not already from syllabus matching)
    async with AsyncSessionLocal() as session:
        for stmt in [
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS syllabus_confidence FLOAT",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS syllabus_scores JSONB",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS syllabus_matched_subjects JSONB",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS syllabus_top_match VARCHAR(255)",
        ]:
            try:
                await session.execute(text(stmt))
            except Exception:
                pass
        await session.commit()

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Lead))
        leads = result.scalars().all()
        print(f"Found {len(leads)} leads to process.\n")

        updated = 0
        for lead in leads:
            # Build text to extract skills from
            text_to_scan = " ".join(filter(None, [
                lead.headline or "",
                lead.job_title or "",
                lead.summary or "",
            ]))
            
            # Also include raw_data summary if available
            if lead.raw_data and isinstance(lead.raw_data, dict):
                raw_summary = lead.raw_data.get("summary", "")
                if raw_summary:
                    text_to_scan += " " + raw_summary
            
            extracted = extract_skills_from_text(text_to_scan)
            
            # Merge extracted skills with existing skills (if any)
            existing = lead.skills or []
            if isinstance(existing, list):
                merged = list(set(existing + extracted))
            else:
                merged = extracted
            
            lead.skills = merged if merged else None

            # Run syllabus matching (uses skills + headline + job_title)
            lead_dict = {
                "skills": lead.skills,
                "job_title": lead.job_title,
                "headline": lead.headline,
                "summary": lead.summary,
                "raw_data": lead.raw_data,
            }
            match = compute_syllabus_match(lead_dict)

            lead.syllabus_confidence = match["syllabus_confidence"]
            lead.syllabus_scores = match["syllabus_scores"]
            lead.syllabus_matched_subjects = match["syllabus_matched_subjects"]
            lead.syllabus_top_match = match["syllabus_top_match"]

            # Blend priority score with syllabus confidence
            old_score = lead.priority_score or 0
            lead.priority_score = round((old_score * 0.4 + match["syllabus_confidence"] * 0.6))

            updated += 1

            # Print sample results
            skills_str = ", ".join(merged[:5]) if merged else "none"
            conf = match["syllabus_confidence"]
            top = match["syllabus_top_match"] or "-"
            matched_list = match["syllabus_matched_subjects"]
            matched_str = ", ".join(matched_list[:3]) if matched_list else "none"
            
            if conf > 0 or merged:
                print(f"  [{lead.name:30s}] skills=[{skills_str:40s}] conf={conf:5.1f} top={top:30s} matched=[{matched_str}]")

        await session.commit()
        print(f"\n✅ Updated {updated} leads with extracted skills + syllabus scores.")


if __name__ == "__main__":
    asyncio.run(main())
