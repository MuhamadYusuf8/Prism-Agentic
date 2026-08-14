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

## Fase 4 — Pipeline Otomatis & Reply Monitor (Selesai)

Pada fase ini, kami mengimplementasikan sistem otomasi penuh untuk monitoring balasan email, penanganan auto-response, dan penjadwalan follow-up secara periodik.

### 1. Celery Beat Periodic Schedule (`celery_app.py`)
- Menambahkan jadwal otomatis `periodic-follow-up-dispatch` yang berjalan setiap **6 jam** untuk memeriksa semua kampanye aktif dan mengirim follow-up kepada kandidat yang belum membalas.
- Konfigurasi Celery yang lebih robust: `task_acks_late=True` dan `worker_prefetch_multiplier=1` untuk memastikan task tidak hilang jika worker mati di tengah proses.

### 2. Celery Task Baru (`email_tasks.py`)
- Menambahkan task `run_periodic_follow_ups` yang di-trigger oleh Celery Beat.
- Task ini secara otomatis mengiterasi semua campaign aktif, memeriksa konfigurasi follow-up masing-masing, dan mendispatch follow-up emails melalui `email_service.send_follow_ups()`.

### 3. Upgrade Monitoring Routes (`monitoring.py`)
- Menambahkan **JWT authentication** ke semua endpoint monitoring yang sebelumnya tidak terlindungi.
- **`POST /process-reply`**: Endpoint baru untuk memproses balasan email secara manual (untuk testing pipeline tanpa IMAP inbox), termasuk klasifikasi intent, update status lead, dan pengiriman auto-response.
- **`GET /replies`**: Endpoint baru untuk melihat semua balasan di seluruh kampanye dengan filter berdasarkan *intent*, *sentiment*, dan status *auto-respond*.
- **`POST /trigger-follow-ups`**: Endpoint baru untuk memicu follow-up secara manual — bisa untuk satu kampanye spesifik atau semua kampanye aktif sekaligus (tanpa harus menunggu jadwal Celery Beat).

### 4. UI Pipeline & Conversation Thread
- **`LeadDetailPage.jsx`**: Menambahkan panel *Email Conversation Thread* di halaman detail kandidat untuk menampilkan riwayat lengkap email keluar dan balasan masuk secara kronologis.
- **`PipelinePage.jsx`**: Membuat halaman visualisasi Kanban Board interaktif yang memetakan kandidat ke dalam 5 tahapan rekrutmen (*New Leads*, *Contacted*, *Interested*, *Applied*, *Enrolled*).
- Menambahkan rute `/pipeline` di `App.jsx` dan menu navigasi **Pipeline** di sidebar.

## Fase 5 — RBAC & Manajemen Pengguna (Selesai)

Pada fase ini, kami mengimplementasikan sistem **Role-Based Access Control (RBAC)** secara penuh — dari lapisan *backend* hingga antarmuka admin — untuk memastikan setiap pengguna hanya dapat mengakses fitur yang sesuai dengan perannya.

### 1. Dependency Factory `require_role()` (`auth.py`)
- Mengubah arsitektur guard dari fungsi sederhana menjadi **dependency factory** yang fleksibel: `require_role(allowed_roles: list[str])`.
- Mendefinisikan 3 shortcut siap pakai: `require_admin`, `require_user_or_admin`, dan `require_recruiter_or_admin` agar mudah digunakan di seluruh router.
- Standarisasi 3 peran sistem: **`admin`** (akses penuh), **`recruiter`** (akses operasional), **`viewer`** (read-only).

### 2. Proteksi Endpoint Sensitif
Mengunci endpoint krusial yang sebelumnya bisa diakses siapa saja dengan `require_admin`:
- **Leads**: `DELETE /{id}` (hapus lead), `POST /cluster` (jalankan clustering AI)
- **Campaigns**: `DELETE /{id}` (hapus campaign), `POST /{id}/send` (kirim email massal)
- **Documents**: `POST /upload` (tambah dokumen ke knowledge base)
- **Settings**: Seluruh rute `GET`/`PUT` kini dilindungi di level router (`router = APIRouter(dependencies=[Depends(require_admin)])`)

### 3. Model Audit Log (`audit_log.py`) [BARU]
- Membuat tabel `audit_logs` di database untuk merekam jejak aktivitas sensitif.
- Setiap entri mencatat: `user_id` (pelaku), `action`, `resource_type`, `resource_id`, `details` (data sebelum/sesudah), `ip_address`, dan `created_at`.
- Audit log otomatis dicatat pada aksi: buat pengguna, hapus pengguna, ganti role, ganti password.

### 4. Endpoint Manajemen Pengguna (`users.py`) [BARU]
Endpoint CRUD lengkap di `/api/users` khusus untuk admin:
- **`GET /`** — List semua pengguna dengan **pagination** server-side.
- **`POST /`** — Buat pengguna baru dengan validasi kekuatan password (min. 8 karakter via Pydantic validator).
- **`PATCH /{user_id}`** — Update role atau status aktif (dengan proteksi agar admin tidak bisa menonaktifkan akunnya sendiri).
- **`DELETE /{user_id}`** — Hapus pengguna permanen (dengan proteksi agar admin tidak bisa menghapus akunnya sendiri).
- **`GET /me`** — Profil pengguna yang sedang login.
- **`PATCH /me/password`** — Ganti password sendiri.
- **`GET /audit-logs`** — Rekam jejak aktivitas sistem dengan pagination (admin only).

### 5. UI Manajemen Pengguna (`UserManagementPage.jsx`) [BARU]
Halaman administrasi pengguna yang komprehensif dengan 2 tab:
- **Tab "Daftar Pengguna"**: Tabel dengan avatar inisial, badge role berwarna, tombol toggle status aktif/nonaktif, dropdown ganti role *inline*, indikator "Saya" untuk akun sendiri, dan kolom *Last Login*.
- **Tab "Audit Log"**: Tabel rekam jejak aktivitas dengan kode aksi berwarna (`create`, `update`, `delete`), nama & email pelaku, IP address, dan timestamp.
- **Role Guard**: Halaman otomatis meng-*redirect* pengguna non-admin ke dashboard agar tidak bisa diakses langsung via URL.
- **Pagination**: Navigasi antar halaman untuk kedua tab.

### 6. Pembaruan Sidebar & Navigasi (`Sidebar.jsx`)
- Menambahkan seksi **"Admin"** tersembunyi di Sidebar yang hanya muncul jika pengguna yang login memiliki role `admin`.
- Menu **"User Management"** (ikon Shield ungu) hanya terlihat oleh admin.
- Badge role pengguna (`Admin` / `Recruiter` / `Viewer`) ditampilkan di panel profil bawah sidebar.

### 7. Perbaikan Bug Kritis (Audit Internal)
Setelah audit menyeluruh, 6 bug kritis ditemukan dan diperbaiki sebelum merge:
- ✅ **Field mismatch**: `hashed_password` → `password_hash` (sesuai model SQLAlchemy)
- ✅ **Field mismatch**: `last_login` → `last_login_at` (sesuai model SQLAlchemy)
- ✅ **Route conflict**: Memindahkan `/me` sebelum `/{user_id}` agar FastAPI tidak salah routing
- ✅ **AuditLog tidak dibuat**: Menambahkan import eksplisit di `main.py` agar `Base.metadata.create_all` mendaftarkan tabel `audit_logs`
- ✅ **Duplikasi endpoint**: Menghapus `GET /auth/users` yang duplikat dari `auth.py`
- ✅ **Role tidak konsisten**: Standarisasi ke `viewer/recruiter/admin` di seluruh kodebase
