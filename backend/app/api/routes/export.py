"""
Export leads to CSV or Excel.
"""
import io
import pandas as pd
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import text

from app.core.database import AsyncSessionLocal

router = APIRouter()


async def _fetch_leads(source: str | None = None) -> list[dict]:
    async with AsyncSessionLocal() as db:
        query = """
            SELECT
                name, email, phone, job_title, company, industry,
                location, education_level, linkedin_url, source,
                priority_score, status, recommended_program,
                notes, created_at
            FROM leads
        """
        params = {}
        if source:
            query += " WHERE source = :source"
            params["source"] = source
        query += " ORDER BY created_at DESC"

        result = await db.execute(text(query), params)
        cols = result.keys()
        return [dict(zip(cols, row)) for row in result.fetchall()]


@router.get("/csv")
async def export_csv(source: str | None = Query(None)):
    """Download all leads as CSV."""
    rows = await _fetch_leads(source)
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["name", "email", "job_title", "company",
                                    "location", "source", "status"])

    # Format timestamps
    if "created_at" in df.columns:
        df["created_at"] = df["created_at"].astype(str)

    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)

    filename = f"leads_{source or 'all'}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/excel")
async def export_excel(source: str | None = Query(None)):
    """Download all leads as Excel (.xlsx)."""
    rows = await _fetch_leads(source)
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["name", "email", "job_title", "company",
                                    "location", "source", "status"])

    if "created_at" in df.columns:
        df["created_at"] = df["created_at"].astype(str)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Leads")

        # Auto-fit column widths
        ws = writer.sheets["Leads"]
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 50)

    buf.seek(0)
    filename = f"leads_{source or 'all'}.xlsx"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
