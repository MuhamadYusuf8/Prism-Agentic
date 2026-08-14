import anthropic
from app.core.config import settings

client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

UNIVERSITY_CONTEXT = """
You are a recruitment assistant for President University, a leading international university
located in Cikarang, Bekasi, West Java, Indonesia.

Programs offered (Pascasarjana / Graduate):
- S2 Ilmu Komputer (Master of Computer Science) — fokus AI, Machine Learning, Data Science,
  Cybersecurity, dan Software Engineering. Durasi 4 semester (2 tahun).
- S2 Manajemen (Master of Management) — fokus Business Strategy, Leadership, dan Organizational
  Management. Tersedia konsentrasi: Marketing Management, Financial Management, HRM.
  Durasi 4 semester (2 tahun).
- S2 Teknik Industri (Master of Industrial Engineering) — fokus Operations Research,
  Supply Chain, Quality Management, dan Lean Manufacturing. Durasi 4 semester (2 tahun).
- MBA Eksekutif (Executive MBA) — program intensif untuk profesional berpengalaman,
  kelas malam dan weekend. Durasi 3 semester (18 bulan).

Key advantages:
- Kampus internasional dengan fasilitas world-class di Cikarang, Jawa Barat
- Kelas diselenggarakan pada hari Sabtu-Minggu untuk mengakomodasi profesional yang bekerja
- Pengajar berpengalaman dari industri dan akademisi internasional
- Jaringan alumni yang kuat di kawasan industri Bekasi-Cikarang-Karawang
- Akreditasi internasional

Tuition: approx IDR 18-30 juta/semester tergantung program.
Contact admissions: admisi@president.ac.id | +62-21-8910-9762
Website: https://www.president.ac.id
"""


async def draft_email(lead, campaign_context: str | None = None) -> dict:
    """
    Draft a personalized outreach email for a lead using Claude AI.
    Returns dict with keys: subject, body (HTML-ready).
    Falls back to a generic template if ANTHROPIC_API_KEY is not configured.
    """
    if not settings.ANTHROPIC_API_KEY:
        # Fallback template when API key not configured
        first_name = lead.name.split(" ")[0] if lead.name else "Bapak/Ibu"
        program = lead.recommended_program or "Program Pascasarjana"
        return {
            "subject": f"Undangan Bergabung di Program {program} — President University",
            "body": f"""<p>Yth. {lead.name or "Bapak/Ibu"},</p>
<p>Salam hangat dari President University!</p>
<p>Kami ingin mengundang Anda untuk bergabung dalam program <strong>{program}</strong>
di President University, universitas internasional yang berlokasi di Cikarang, Jawa Barat.</p>
<p>Program kami dirancang khusus untuk para profesional seperti Anda, dengan jadwal kelas
di akhir pekan sehingga tidak mengganggu aktivitas kerja sehari-hari.</p>
<p>Apakah Anda berminat untuk mengetahui lebih lanjut?
Kami dengan senang hati akan memberikan informasi lengkap.</p>
<p>Hormat kami,<br>Tim Rekrutmen<br>President University<br>
admisi@president.ac.id | +62-21-8910-9762</p>""",
        }

    profile_summary = (
        f"Nama: {lead.name}\n"
        f"Perusahaan: {lead.company or 'N/A'}\n"
        f"Jabatan: {lead.job_title or 'N/A'}\n"
        f"Tingkat Pendidikan: {lead.education_level or 'N/A'}\n"
        f"Industri: {lead.industry or 'N/A'}\n"
        f"Lokasi: {lead.location or 'N/A'}\n"
        f"Skills: {', '.join((lead.skills or [])[:5]) or 'N/A'}\n"
        f"Program yang Direkomendasikan: {lead.recommended_program or 'belum ditentukan'}"
    )

    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=[
            {
                "type": "text",
                "text": UNIVERSITY_CONTEXT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Buatkan email outreach yang hangat dan personal dalam Bahasa Indonesia untuk calon mahasiswa berikut.\n\n"
                    f"Profil kandidat:\n{profile_summary}\n\n"
                    f"Konteks tambahan: {campaign_context or 'Outreach umum untuk program pascasarjana'}\n\n"
                    f"Panduan:\n"
                    f"- Gunakan Bahasa Indonesia yang profesional namun hangat\n"
                    f"- Sebutkan nama kandidat di pembukaan\n"
                    f"- Hubungkan latar belakang kandidat dengan program yang relevan\n"
                    f"- Sertakan call-to-action yang jelas (reply email atau hubungi admisi)\n"
                    f"- Panjang email: 150-250 kata\n"
                    f"- Format body sebagai HTML sederhana (gunakan <p>, <strong>, <br>)\n\n"
                    f"Return JSON dengan keys: 'subject' (string) dan 'body' (HTML string)"
                ),
            }
        ],
    )

    import json, re
    text = response.content[0].text
    # Try to parse JSON from the response
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    # Fallback: use raw text as body
    return {
        "subject": f"Undangan Program Pascasarjana — President University",
        "body": text,
    }
