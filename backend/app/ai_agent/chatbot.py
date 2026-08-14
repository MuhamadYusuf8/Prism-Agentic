import json
import anthropic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.core.config import settings

client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None

SYSTEM_PROMPT = """
Kamu adalah asisten penerimaan mahasiswa President University, universitas internasional
terkemuka yang berlokasi di Cikarang, Bekasi, Jawa Barat, Indonesia.

Tugasmu adalah membantu calon mahasiswa yang ingin melanjutkan studi ke jenjang S2 (Pascasarjana).

Program Pascasarjana yang tersedia:
1. S2 Ilmu Komputer (Master of Computer Science)
   - Konsentrasi: AI/Machine Learning, Data Science, Cybersecurity, Software Engineering
   - Durasi: 4 semester (2 tahun)

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

Kontak admisi:
- Email: admisi@president.ac.id
- Telepon: +62-21-8910-9762
- Website: https://www.president.ac.id

Cara menjawab:
- Selalu gunakan Bahasa Indonesia yang ramah, profesional, dan informatif
- Berikan informasi yang akurat berdasarkan konteks yang diberikan
- Jika tidak tahu jawaban spesifik, arahkan ke kontak admisi di atas
- Jangan memberikan informasi yang tidak pasti sebagai fakta
"""


async def _get_document_context(query: str, db: AsyncSession) -> str:
    """
    Retrieve relevant document chunks for RAG context.
    Falls back gracefully if document_chunks table doesn't exist yet.
    """
    try:
        result = await db.execute(
            text(
                """
                SELECT content FROM document_chunks
                WHERE LOWER(content) LIKE :query
                ORDER BY chunk_index
                LIMIT 3
                """
            ),
            {"query": f"%{query[:50].lower()}%"},
        )
        chunks = result.scalars().all()
        if chunks:
            return "\n\n---\n\n".join(chunks)
    except Exception:
        # Table doesn't exist yet — skip RAG context
        pass
    return ""


async def stream_chat_response(session_id: str, message: str, db: AsyncSession):
    """
    Stream a chat response using Claude AI with RAG context.
    Falls back to a simple response if ANTHROPIC_API_KEY is not configured.
    """
    # Fallback when no API key configured
    if not client:
        fallback = (
            "Halo! Terima kasih sudah menghubungi President University. "
            "Untuk informasi lengkap tentang program S2 kami, silakan hubungi "
            "admisi@president.ac.id atau +62-21-8910-9762. "
            "Tim kami siap membantu Anda!"
        )
        yield f"data: {json.dumps({'text': fallback})}\n\n"
        yield "data: [DONE]\n\n"
        return

    # Retrieve RAG context from uploaded documents
    doc_context = await _get_document_context(message, db)

    # Build system prompt with optional RAG context
    system = SYSTEM_PROMPT
    if doc_context:
        system += f"\n\n=== Informasi tambahan dari dokumen kampus ===\n{doc_context}\n==="

    # Stream response from Claude
    async with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=800,
        system=system,
        messages=[{"role": "user", "content": message}],
    ) as stream:
        async for chunk in stream.text_stream:
            yield f"data: {json.dumps({'text': chunk})}\n\n"

    yield "data: [DONE]\n\n"

