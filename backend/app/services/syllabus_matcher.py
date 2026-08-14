"""
Syllabus Matching Engine — matches scraped lead data (skills, headline, job title,
summary) against the Master's program syllabus subjects and computes a confidence
score for each subject.

Syllabus subjects (10):
  1. Research Method
  2. Machine Learning
  3. Ubiquitous Computing
  4. Big Data Analysis
  5. Fundamental of Deep Learning
  6. Business Intelligence and Analytics
  7. Voice & Image Recognition
  8. Information Retrieval
  9. Digital Forensics & Advanced Cyber Security
  10. NLP & Conversational AI

Confidence Formula:
  For each subject, keyword matches are detected in:
    - skills[]         (weight: 50%)
    - job_title        (weight: 20%)
    - headline         (weight: 15%)
    - summary          (weight: 15%)

  subject_score = (skill_match_count * 50 + title_match * 20 +
                   headline_match * 15 + summary_match * 15) / total_keywords_for_subject

  overall_confidence = average of all 10 subject_scores (0–100)

  matched_subjects = subjects with subject_score >= 15 (meaningful match)
"""

import re
import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


# ── Syllabus Subjects → Keyword Mappings ──────────────────────────────────────

SYLLABUS = [
    {
        "id": 1,
        "name": "Research Method",
        "keywords": [
            "research", "methodology", "research method", "scientific method",
            "quantitative", "qualitative", "statistical analysis", "experiment",
            "hypothesis", "data collection", "survey", "case study",
        ],
    },
    {
        "id": 2,
        "name": "Machine Learning",
        "keywords": [
            "machine learning", "ml", "supervised", "unsupervised",
            "classification", "regression", "clustering", "scikit",
            "xgboost", "random forest", "decision tree", "svm",
            "dimensionality reduction", "feature engineering",
        ],
    },
    {
        "id": 3,
        "name": "Ubiquitous Computing",
        "keywords": [
            "ubiquitous", "pervasive", "iot", "internet of things",
            "embedded", "sensor", "wearable", "smart device",
            "cyber-physical", "cps", "context-aware", "ambient",
        ],
    },
    {
        "id": 4,
        "name": "Big Data Analysis",
        "keywords": [
            "big data", "spark", "hadoop", "data analysis",
            "data pipeline", "etl", "data warehouse", "data lake",
            "data engineering", "data platform", "hive", "kafka",
            "data streaming", "pyspark", "databricks", "snowflake",
            "bigquery",
        ],
    },
    {
        "id": 5,
        "name": "Fundamental of Deep Learning",
        "keywords": [
            "deep learning", "neural network", "cnn", "rnn", "lstm",
            "transformer", "keras", "pytorch", "tensorflow",
            "attention mechanism", "gan", "autoencoder", "backpropagation",
            "reinforcement learning",
        ],
    },
    {
        "id": 6,
        "name": "Business Intelligence and Analytics",
        "keywords": [
            "business intelligence", "bi", "analytics", "tableau",
            "power bi", "looker", "data visualization", "dashboard",
            "kpi", "reporting", "business analyst", "data analytics",
            "olap", "decision support",
        ],
    },
    {
        "id": 7,
        "name": "Voice & Image Recognition",
        "keywords": [
            "voice recognition", "image recognition", "computer vision",
            "speech", "object detection", "opencv", "facial recognition",
            "image classification", "object tracking", "ocr",
            "speech-to-text", "text-to-speech", "image processing",
            "yolo", "segmentation",
        ],
    },
    {
        "id": 8,
        "name": "Information Retrieval",
        "keywords": [
            "information retrieval", "search engine", "elasticsearch",
            "solr", "indexing", "ranking", "query", "recommendation",
            "information extraction", "web scraping", "crawling",
            "semantic search", "knowledge graph",
        ],
    },
    {
        "id": 9,
        "name": "Digital Forensics & Advanced Cyber Security",
        "keywords": [
            "cyber security", "cybersecurity", "digital forensics",
            "network security", "penetration", "ethical hacking",
            "vulnerability", "incident response", "malware",
            "encryption", "cryptography", "security engineer",
            "application security", "cloud security", "soc",
            "forensics",
        ],
    },
    {
        "id": 10,
        "name": "NLP & Conversational AI",
        "keywords": [
            "nlp", "natural language", "conversational ai", "chatbot",
            "llm", "gpt", "bert", "langchain", "openai",
            "text classification", "sentiment", "named entity",
            "tokenization", "word embedding", "text mining",
            "question answering", "rag",
        ],
    },
]

# Pre-compile keyword regexes for performance
for subject in SYLLABUS:
    subject["_regexes"] = [re.compile(re.escape(kw), re.IGNORECASE) for kw in subject["keywords"]]


def _text_from_lead(lead: dict) -> dict[str, str]:
    """Extract searchable text fields from a lead dict."""
    # Skills from raw_data.skills or the skills field
    skills_list = lead.get("skills") or []
    if not skills_list:
        raw = lead.get("raw_data") or {}
        skills_list = raw.get("skills") or []

    skills_text = " ".join(skills_list) if skills_list else ""

    return {
        "skills": skills_text,
        "job_title": lead.get("job_title") or "",
        "headline": lead.get("headline") or "",
        "summary": lead.get("summary") or "",
    }


def _count_matches(text: str, regexes: list[re.Pattern]) -> int:
    """Count how many distinct keywords from a subject appear in the text."""
    if not text:
        return 0
    text_lower = text.lower()
    count = 0
    for regex in regexes:
        if regex.search(text_lower):
            count += 1
    return count


def compute_syllabus_match(lead: dict) -> dict:
    """
    Compute syllabus matching scores for a single lead.

    Returns:
    {
        "syllabus_scores": {
            "Research Method": 45,
            "Machine Learning": 80,
            ...
        },
        "syllabus_confidence": 52.3,       # average across all 10 subjects
        "syllabus_matched_subjects": ["Machine Learning", "Big Data Analysis"],
        "syllabus_top_match": "Machine Learning",
        "syllabus_breakdown": { ... }       # per-subject detailed breakdown
    }
    """
    fields = _text_from_lead(lead)
    total_possible_keywords = sum(len(s["keywords"]) for s in SYLLABUS)

    scores = {}
    breakdowns = {}

    for subject in SYLLABUS:
        # Count matches in each field
        skill_matches = _count_matches(fields["skills"], subject["_regexes"])
        title_matches = _count_matches(fields["job_title"], subject["_regexes"])
        headline_matches = _count_matches(fields["headline"], subject["_regexes"])
        summary_matches = _count_matches(fields["summary"], subject["_regexes"])

        total_subject_keywords = len(subject["keywords"])
        if total_subject_keywords == 0:
            subject_score = 0
        else:
            # Weighted score (max 100 per subject)
            weighted = (
                min(skill_matches, 3) / 3 * 50     # skills: 50% weight, capped at 3 matches
                + min(title_matches, 2) / 2 * 20   # job_title: 20% weight, capped at 2
                + min(headline_matches, 2) / 2 * 15  # headline: 15% weight
                + min(summary_matches, 3) / 3 * 15   # summary: 15% weight, capped at 3
            )
            subject_score = round(min(weighted, 100), 1)

        scores[subject["name"]] = subject_score
        breakdowns[subject["name"]] = {
            "skill_matches": skill_matches,
            "title_matches": title_matches,
            "headline_matches": headline_matches,
            "summary_matches": summary_matches,
            "weighted_score": subject_score,
        }

    # Overall confidence = average of all subject scores
    overall = round(sum(scores.values()) / len(scores), 1) if scores else 0

    # Subjects with score >= 15 are considered "matched"
    matched = [name for name, score in scores.items() if score >= 15]
    matched.sort(key=lambda n: scores[n], reverse=True)

    # Top match
    top_match = matched[0] if matched else None

    return {
        "syllabus_confidence": overall,
        "syllabus_scores": scores,
        "syllabus_matched_subjects": matched,
        "syllabus_top_match": top_match,
        "syllabus_breakdown": breakdowns,
    }


async def run_syllabus_matching_on_all_leads(db: AsyncSession) -> dict:
    """Run syllabus matching on all leads and update their records."""
    from sqlalchemy import select
    from app.models.lead import Lead

    result = await db.execute(select(Lead))
    leads = result.scalars().all()

    updated = 0
    for lead in leads:
        lead_dict = {
            "skills": lead.skills,
            "job_title": lead.job_title,
            "headline": lead.headline,
            "summary": lead.summary,
            "raw_data": lead.raw_data,
        }
        match_result = compute_syllabus_match(lead_dict)

        lead.syllabus_confidence = match_result["syllabus_confidence"]
        lead.syllabus_scores = match_result["syllabus_scores"]
        lead.syllabus_matched_subjects = match_result["syllabus_matched_subjects"]
        lead.syllabus_top_match = match_result["syllabus_top_match"]

        # Update the priority_score to factor in syllabus match
        # Keep existing priority_score logic but blend with syllabus confidence
        old_score = lead.priority_score or 0
        lead.priority_score = round((old_score * 0.4 + match_result["syllabus_confidence"] * 0.6))

        updated += 1

    await db.commit()
    return {"total_leads": len(leads), "updated": updated}
