# Changelog PRISM Agentic

## Fase 1 — Fondasi & Branding (Selesai)

Pada fase ini, kami merombak aplikasi agar secara resmi menggunakan identitas **President University** dan memperbaiki fungsi-fungsi inti yang masih berupa "kerangka kosong" (*placeholder*).

### 1. Rebranding Identitas AI (Chatbot & Email Drafter)
- Mengubah seluruh *prompt* sistem AI dari "Universitas XYZ" (placeholder) menjadi asisten resmi **President University** (Cikarang).
- Menetapkan 4 program Pascasarjana resmi yang ditawarkan: 
  - S2 Ilmu Komputer (Master of Computer Science)
  - S2 Manajemen (Master of Management)
  - S2 Teknik Industri (Master of Industrial Engineering)
  - MBA Eksekutif (Executive MBA)
- Menambahkan mekanisme *graceful fallback*: jika `ANTHROPIC_API_KEY` belum dikonfigurasi, aplikasi tidak akan *crash*, melainkan menggunakan template email dan balasan chat statis yang tetap fungsional.

### 2. Perbaikan Sistem Skoring / Profiling (`profiling.py`)
- Memperbaiki sistem *scoring* agar tidak bias hanya kepada kandidat IT/Computer Science.
- Setiap program kini memiliki bobot dan kata kunci (`keywords`) masing-masing.
- Kandidat dengan latar belakang bisnis, kepemimpinan, atau manajemen (*Business Strategy*, *Sales*, *Finance*) kini akan mendapat skor relevansi yang tinggi untuk program **S2 Manajemen** atau **MBA Eksekutif**.

### 3. Mengaktifkan Endpoint Kampanye Email (`campaigns.py`)
- Menghapus logika `not yet implemented` (yang sebelumnya mencegah email terkirim) dari endpoint `/send-test` dan `/send-follow-ups`.
- Endpoint tersebut kini dihubungkan secara fungsional ke `email_service.py` untuk mensimulasikan pengiriman email yang di-personalisasi berdasarkan profil setiap kandidat.

### 4. Penerapan Keamanan Rute (JWT Guard)
- Mengamankan rute-rute penting (`/api/leads`, `/api/campaigns`, `/api/analytics`) agar hanya dapat diakses oleh user yang sudah login (`Depends(get_current_user)`).
- Menambahkan proteksi tingkat lanjut (`Depends(require_admin)`) khusus untuk endpoint *LinkedIn Scraper* karena menggunakan resource API (*Serper/Scrapin*) yang sensitif dan terbatas.

### 5. Pembaruan Simulasi Data / Database Seeding (`seed_data.py`)
- Memperbarui skrip `seed_data.py` untuk menyuntikkan data *dummy* berupa **60 kandidat (leads)** dan **6 template kampanye** yang isinya sudah disesuaikan persis untuk penawaran program Pascasarjana President University.
- Mereset total database dan menjalankan ulang *seeding* agar tampilan visual dasbor UI terisi penuh dengan grafik interaksi (email dibuka, diklik, dibalas, dll.) secara realistis.
