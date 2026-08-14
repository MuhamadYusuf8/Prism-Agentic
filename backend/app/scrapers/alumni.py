"""
Alumni Data Importer
Accepts CSV or Excel files, normalises columns, upserts into leads table.

Expected columns (flexible — we map common variants):
  name, email, phone, company, job_title, education_level, location, notes
"""

import io
import pandas as pd
from dataclasses import dataclass
import structlog

log = structlog.get_logger()

# Map of common column name variants → our canonical name
COLUMN_MAP = {
    # name
    "nama": "name", "full_name": "name", "fullname": "name", "nama_lengkap": "name",
    # email
    "email_address": "email", "surel": "email", "e-mail": "email",
    # phone
    "phone": "phone", "no_hp": "phone", "handphone": "phone", "no_telp": "phone",
    "telepon": "phone", "mobile": "phone",
    # company
    "perusahaan": "company", "employer": "company", "tempat_kerja": "company",
    # job title
    "jabatan": "job_title", "position": "job_title", "posisi": "job_title",
    "title": "job_title",
    # education
    "pendidikan": "education_level", "education": "education_level",
    "jenjang": "education_level", "degree": "education_level",
    # location
    "kota": "location", "city": "location", "domisili": "location",
    "alamat": "location", "address": "location",
    # notes
    "catatan": "notes", "keterangan": "notes", "remark": "notes",
}


@dataclass
class ParseResult:
    records: list[dict]
    total_rows: int
    skipped: int
    errors: list[str]


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase + strip column names and apply COLUMN_MAP."""
    df.columns = [c.lower().strip().replace(" ", "_").replace("-", "_") for c in df.columns]
    df = df.rename(columns=COLUMN_MAP)
    return df


def _clean_value(val) -> str | None:
    if pd.isna(val):
        return None
    s = str(val).strip()
    return s if s else None


def parse_alumni_file(content: bytes, filename: str) -> ParseResult:
    """Parse uploaded CSV/Excel into a list of normalised lead dicts."""
    errors: list[str] = []

    try:
        if filename.lower().endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content), dtype=str)
        elif filename.lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(content), dtype=str)
        else:
            return ParseResult([], 0, 0, [f"Unsupported file type: {filename}"])
    except Exception as e:
        return ParseResult([], 0, 0, [f"Failed to parse file: {e}"])

    df = _normalise_columns(df)
    total_rows = len(df)
    records: list[dict] = []
    skipped = 0

    for i, row in df.iterrows():
        name = _clean_value(row.get("name"))
        if not name:
            skipped += 1
            errors.append(f"Row {i + 2}: missing name, skipped")
            continue

        records.append({
            "name": name,
            "email": _clean_value(row.get("email")),
            "phone": _clean_value(row.get("phone")),
            "company": _clean_value(row.get("company")),
            "job_title": _clean_value(row.get("job_title")),
            "education_level": _clean_value(row.get("education_level")),
            "location": _clean_value(row.get("location")),
            "notes": _clean_value(row.get("notes")),
            "source": "alumni",
            "status": "new",
        })

    log.info("alumni_parsed", total=total_rows, valid=len(records), skipped=skipped)
    return ParseResult(records=records, total_rows=total_rows, skipped=skipped, errors=errors)


async def save_alumni_records(records: list[dict], db) -> int:
    """Upsert parsed alumni records into the leads table."""
    from sqlalchemy import text

    saved = 0
    for r in records:
        await db.execute(
            text("""
                INSERT INTO leads (name, email, phone, company, job_title,
                                   education_level, location, notes, source, status)
                VALUES (:name, :email, :phone, :company, :job_title,
                        :education_level, :location, :notes, :source, :status)
                ON CONFLICT (email) DO UPDATE SET
                    company        = EXCLUDED.company,
                    job_title      = EXCLUDED.job_title,
                    education_level= EXCLUDED.education_level,
                    location       = EXCLUDED.location,
                    updated_at     = NOW()
                WHERE leads.email IS NOT NULL
            """),
            r,
        )
        saved += 1

    await db.commit()
    log.info("alumni_saved", count=saved)
    return saved
