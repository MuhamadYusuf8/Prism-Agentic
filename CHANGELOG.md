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

## Fase 2 — Email Campaign (Selesai)

Pada fase ini, kami mengimplementasikan sistem antrean latar belakang (background queue) untuk pengiriman email agar prosesnya tidak membuat aplikasi membeku (freeze), serta merombak halaman antarmuka agar bisa menampilkan metrik email secara *real-time*.

### 1. Implementasi Pekerja Latar Belakang Celery (`email_tasks.py`)
- Menerapkan arsitektur _Asynchronous Task Queue_ menggunakan Celery untuk memproses pengiriman email massal di luar siklus HTTP request/response.
- Mengimplementasikan 3 task utama: `dispatch_campaign` (broadcast massal), `send_bulk_outreach` (pengiriman ke beberapa kandidat terpilih), dan `dispatch_follow_ups` (email otomatis jika tidak ada balasan).

### 2. Penambahan Endpoint API Real-Time (`campaigns.py`)
- **`/send`**: Menjadi trigger utama untuk mengirim kampanye yang langsung dialihkan ke _Celery Worker_.
- **`/logs`**: Menyediakan data riwayat pengiriman per email secara detail dan terpaginasi (status, jumlah *open*, *click*, waktu dikirim).
- **`/replies`**: Menarik data seluruh balasan dari kandidat, lengkap dengan analisis *Intent* (contoh: *Interested*, *Request Info*) dan sentimen.

### 3. Perombakan Total UI CampaignDetailPage (`CampaignDetailPage.jsx`)
- Mengubah struktur halaman menjadi navigasi berbasis *Tab* modern (Overview, Email Logs, Replies, Template Preview).
- **Statistik Dinamis**: Menampilkan persentase metrik performa (*Open rate, Click rate, Reply rate*) langsung dari pembacaan database log.
- **Daftar Logs & Balasan**: Menampilkan status interaksi menggunakan badge warna-warni yang memudahkan pembacaan, di mana detail setiap aktivitas terlihat secara visual.
- **Tombol "Kirim Campaign" Fungsional**: Terhubung ke endpoint Celery sehingga tombol memberikan *loading state* tanpa membekukan keseluruhan aplikasi.
- **HTML Preview**: Memungkinkan pengelola melihat secara visual bagaimana desain email akan muncul di kotak masuk penerima.

## Fase 3 — RAG Chatbot Assistant (Selesai)

Pada fase ini, kami mengubah chatbot dari sebuah asisten AI sederhana menjadi sistem berpengetahuan (RAG) yang memiliki memori percakapan dan dapat belajar dari dokumen yang diunggah.

### 1. Conversation History per Session (`chatbot.py`)
- Mengimplementasikan penyimpanan riwayat percakapan berbasis *in-memory* (per `session_id`) menggunakan `deque` dengan batas 20 pesan.
- Claude AI sekarang menerima seluruh riwayat percakapan sehingga bisa memberikan jawaban yang kontekstual dan koheren di setiap sesi.

### 2. RAG Multi-Keyword & Knowledge Base (`documents.py`)
- Mengubah pencarian RAG dari *single-keyword* menjadi *multi-keyword* sehingga lebih banyak dokumen relevan yang ditemukan.
- Mengimplementasikan endpoint `POST /api/documents/upload` yang benar-benar berfungsi: bisa menerima file PDF/TXT, memecahnya menjadi *chunks*, dan menyimpannya ke database.
- Menambahkan endpoint `POST /api/documents/seed` untuk memasukkan data bawaan kampus (Silabus S2 Ilmu Komputer & Profil President University) ke *knowledge base* chatbot secara instan.
- Melakukan *seeding* knowledge base sehingga chatbot langsung aktif dengan RAG konteks kampus yang relevan.

### 3. Endpoint Baru Chatbot (`chatbot.py`)
- `GET /chatbot/history/{session_id}` — Mengambil riwayat percakapan suatu sesi.
- `DELETE /chatbot/history/{session_id}` — Menghapus riwayat percakapan (mulai ulang sesi).
- `GET /chatbot/sessions` — Melihat semua sesi aktif (khusus admin).

### 4. UI Chatbot Premium (`ChatbotPage.jsx`)
- Tampilan *chat bubble* modern dengan avatar berbeda untuk pengguna dan AI.
- *Streaming* respons AI secara *real-time* (karakter per karakter muncul secara bertahap).
- *Typing indicator* animasi *bounce* saat AI sedang memproses.
- *Quick reply chips* untuk pertanyaan yang paling umum ditanyakan.
- *Markdown rendering*: respons AI yang mengandung **tebal**, *miring*, atau daftar akan tampil dengan format yang tepat.
- Panel **Knowledge Base** terintegrasi untuk upload dokumen baru atau seeding data kampus langsung dari UI.
- Tombol **Bersihkan** untuk memulai sesi percakapan baru dan menghapus riwayat.
- Menu **AI Chatbot** ditambahkan ke navigasi *Sidebar* utama aplikasi.

