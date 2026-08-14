from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

router = APIRouter()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Upload a PDF/text document into the RAG knowledge base."""
    content = await file.read()
    # TODO: parse, chunk, embed, and store in documents table
    return {"filename": file.filename, "size": len(content), "status": "queued"}
