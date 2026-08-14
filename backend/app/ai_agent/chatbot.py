"""
RAG Chatbot — AI-powered admissions assistant for President University.

Features:
  - Persistent conversation history per session (in-memory store)
  - RAG context retrieval from document_chunks table
  - Claude claude-sonnet-4-6 streaming with conversation history
  - Graceful fallback when ANTHROPIC_API_KEY is not configured
"""

import json
from collections import deque
from datetime import datetime, timezone
from typing import AsyncGenerator

import anthropic
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

# ── Claude Client ──────────────────────────────────────────────────────────────

client = (
    anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    if settings.ANTHROPIC_API_KEY
    else None
)

# ── Conversation History (in-memory per session) ───────────────────────────────
# Maps session_id → deque of {"role": "user"|"assistant", "content": str}
# Max 20 messages per session to stay within token limits

_HISTORY: dict[str, deque] = {}
_MAX_HISTORY = 20


def get_history(session_id: str) -> list[dict]:
    return list(_HISTORY.get(session_id, []))


def add_to_history(session_id: str, role: str, content: str) -> None:
    if session_id not in _HISTORY:
        _HISTORY[session_id] = deque(maxlen=_MAX_HISTORY)
    _HISTORY[session_id].append({"role": role, "content": content})


def clear_history(session_id: str) -> None:
    _HISTORY.pop(session_id, None)


def list_sessions() -> list[str]:
    return list(_HISTORY.keys())


# ── System Prompt ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
Kamu adalah asisten penerimaan mahasiswa President University, universitas internasional
terkemuka yang berlokasi di Cikarang, Bekasi, Jawa Barat, Indonesia.

Tugasmu adalah membantu calon mahasiswa yang ingin melanjutkan studi ke jenjang S2 (Pascasarjana).

Program Pascasarjana yang tersedia:
1. S2 Ilmu Komputer (Master of Computer Science)
   - Konsentrasi: AI/Machine Learning, Data Science, Cybersecurity, Software Engineering
   - Durasi: 4 semester (2 tahun)
   - Silabus: Research Method, Machine Learning, Ubiquitous Computing, Big Data Analysis,
     Deep Learning, Business Intelligence, Voice & Image Recognition, Information Retrieval,
     Digital Forensics & Cyber Security, NLP & Conversational AI

2. S2 Manajemen (Master of Management)
   - Konsentrasi: Marketing Management, Financial Management, Human Resource Management
   - Durasi: 4 semester (2 tahun)

3. S2 Teknik Industri (Master of Industrial Engineering)
   - Konsentrasi: Operations Research, Supply Chain Management, Quality Management
   - Durasi: 4 semester (2 tahun)

4. MBA Eksekutif (Executive MBA)
   - Program intensif untuk profesional berpengalaman
   - Kelas malam dan weekend
   - Durasi: 3 semester (18 bulan)

Keunggulan President University:
- Kampus internasional dengan fasilitas world-class di Cikarang, Jawa Barat
- Kelas Sabtu-Minggu untuk para profesional yang bekerja
- Biaya kuliah: IDR 18-30 juta/semester tergantung program
- Dekat dengan kawasan industri Bekasi-Cikarang-Karawang (MM2100, EJIP, KIIC)

Informasi Admisi:
- Email: admisi@president.ac.id
- Telepon: +62-21-8910-9762
- Website: https://www.president.ac.id

Persyaratan Umum Pendaftaran S2:
- Lulusan S1 dari program terakreditasi (min. B)
- IPK minimal 2.75 (skala 4.00)
- Surat rekomendasi dari dosen/atasan
- Statement of Purpose
- Transkrip akademik dan ijazah

Cara menjawab:
- Selalu gunakan Bahasa Indonesia yang ramah, profesional, dan informatif
- Berikan informasi yang akurat berdasarkan konteks yang diberikan
- Jika tidak tahu jawaban spesifik, arahkan ke kontak admisi di atas
- Jangan memberikan informasi yang tidak pasti sebagai fakta
- Gunakan riwayat percakapan untuk memberikan jawaban yang kontekstual
"""


# ── RAG Context Retrieval ──────────────────────────────────────────────────────


async def _get_document_context(query: str, db: AsyncSession) -> str:
    """
    Retrieve relevant document chunks for RAG context.
    Uses LIKE-based text search — falls back gracefully if table missing.
    """
    try:
        # Search across multiple keywords from the query
        keywords = [w.lower() for w in query.split() if len(w) > 3][:5]
        if not keywords:
            return ""

        # Build a simple multi-keyword LIKE query
        conditions = " OR ".join([f"LOWER(content) LIKE :kw{i}" for i in range(len(keywords))])
        params = {f"kw{i}": f"%{kw}%" for i, kw in enumerate(keywords)}

        result = await db.execute(
            text(f"""
                SELECT content, source_file, chunk_index
                FROM document_chunks
                WHERE {conditions}
                ORDER BY chunk_index
                LIMIT 4
            """),
            params,
        )
        rows = result.fetchall()
        if rows:
            chunks = [row[0] for row in rows]
            return "\n\n---\n\n".join(chunks)
    except Exception:
        # Table doesn't exist yet or query error — skip RAG context
        pass
    return ""


# ── Chat Streaming ─────────────────────────────────────────────────────────────


async def stream_chat_response(
    session_id: str,
    message: str,
    db: AsyncSession,
) -> AsyncGenerator[str, None]:
    """
    Stream a chat response using Claude AI with conversation history and RAG.
    Falls back to a helpful static response if ANTHROPIC_API_KEY is not configured.
    """
    # Add user message to history FIRST
    add_to_history(session_id, "user", message)

    # Fallback when no API key configured
    if not client:
        fallback = (
            "Halo! Terima kasih sudah menghubungi **President University**. "
            "Untuk informasi lengkap tentang program S2 kami (Ilmu Komputer, Manajemen, "
            "Teknik Industri, MBA Eksekutif), silakan hubungi:\n\n"
            "📧 admisi@president.ac.id\n"
            "📞 +62-21-8910-9762\n"
            "🌐 https://www.president.ac.id\n\n"
            "Tim kami siap membantu Anda!"
        )
        add_to_history(session_id, "assistant", fallback)
        yield f"data: {json.dumps({'text': fallback})}\n\n"
        yield "data: [DONE]\n\n"
        return

    # Retrieve RAG context from uploaded documents
    doc_context = await _get_document_context(message, db)

    # Build system prompt with optional RAG context
    system = SYSTEM_PROMPT
    if doc_context:
        system += f"\n\n=== Informasi tambahan dari dokumen kampus ===\n{doc_context}\n==="

    # Build message list with conversation history
    history = get_history(session_id)
    # history already includes the latest user message we just added
    messages = history  # list of {"role": ..., "content": ...}

    # Stream response from Claude
    full_response = ""
    try:
        async with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system,
            messages=messages,
        ) as stream:
            async for chunk in stream.text_stream:
                full_response += chunk
                yield f"data: {json.dumps({'text': chunk})}\n\n"

        # Save assistant response to history
        add_to_history(session_id, "assistant", full_response)

    except Exception as e:
        error_msg = (
            "Maaf, terjadi kesalahan pada sistem AI saat ini. "
            "Silakan hubungi admisi@president.ac.id untuk bantuan langsung."
        )
        add_to_history(session_id, "assistant", error_msg)
        yield f"data: {json.dumps({'text': error_msg, 'error': str(e)})}\n\n"

    yield "data: [DONE]\n\n"
