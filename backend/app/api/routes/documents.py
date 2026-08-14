"""
Documents routes — RAG knowledge base management.

Supports uploading PDF and text files to populate the document_chunks table
used by the chatbot for RAG context retrieval.

Endpoints:
  POST /upload       — Upload and ingest a document into the knowledge base
  GET  /             — List all ingested documents
  DELETE /{doc_id}   — Delete a document and its chunks
  POST /seed         — Seed built-in campus documents (admin only)
"""

import hashlib
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user, require_admin
from app.models.user import User

router = APIRouter()

# ── Text chunking ─────────────────────────────────────────────────────────────

CHUNK_SIZE = 800       # characters per chunk
CHUNK_OVERLAP = 100    # overlap between chunks


def _chunk_text(text_content: str, source: str) -> list[dict]:
    """Split text into overlapping chunks for RAG ingestion."""
    chunks = []
    start = 0
    idx = 0
    while start < len(text_content):
        end = start + CHUNK_SIZE
        chunk = text_content[start:end].strip()
        if chunk:
            chunks.append({
                "id": str(uuid.uuid4()),
                "source_file": source,
                "chunk_index": idx,
                "content": chunk,
            })
            idx += 1
        start = end - CHUNK_OVERLAP
    return chunks


def _extract_text(filename: str, content: bytes) -> str:
    """Extract text from uploaded file. Supports .txt and basic .pdf."""
    if filename.endswith(".pdf"):
        try:
            import io
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(content))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(pages)
        except ImportError:
            # pypdf not installed, decode as UTF-8 and hope for the best
            return content.decode("utf-8", errors="ignore")
    else:
        return content.decode("utf-8", errors="ignore")


async def _ensure_chunks_table(db: AsyncSession) -> None:
    """Ensure document_chunks table exists (created by SQLAlchemy on startup,
    but this handles environments where table creation is deferred)."""
    await db.execute(text("""
        CREATE TABLE IF NOT EXISTS document_chunks (
            id TEXT PRIMARY KEY,
            source_file TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """))
    await db.commit()


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    Upload a PDF or TXT document into the RAG knowledge base.

    The document is chunked and stored in the document_chunks table.
    The chatbot will automatically include relevant chunks as context.
    """
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    allowed_ext = {".txt", ".pdf", ".md", ".csv"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_ext:
        raise HTTPException(
            400,
            f"Unsupported file type: {ext}. Allowed: {', '.join(allowed_ext)}"
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(400, "File is empty")

    if len(content) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(400, "File too large (max 10 MB)")

    # Extract text
    text_content = _extract_text(file.filename, content)
    if not text_content.strip():
        raise HTTPException(400, "Could not extract any text from the file")

    # Ensure table exists
    await _ensure_chunks_table(db)

    # Delete existing chunks for the same source file
    await db.execute(
        text("DELETE FROM document_chunks WHERE source_file = :src"),
        {"src": file.filename},
    )

    # Chunk and insert
    chunks = _chunk_text(text_content, file.filename)
    for chunk in chunks:
        await db.execute(
            text("""
                INSERT INTO document_chunks (id, source_file, chunk_index, content)
                VALUES (:id, :source_file, :chunk_index, :content)
                ON CONFLICT (id) DO NOTHING
            """),
            chunk,
        )

    await db.commit()

    return {
        "filename": file.filename,
        "size_bytes": len(content),
        "characters": len(text_content),
        "chunks_created": len(chunks),
        "status": "ingested",
        "message": f"Successfully ingested {len(chunks)} chunks from '{file.filename}'. The chatbot can now use this document as context.",
    }


@router.get("/")
async def list_documents(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all documents in the RAG knowledge base."""
    await _ensure_chunks_table(db)
    result = await db.execute(text("""
        SELECT source_file, COUNT(*) as chunk_count, MIN(created_at) as uploaded_at
        FROM document_chunks
        GROUP BY source_file
        ORDER BY uploaded_at DESC
    """))
    rows = result.fetchall()
    return {
        "total_documents": len(rows),
        "documents": [
            {
                "source_file": row[0],
                "chunk_count": row[1],
                "uploaded_at": row[2].isoformat() if row[2] else None,
            }
            for row in rows
        ],
    }


@router.delete("/{source_file:path}")
async def delete_document(
    source_file: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Delete a document and all its chunks from the knowledge base (admin only)."""
    await _ensure_chunks_table(db)
    result = await db.execute(
        text("DELETE FROM document_chunks WHERE source_file = :src RETURNING id"),
        {"src": source_file},
    )
    deleted = len(result.fetchall())
    await db.commit()

    if deleted == 0:
        raise HTTPException(404, f"Document '{source_file}' not found in knowledge base")

    return {
        "source_file": source_file,
        "chunks_deleted": deleted,
        "status": "deleted",
    }


@router.post("/seed")
async def seed_campus_documents(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    Seed the built-in campus documents (Syllabus.txt, etc.) into the knowledge base.
    Run this once after initial setup to enable chatbot RAG context.
    """
    await _ensure_chunks_table(db)

    # Built-in campus knowledge to seed
    built_in_docs = {
        "Syllabus_S2_Ilmu_Komputer.txt": """
President University - Program S2 Ilmu Komputer (Master of Computer Science)

Silabus Mata Kuliah:
1. Research Method - Metodologi penelitian ilmiah, literature review, dan penulisan karya ilmiah
2. Machine Learning - Supervised learning, unsupervised learning, neural networks, dan evaluasi model
3. Ubiquitous Computing - Internet of Things, mobile computing, dan pervasive systems
4. Big Data Analysis - Hadoop, Spark, data warehousing, dan teknik analisis data besar
5. Fundamental of Deep Learning - Arsitektur CNN, RNN, Transformer, dan transfer learning
6. Business Intelligence and Analytics - Dashboard, OLAP, data visualization, dan decision support
7. Voice & Image Recognition - Computer vision, speech processing, dan pattern recognition
8. Information Retrieval - Search engine, indexing, ranking algorithms, dan information extraction
9. Digital Forensics & Advanced Cyber Security - Network security, ethical hacking, dan forensik digital
10. NLP & Conversational AI - Natural language processing, chatbot development, dan sentiment analysis

Durasi: 4 semester (2 tahun)
Konsentrasi: AI/Machine Learning, Data Science, Cybersecurity, Software Engineering
        """,
        "Profil_President_University.txt": """
President University adalah universitas internasional terkemuka yang berlokasi di Cikarang, 
Bekasi, Jawa Barat, Indonesia. Didirikan untuk mendukung kebutuhan sumber daya manusia 
kawasan industri terbesar di Asia Tenggara (EJIP, MM2100, KIIC, BIIE).

Keunggulan:
- Kampus bertaraf internasional dengan fasilitas world-class
- Program Pascasarjana tersedia dengan kelas Sabtu-Minggu (ramah pekerja profesional)
- Biaya kuliah: IDR 18-30 juta per semester tergantung program
- Dekat dengan kawasan industri Bekasi-Cikarang-Karawang

Program Pascasarjana (S2):
1. S2 Ilmu Komputer (Master of Computer Science)
2. S2 Manajemen (Master of Management)
3. S2 Teknik Industri (Master of Industrial Engineering)
4. MBA Eksekutif (Executive MBA) - khusus profesional berpengalaman

Persyaratan Umum Pendaftaran S2:
- Lulusan S1 terakreditasi (min. akreditasi B)
- IPK minimal 2.75 dari skala 4.00
- Surat rekomendasi
- Statement of Purpose
- Transkrip akademik dan ijazah

Kontak Admisi:
- Email: admisi@president.ac.id
- Telepon: +62-21-8910-9762
- Website: https://www.president.ac.id
- Alamat: Jl. Ki Hajar Dewantara, Kota Jababeka, Cikarang, Bekasi 17550
        """,
    }

    total_chunks = 0
    seeded_docs = []

    for filename, content in built_in_docs.items():
        # Delete existing chunks for this doc
        await db.execute(
            text("DELETE FROM document_chunks WHERE source_file = :src"),
            {"src": filename},
        )
        chunks = _chunk_text(content.strip(), filename)
        for chunk in chunks:
            await db.execute(
                text("""
                    INSERT INTO document_chunks (id, source_file, chunk_index, content)
                    VALUES (:id, :source_file, :chunk_index, :content)
                    ON CONFLICT (id) DO NOTHING
                """),
                chunk,
            )
        total_chunks += len(chunks)
        seeded_docs.append({"filename": filename, "chunks": len(chunks)})

    await db.commit()

    return {
        "status": "seeded",
        "total_chunks": total_chunks,
        "documents": seeded_docs,
        "message": "Campus knowledge base seeded successfully. Chatbot RAG context is now active.",
    }
