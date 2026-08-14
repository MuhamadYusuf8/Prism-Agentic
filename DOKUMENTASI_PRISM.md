# 📘 DOKUMENTASI LENGKAP PRISM
### President Recruitment Intelligence System & Matcher
> Platform rekrutmen mahasiswa berbasis AI untuk **President University**  
> Versi: 2.0.0 | Bahasa: Python (FastAPI) + JavaScript (React/Vite)

---

## 📌 Daftar Isi

1. [Gambaran Umum & Tujuan](#1-gambaran-umum--tujuan)
2. [Masalah yang Diselesaikan](#2-masalah-yang-diselesaikan)
3. [Alur Rekrutmen (End-to-End Flow)](#3-alur-rekrutmen-end-to-end-flow)
4. [Arsitektur Sistem](#4-arsitektur-sistem)
5. [Tech Stack](#5-tech-stack)
6. [Struktur Direktori](#6-struktur-direktori)
7. [Komponen Backend (Detail)](#7-komponen-backend-detail)
8. [Komponen Frontend (Detail)](#8-komponen-frontend-detail)
9. [Database & Model Data](#9-database--model-data)
10. [Fitur Unggulan](#10-fitur-unggulan)
11. [API Endpoints](#11-api-endpoints)
12. [Konfigurasi Lingkungan (.env)](#12-konfigurasi-lingkungan-env)
13. [Docker Services](#13-docker-services)
14. [Cara Menjalankan](#14-cara-menjalankan)
15. [Kredensial Default](#15-kredensial-default)

---

## 1. Gambaran Umum & Tujuan

**PRISM** (*President Recruitment Intelligence System & Matcher*) adalah platform rekrutmen mahasiswa tingkat pascasarjana (S2) yang sepenuhnya otomatis dan berbasis kecerdasan buatan (AI). Platform ini dibangun khusus untuk **President University** dengan tujuan mengotomatiskan seluruh proses rekrutmen — mulai dari menemukan calon mahasiswa, menganalisis profil mereka, hingga mengirimkan email personal yang cerdas, dan memantau respons mereka.

### Tujuan Utama

| # | Tujuan | Penjelasan |
|---|--------|------------|
| 1 | **Otomatisasi Pencarian Calon Mahasiswa** | Menemukan calon mahasiswa S2 potensial secara otomatis melalui LinkedIn dan sumber lainnya |
| 2 | **Analisis Profil dengan AI** | Menilai relevansi setiap calon dengan program studi yang ditawarkan secara otomatis |
| 3 | **Pencocokan Kurikulum** | Mencocokkan background kandidat dengan 10 mata kuliah program S2 |
| 4 | **Komunikasi Personal & Massal** | Mengirimkan email yang dipersonalisasi ke ratusan calon mahasiswa |
| 5 | **Pemantauan & Follow-up Otomatis** | Memantau balasan email dan melakukan tindak lanjut otomatis sesuai tahap percakapan |
| 6 | **Analitik Rekrutmen** | Menyediakan dashboard lengkap dengan KPI dan statistik pipeline rekrutmen |

**Scope Program:** Hanya untuk calon mahasiswa **S2 (Master's)** — bukan S1 atau S3.

---

## 2. Masalah yang Diselesaikan

Sebelum PRISM, proses rekrutmen mahasiswa S2 dilakukan secara manual:
- Tim harus mencari calon satu per satu di LinkedIn
- Menilai kesesuaian latar belakang secara subjektif
- Membuat dan mengirim email satu per satu
- Tidak ada sistem untuk memantau apakah email dibuka, diklik, atau dibalas
- Tidak ada alur percakapan terstruktur untuk menindaklanjuti respons

**PRISM memecahkan semua masalah ini** dengan pipeline otomatis yang berjalan dari ujung ke ujung tanpa intervensi manual yang berulang.

---

## 3. Alur Rekrutmen (End-to-End Flow)

Berikut adalah alur lengkap bagaimana sistem PRISM bekerja:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PIPELINE REKRUTMEN PRISM                             │
└─────────────────────────────────────────────────────────────────────────┘

TAHAP 1: PENEMUAN CALON (Lead Sourcing)
────────────────────────────────────────
  [Serper API / Google Search]
       │
       ▼
  Menemukan URL profil LinkedIn → Disimpan sebagai "Lead" baru (status: NEW)
       │
  [LinkedIn Detail Scraper]
       │
       ▼
  Mengambil detail lengkap: nama, headline, skills, pendidikan, pengalaman
  (status: SCRAPED)
       │
  [Alumni CSV/Excel Import] ──── (alternatif sumber data)
       │
  [Manual Entry via API] ──────── (alternatif sumber data)


TAHAP 2: ANALISIS & PROFILING (AI Scoring)
────────────────────────────────────────────
       ▼
  [Syllabus Matching Engine]
  • Mencocokkan skills, headline, job title, summary dengan 10 mata kuliah S2
  • Menghasilkan: syllabus_confidence (0-100), syllabus_matched_subjects
  
       ▼
  [AI Profiling Engine]
  • CS Relevance Score (0-100): apakah background IT-related?
  • Education Analysis: deteksi level S2/S3/professional
  • Program Matching: cocokkan dengan program MSCS, AI/ML, Data Science, dll
  • Weighted Scoring:
      Academic Score   (35%) ──┐
      Engagement Score (20%) ──┤── Priority Score Final (0-100)
      Program Fit      (30%) ──┤
      Data Completeness(15%) ──┘
  • Auto-tagging, Data Quality Assessment (HIGH/MEDIUM/LOW)
  (status: PROFILED)


TAHAP 3: PENGELOMPOKAN (Clustering)
─────────────────────────────────────
       ▼
  [Clustering Service]
  • Mengelompokkan lead berdasarkan profile_type (master/phd/professional)
  • Memperbarui karakteristik cluster: skill umum, lokasi, rata-rata skor
  (status: CLUSTERED)


TAHAP 4: KAMPANYE EMAIL (Campaign Management)
───────────────────────────────────────────────
       ▼
  [Campaign Manager]
  • Tim membuat kampanye dengan target spesifik (cluster/profile_type)
  • Template email dibuat dengan variabel personalisasi:
      {{name}}, {{firstName}}, {{program}}, {{university}}, {{skills}}
       
       ▼
  [AI Email Drafter (Claude API)]
  • Jika diaktifkan: Claude menghasilkan draft email personal per lead
  
       ▼
  [Email Service + Resend API]
  • Personalisasi template untuk setiap lead
  • Tambahkan tracking pixel (open tracking)
  • Rewrite links (click tracking)
  • Kirim via Resend API
  (status lead: CONTACTED)


TAHAP 5: MONITORING & FOLLOW-UP
─────────────────────────────────
       ▼
  [Email Open/Click Tracking]
  • Pixel 1x1 pixel invisible mencatat kapan email dibuka
  • Link tracking mencatat kapan link diklik
  
       ▼
  [IMAP Reply Monitor]
  • Memantau inbox secara berkala untuk balasan email
  • Klasifikasi intent: positif (minat) / negatif (tidak tertarik)
  
       ▼
  [9-Stage Conversation Pipeline]
  Melacak perjalanan calon mahasiswa:
  
  1. INITIAL_INQUIRY     → Pertama kali menghubungi
  2. INFO_REQUESTED      → Meminta informasi program
  3. INFO_RECEIVED       → Sudah menerima informasi
  4. APPLICATION_SUBMITTED → Mendaftar
  5. DOCUMENTS_REVIEWED  → Dokumen diperiksa
  6. INTERVIEW_SCHEDULED → Interview dijadwalkan
  7. INTERVIEW_COMPLETED → Interview selesai
  8. OFFER_MADE          → Penawaran diberikan
  9. LOA_ISSUED          → LoA (Letter of Acceptance) diterbitkan
  
  [Auto-Response Engine]
  • Kirim balasan otomatis sesuai tahap percakapan
  (status lead: INTERESTED → APPLIED → ENROLLED)


TAHAP 6: ANALITIK & PELAPORAN
────────────────────────────────
       ▼
  [Analytics Dashboard]
  • KPI: total leads, open rate, reply rate, conversion rate
  • Funnel visualization
  • Source breakdown (LinkedIn vs CSV vs Manual)
  • Trend rekrutmen dari waktu ke waktu
  • Top prospects berdasarkan skor prioritas
```

### Status Lead (Lifecycle)

```
NEW → SCRAPED → PROFILED → CLUSTERED → CONTACTED → INTERESTED → APPLIED → ENROLLED
                                                  ↘ NOT_INTERESTED
                                                  ↘ UNSUBSCRIBED
```

---

## 4. Arsitektur Sistem

```
┌──────────────────────────────────────────────────────────────────┐
│                        BROWSER / CLIENT                          │
│                    React 18 + Vite (Port 3000)                   │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTP / WebSocket
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                        NGINX (Port 80)                           │
│                     Reverse Proxy / Load Balancer                │
└────────────────────────────┬─────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
┌─────────────────────────┐   ┌─────────────────────────────────┐
│   FastAPI Backend       │   │   Static Assets / Frontend      │
│   (Port 8000)           │   │   (dilayani Nginx)              │
│                         │   └─────────────────────────────────┘
│  ┌───────────────────┐  │
│  │   API Routes      │  │
│  │  ─ /api/leads     │  │
│  │  ─ /api/campaigns │  │◄──── Celery Worker (background tasks)
│  │  ─ /api/analytics │  │         │
│  │  ─ /api/scraper   │  │         ▼
│  │  ─ /api/email     │  │   ┌──────────────┐
│  │  ─ /api/chatbot   │  │   │   Redis      │
│  │  ─ /ws (WebSocket)│  │   │   (Port 6379)│
│  └─────────┬─────────┘  │   │   Task Queue │
│            │             │   └──────────────┘
│  ┌─────────▼─────────┐  │
│  │   Services Layer   │  │
│  │  ─ profiling.py   │  │
│  │  ─ clustering.py  │  │
│  │  ─ email_service  │  │
│  │  ─ syllabus_match │  │
│  │  ─ reply_monitor  │  │
│  │  ─ conv_pipeline  │  │
│  └─────────┬─────────┘  │
│            │             │
│  ┌─────────▼─────────┐  │
│  │   AI Agents       │  │
│  │  ─ Claude API     │  │
│  │  ─ Resend API     │  │
│  │  ─ Serper API     │  │
│  └─────────┬─────────┘  │
└────────────┼────────────┘
             │
             ▼
┌──────────────────────────┐
│   PostgreSQL + pgvector  │
│   (Port 5432)            │
│   Database utama PRISM   │
└──────────────────────────┘
             │
             ▼
┌──────────────────────────┐
│   Adminer (Port 8080)    │
│   Database Admin UI      │
└──────────────────────────┘
```

### Pola Komunikasi Real-time

- **REST API** — untuk semua operasi CRUD standar
- **SSE (Server-Sent Events)** — untuk streaming hasil scraping LinkedIn secara real-time ke browser
- **WebSocket (`/ws`)** — untuk update status kampanye email secara live
- **Celery + Redis** — untuk eksekusi tugas berat di background (scraping, email batch)

---

## 5. Tech Stack

| Layer | Teknologi | Versi | Fungsi |
|-------|-----------|-------|--------|
| **Frontend** | React | 18 | UI Framework |
| **Build Tool** | Vite | Latest | Dev server & bundler |
| **Styling** | Tailwind CSS | 3 | Utility-first CSS |
| **Backend** | FastAPI | 0.115 | REST API & WebSocket |
| **Runtime** | Python | 3.12 | Bahasa backend |
| **ORM** | SQLAlchemy | 2.0 | Database abstraction (async) |
| **Database** | PostgreSQL | 16 | Database relasional utama |
| **Extension DB** | pgvector | - | Penyimpanan vektor AI embedding |
| **Task Queue** | Celery | 5.4 | Background job processing |
| **Message Broker** | Redis | 7 | Broker untuk Celery |
| **AI / LLM** | Claude (Anthropic) | - | Email drafting & RAG chatbot |
| **Email Sending** | Resend | - | Layanan pengiriman email |
| **LinkedIn Search** | Serper.dev | - | Google Search API untuk profil LinkedIn |
| **Web Scraping** | httpx + BeautifulSoup | - | Scraping detail profil LinkedIn |
| **Proxy** | Nginx | Alpine | Reverse proxy & load balancer |
| **Container** | Docker + Docker Compose | - | Containerisasi semua services |

---

## 6. Struktur Direktori

```
prism-main/
├── 📁 backend/                        # FastAPI Backend
│   ├── Dockerfile
│   ├── requirements.txt               # 60+ Python dependencies
│   └── 📁 app/
│       ├── main.py                    # Entry point FastAPI, route registration, WebSocket
│       ├── seed_data.py               # Script untuk mengisi data dummy (60 leads, 6 campaigns)
│       ├── 📁 api/routes/             # HTTP Route Handlers
│       │   ├── analytics.py           # Endpoint statistik & KPI
│       │   ├── auth.py                # Login, register, JWT
│       │   ├── campaigns.py           # CRUD kampanye email
│       │   ├── chatbot.py             # RAG chatbot endpoint (SSE)
│       │   ├── documents.py           # Upload dokumen ke RAG
│       │   ├── email.py               # AI draft & send email
│       │   ├── export.py              # Export leads ke CSV/Excel
│       │   ├── leads.py               # CRUD leads, profiling, clustering
│       │   ├── monitoring.py          # Monitoring email (inbox scanning)
│       │   ├── scraper.py             # LinkedIn scraping (SSE streaming)
│       │   ├── settings.py            # App settings CRUD
│       │   └── tracking.py            # Tracking pixel open/click
│       ├── 📁 core/                   # Konfigurasi & Infrastruktur
│       │   ├── config.py              # Settings dari .env
│       │   ├── database.py            # AsyncSession PostgreSQL setup
│       │   ├── auth.py                # JWT token generation/validation
│       │   ├── bootstrap.py           # Auto-create admin user saat startup
│       │   └── celery_app.py          # Konfigurasi Celery
│       ├── 📁 models/                 # SQLAlchemy ORM Models
│       │   ├── lead.py                # Model Lead (tabel utama)
│       │   ├── campaign.py            # Model Campaign email
│       │   ├── email_log.py           # Model log pengiriman email
│       │   ├── reply.py               # Model balasan email masuk
│       │   ├── cluster.py             # Model kelompok lead
│       │   └── user.py                # Model pengguna sistem
│       ├── 📁 services/               # Business Logic Layer
│       │   ├── profiling.py           # Engine penilaian & profiling lead
│       │   ├── syllabus_matcher.py    # Engine pencocokan kurikulum S2
│       │   ├── clustering.py          # Engine pengelompokan lead
│       │   ├── email_service.py       # Kirim email dengan tracking
│       │   ├── conversation_pipeline.py # Pipeline 9 tahap rekrutmen
│       │   ├── reply_monitor.py       # Monitor inbox IMAP
│       │   ├── data_processor.py      # Cleaning & deduplication data
│       │   ├── monitoring.py          # Email monitoring service
│       │   └── interaction_monitor.py # Pantau interaksi lead
│       ├── 📁 scrapers/               # Web Scraping Modules
│       │   ├── linkedin.py            # Phase 1: Serper API → temukan URL profil
│       │   ├── linkedin_detail.py     # Phase 2: Scrape detail profil LinkedIn
│       │   ├── alumni.py              # Import alumni dari CSV/Excel
│       │   └── cikarang.py            # Scrape direktori perusahaan Cikarang
│       ├── 📁 email_agent/            # AI Email Agent
│       │   ├── drafter.py             # Claude API → generate draft email
│       │   └── sender.py              # Resend API → kirim email
│       ├── 📁 ai_agent/               # AI Chatbot
│       │   └── chatbot.py             # RAG chatbot berbasis Claude
│       └── 📁 workers/                # Celery Background Tasks
│           ├── email_tasks.py         # Task async untuk pengiriman email
│           └── scrape_tasks.py        # Task async untuk scraping
│
├── 📁 frontend/                       # React + Vite Frontend
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js                 # Proxy: /api → http://localhost:8000
│   └── 📁 src/
│       ├── App.jsx                    # Router utama + route protection
│       ├── main.jsx                   # Entry point React
│       ├── index.css                  # Global styles
│       ├── 📁 pages/                  # Halaman-halaman aplikasi
│       │   ├── UnifiedDashboardPage.jsx  # Dashboard utama (10 seksi)
│       │   ├── DashboardPage.jsx         # KPI & pipeline stats
│       │   ├── AllLeadsPage.jsx          # Tabel semua leads
│       │   ├── LeadDetailPage.jsx        # Profil detail seorang lead
│       │   ├── AnalyticsPage.jsx         # Distribusi profil & analitik
│       │   ├── EmailPage.jsx             # Manajemen kampanye email
│       │   ├── EmailMonitoringPage.jsx   # Monitoring inbox & balasan
│       │   ├── CampaignDetailPage.jsx    # Detail kampanye + log email
│       │   ├── LinkedInSourcingPage.jsx  # Scraping LinkedIn (real-time SSE)
│       │   ├── CampusIntakePage.jsx      # Import CSV/Excel alumni
│       │   ├── ClustersPage.jsx          # Visualisasi cluster lead
│       │   ├── SettingsPage.jsx          # Pengaturan aplikasi
│       │   ├── LoginPage.jsx             # Halaman login JWT
│       │   └── RegisterPage.jsx          # Halaman registrasi
│       ├── 📁 components/             # Komponen UI yang digunakan ulang
│       │   └── ui/
│       │       └── Sidebar.jsx        # Sidebar navigasi
│       └── 📁 lib/                    # Utilitas & Context
│           ├── api.js                 # Axios API client + interceptor JWT
│           └── auth-context.jsx       # React Context untuk autentikasi
│
├── 📁 nginx/
│   └── nginx.conf                     # Konfigurasi reverse proxy
├── 📁 scripts/
│   └── init.sql                       # SQL inisialisasi database
├── 📁 dataset/                        # Data syllabus & referensi
├── 📁 plans/                          # Dokumen perencanaan arsitektur
├── docker-compose.yml                 # Orkestrasi 8 Docker services
├── .env                               # Environment variables (API keys, DB)
├── .env.example                       # Template konfigurasi
├── README.md                          # Dokumentasi bahasa Inggris
└── RUNNING_LOCALLY.md                 # Panduan menjalankan lokal
```

---

## 7. Komponen Backend (Detail)

### 7.1 Profiling Engine (`services/profiling.py`)

Engine ini menilai setiap calon mahasiswa secara otomatis menggunakan dua metode gabungan:

**A. CS Relevance Scoring**
```
Cara kerja:
- Mengumpulkan teks dari: headline, summary, job_title, skills, education, experience
- Mencocokkan dengan 36+ kata kunci teknologi (python, machine learning, docker, dll)
- Setiap keyword yang cocok = +8 poin (maks 100)
- is_cs_related = True jika skor ≥ 30
```

**B. Weighted Priority Score**
```
Academic Score     (35%) = education_level + CS relevance + jumlah skills
Engagement Score   (20%) = ada LinkedIn URL + headline + summary + phone + experience
Program Fit        (30%) = CS relevance + best program match confidence
Data Completeness  (15%) = persentase field yang terisi dari 13 field penting

Priority Score = (Academic × 0.35) + (Engagement × 0.20) + 
                 (Program Fit × 0.30) + (Completeness × 0.15)
```

**C. Program Matching**
```
Mencocokkan profil dengan program yang tersedia:
- Master of Computer Science (MSCS)
- Master in AI/ML
- Master in Data Science
- Master in Cybersecurity
- MS in Software Engineering
- Master of Business Administration (MBA)
- Master of Information Technology
- Master of Management
```

---

### 7.2 Syllabus Matching Engine (`services/syllabus_matcher.py`)

Engine ini mencocokkan latar belakang calon mahasiswa dengan 10 mata kuliah S2 President University:

| # | Mata Kuliah | Contoh Keyword |
|---|-------------|----------------|
| 1 | Research Method | research, methodology, quantitative, hypothesis |
| 2 | Machine Learning | ml, supervised, classification, scikit, xgboost |
| 3 | Ubiquitous Computing | iot, internet of things, embedded, sensor, wearable |
| 4 | Big Data Analysis | spark, hadoop, etl, data warehouse, kafka |
| 5 | Fundamental of Deep Learning | neural network, cnn, pytorch, tensorflow, lstm |
| 6 | Business Intelligence & Analytics | tableau, power bi, kpi, data visualization |
| 7 | Voice & Image Recognition | computer vision, opencv, speech, yolo, ocr |
| 8 | Information Retrieval | elasticsearch, indexing, semantic search, crawling |
| 9 | Digital Forensics & Cyber Security | penetration, malware, encryption, forensics |
| 10 | NLP & Conversational AI | nlp, llm, gpt, bert, langchain, chatbot |

**Formula Skor Per Mata Kuliah:**
```
subject_score = (skill_matches/3 × 50%) + 
                (title_matches/2 × 20%) + 
                (headline_matches/2 × 15%) + 
                (summary_matches/3 × 15%)

overall_confidence = rata-rata semua 10 skor (0-100)
matched_subjects = mata kuliah dengan skor ≥ 15
```

---

### 7.3 LinkedIn Scraper (2-Phase)

**Phase 1 — Discovery (Serper API)**
```
Input: query pencarian (misal: "site:linkedin.com/in S2 Computer Science Indonesia")
Proses: Serper.dev → Google Search → Ekstrak URL profil LinkedIn dari snippets
Output: List URL profil LinkedIn → disimpan sebagai lead baru (status: NEW)
```

**Phase 2 — Enrichment (LinkedIn Session)**
```
Input: LinkedIn profile URL + cookie "li_at" (session LinkedIn yang login)
Proses: HTTP request dengan session cookie → Parse HTML halaman profil
Output: Nama, headline, summary, skills, pendidikan, pengalaman kerja, lokasi
Status lead berubah menjadi: SCRAPED
```

**Streaming SSE:** Hasil scraping dikirimkan secara real-time ke browser via Server-Sent Events sehingga tim bisa melihat progress langsung tanpa menunggu selesai.

---

### 7.4 Email Service (`services/email_service.py`)

**Personalisasi Template:**
```
Variabel yang didukung:
{{name}}        → Nama lengkap lead
{{firstName}}   → Nama depan
{{program}}     → Program yang direkomendasikan
{{university}}  → "President University"
{{location}}    → Lokasi lead
{{skills}}      → 5 skill pertama dari profil
{{headline}}    → Headline LinkedIn
```

**Tracking Email:**
```
Open Tracking  → Pixel 1x1px tersembunyi di body email
                 → Saat dibuka: GET /api/tracking/open/{tracking_id}
Click Tracking → Semua link di-rewrite ke /api/tracking/click/{tracking_id}?url=...
                 → Saat diklik: redirect ke URL asli + catat klik
```

**Sending:** Via Resend API. Jika Resend tidak dikonfigurasi, email hanya dicatat di database (mode "logged").

---

### 7.5 Conversation Pipeline (`services/conversation_pipeline.py`)

Pipeline 9 tahap ini melacak perjalanan rekrutmen setiap calon mahasiswa:

```
Tahap 1: INITIAL_INQUIRY     │ Lead pertama kali masuk / dihubungi
Tahap 2: INFO_REQUESTED      │ Lead meminta informasi program
Tahap 3: INFO_RECEIVED       │ Lead sudah menerima informasi  
Tahap 4: APPLICATION_SUBMITTED│ Lead mendaftar secara resmi
Tahap 5: DOCUMENTS_REVIEWED  │ Dokumen aplikasi diperiksa tim
Tahap 6: INTERVIEW_SCHEDULED │ Jadwal wawancara dibuat
Tahap 7: INTERVIEW_COMPLETED │ Wawancara selesai dilakukan
Tahap 8: OFFER_MADE          │ Tawaran penerimaan diberikan
Tahap 9: LOA_ISSUED          │ Letter of Acceptance diterbitkan
```

Setiap tahap memiliki template respons otomatis yang dikirimkan ke calon mahasiswa.

---

### 7.6 Background Tasks (Celery)

Celery digunakan untuk menjalankan tugas berat di background agar API tidak blocking:

| Task | File | Fungsi |
|------|------|--------|
| Scraping batch | `scrape_tasks.py` | Scrape banyak profil LinkedIn secara async |
| Email batch | `email_tasks.py` | Kirim email ke banyak lead secara async |
| Celery Beat | Scheduler | Jalankan monitoring inbox IMAP secara berkala |

---

### 7.7 RAG Chatbot (`ai_agent/chatbot.py`)

Chatbot berbasis **Claude API** dengan **Retrieval-Augmented Generation (RAG)**:
- Tim bisa upload dokumen PDF/teks ke knowledge base
- Calon mahasiswa bisa bertanya dalam Bahasa Indonesia
- Chatbot mengambil informasi relevan dari dokumen yang diupload
- Respons distream secara real-time via SSE

---

## 8. Komponen Frontend (Detail)

### Halaman & Fungsi

| Route | Halaman | Fungsi |
|-------|---------|--------|
| `/` | **Unified Dashboard** | Dashboard all-in-one dengan 10 seksi scrollable |
| `/dashboard` | Dashboard | KPI cards, pipeline funnel, source breakdown, trend chart |
| `/leads` | All Leads | Tabel semua lead dengan search, filter status, filter source, pagination |
| `/leads/:id` | Lead Detail | Profil lengkap lead: skor, syllabus match, email history, replies, timeline |
| `/analytics` | Analytics | Distribusi profil, education breakdown, top prospects, email stats |
| `/email` | Email Campaigns | List kampanye, buat kampanye baru, aktivasi/pause |
| `/email/:id` | Campaign Detail | Statistik kampanye, log email per-lead, monitor replies |
| `/email-monitoring` | Email Monitoring | Pantau inbox, lihat balasan, klasifikasi intent |
| `/linkedin` | LinkedIn Sourcing | Form scraping LinkedIn dengan progress real-time (SSE) |
| `/settings` | Settings | Konfigurasi SMTP, LinkedIn cookie, monitoring interval |
| `/login` | Login | Form autentikasi JWT |
| `/register` | Register | Form registrasi pengguna baru |

### Sistem Autentikasi

- **JWT Token** disimpan di `localStorage`
- **Axios Interceptor** otomatis menyisipkan `Authorization: Bearer <token>` di setiap request
- **Protected Routes** — semua halaman selain `/login` memerlukan autentikasi
- **Auth Context** — state autentikasi dikelola di React Context global

---

## 9. Database & Model Data

### Skema Tabel Utama

#### Tabel `leads` — Data Calon Mahasiswa
```
id                       UUID (Primary Key)
name                     VARCHAR(255) - Nama lengkap
email                    VARCHAR(255) - Unique, index
phone                    VARCHAR(50)
linkedin_url             VARCHAR(512) - Unique index
headline                 TEXT - Headline LinkedIn
summary                  TEXT - Ringkasan profil LinkedIn
company                  VARCHAR(255)
job_title                VARCHAR(255)
industry                 VARCHAR(255)
location                 VARCHAR(255)
skills                   JSON - Array of strings
education_level          VARCHAR(100) - SMA/D3/S1/S2/S3
education                JSON - Array of education entries
experience               JSON - Array of experience entries
source                   VARCHAR(100) - linkedin_serper/csv_import/manual/etc
status                   VARCHAR(50)  - new/scraped/profiled/clustered/contacted/...
field                    VARCHAR(50)  - computer_science/management/law
profile_score            FLOAT   - Skor profil (0-100)
profile_type             VARCHAR(50)  - master/phd/professional/unknown
priority_score           INTEGER - Skor prioritas final
is_computer_science_related BOOLEAN
matched_programs         JSON - Array of {name, confidence, type}
recommended_program      VARCHAR(255)
tags                     JSON - Auto-generated tags
data_quality             VARCHAR(20)  - high/medium/low
syllabus_confidence      FLOAT   - Confidence matching syllabus (0-100)
syllabus_scores          JSON - {subject: score} untuk 10 mata kuliah
syllabus_matched_subjects JSON - Array nama mata kuliah yang match
syllabus_top_match       VARCHAR(255) - Mata kuliah dengan skor tertinggi
cluster_id               UUID - Foreign key ke clusters
communication            JSON - History email: [{sent_at, opened, clicked, replied}]
profile_embedding        JSON - Vector embedding AI
raw_data                 JSON - Raw scraped data
notes                    TEXT
created_at, updated_at, profiled_at, last_contacted_at  TIMESTAMP
```

#### Tabel `campaigns` — Kampanye Email
```
id                  UUID (Primary Key)
name                VARCHAR(255)
description         TEXT
target_type         VARCHAR(50) - bachelor/master/all
target_clusters     JSON - Array of cluster IDs
email_template      JSON - {subject, body (HTML), variables}
follow_up           JSON - {enabled, delay_days, max_follow_ups, template}
schedule            JSON - {start_date, end_date, timezone, send_window}
stats               JSON - {total_targeted, emails_sent, emails_opened, emails_clicked, ...}
status              VARCHAR(50) - draft/active/paused/completed/cancelled
created_by          UUID - FK ke users
created_at, updated_at, launched_at, completed_at  TIMESTAMP
```

#### Tabel `email_logs` — Log Pengiriman Email
```
id                  UUID (Primary Key)
campaign_id         UUID - FK ke campaigns
lead_id             UUID - FK ke leads
recipient_email     VARCHAR(255)
recipient_name      VARCHAR(255)
subject             VARCHAR(500)
body                TEXT - HTML email (termasuk tracking pixel)
tracking_id         UUID - Unique per email untuk tracking
status              VARCHAR(50) - pending/sent/failed/logged
is_follow_up        BOOLEAN
follow_up_number    INTEGER
opened              BOOLEAN
opened_at           TIMESTAMP
clicked             BOOLEAN
clicked_at          TIMESTAMP
replied             BOOLEAN
replied_at          TIMESTAMP
sent_at             TIMESTAMP
error_message       TEXT
```

#### Tabel `replies` — Balasan Email Masuk
```
id                  UUID (Primary Key)
lead_id             UUID - FK ke leads
campaign_id         UUID - FK ke campaigns
from_email          VARCHAR(255)
subject             VARCHAR(500)
body                TEXT
intent              VARCHAR(50) - positive/negative/neutral
conversation_stage  VARCHAR(100) - Tahap pipeline saat ini
received_at         TIMESTAMP
processed_at        TIMESTAMP
```

#### Tabel `clusters` — Kelompok Lead
```
id              UUID (Primary Key)
name            VARCHAR(255)
description     TEXT
type            VARCHAR(50) - master/phd/professional
characteristics JSON - {average_score, common_skills, top_locations, ...}
member_count    INTEGER
is_active       BOOLEAN
```

#### Tabel `users` — Pengguna Sistem
```
id          UUID (Primary Key)
email       VARCHAR(255) - Unique
password    VARCHAR(255) - Hashed (bcrypt)
role        VARCHAR(50) - admin/user
is_active   BOOLEAN
created_at  TIMESTAMP
```

---

## 10. Fitur Unggulan

### 🔍 Scraping LinkedIn 2-Fase dengan Streaming Real-time
Proses scraping dibagi dua fase terpisah untuk menghindari rate limiting LinkedIn. Hasilnya distream langsung ke browser via SSE — tim bisa melihat setiap profil yang ditemukan secara langsung tanpa refresh halaman.

### 🧠 Dual Scoring System
Setiap lead dinilai dari dua sudut pandang berbeda:
1. **Priority Score** (0-100): menilai kesesuaian akademik dan engagement potential
2. **Syllabus Confidence** (0-100): menilai kesesuaian dengan kurikulum S2 yang spesifik

Skor akhir `priority_score` menggabungkan keduanya: `(priority × 0.4) + (syllabus × 0.6)`

### ✉️ Email dengan Full Tracking
Setiap email memiliki tracking ID unik yang memungkinkan sistem mengetahui:
- Kapan email dibuka (open tracking via pixel)
- Kapan dan link mana yang diklik (click tracking via redirect)
- Apakah ada balasan masuk (reply monitoring via IMAP)

### 💬 RAG Chatbot untuk Calon Mahasiswa
Calon mahasiswa bisa bertanya langsung tentang program S2 kepada chatbot AI. Chatbot menjawab berdasarkan dokumen yang diupload oleh admin (brosur, kurikulum, FAQ, dll).

### 📊 Analytics Komprehensif
Dashboard menampilkan:
- Funnel konversi lengkap (berapa yang masuk → tertarik → daftar → enrolled)
- Breakdown sumber lead (LinkedIn vs CSV vs Manual)
- Distribusi profil berdasarkan tipe (Master/PhD/Professional)
- Tren rekrutmen dari waktu ke waktu
- Top prospects berdasarkan skor prioritas

### 🔄 9-Stage Pipeline Otomatis
Sistem melacak setiap calon mahasiswa melalui 9 tahap perjalanan rekrutmen dari pertama kali dihubungi hingga menerima LoA, dengan respons email otomatis di setiap tahap.

---

## 11. API Endpoints

| Method | Endpoint | Fungsi |
|--------|----------|--------|
| POST | `/api/auth/login` | Login, dapat JWT token |
| POST | `/api/auth/register` | Registrasi pengguna baru |
| GET | `/api/leads` | Ambil semua leads (dengan filter & pagination) |
| POST | `/api/leads` | Buat lead manual baru |
| GET | `/api/leads/{id}` | Detail satu lead |
| PUT | `/api/leads/{id}` | Update data lead |
| POST | `/api/leads/{id}/profile` | Jalankan profiling pada satu lead |
| POST | `/api/leads/batch-profile` | Profiling batch banyak lead |
| POST | `/api/leads/cluster` | Jalankan clustering |
| POST | `/api/leads/import-alumni` | Import dari CSV/Excel |
| GET | `/api/campaigns` | List semua kampanye |
| POST | `/api/campaigns` | Buat kampanye baru |
| POST | `/api/campaigns/{id}/activate` | Aktivasi kampanye |
| POST | `/api/campaigns/{id}/pause` | Pause kampanye |
| POST | `/api/campaigns/{id}/send` | Kirim email kampanye |
| POST | `/api/campaigns/{id}/follow-up` | Kirim follow-up |
| GET | `/api/analytics/summary` | KPI & ringkasan statistik |
| GET | `/api/analytics/funnel` | Data funnel konversi |
| GET | `/api/analytics/trends` | Tren rekrutmen dari waktu ke waktu |
| GET | `/api/scraper/linkedin` | Scraping LinkedIn (SSE stream) |
| POST | `/api/email/draft` | Generate draft email via Claude AI |
| GET | `/api/email/monitoring/inbox` | Scan inbox IMAP |
| POST | `/api/chatbot/chat` | Chat dengan RAG chatbot (SSE) |
| POST | `/api/documents/upload` | Upload dokumen ke RAG |
| GET | `/api/export/leads` | Export leads ke CSV/Excel |
| GET | `/api/settings` | Ambil semua settings |
| PUT | `/api/settings` | Update settings |
| GET | `/api/tracking/open/{id}` | Tracking pixel email open |
| GET | `/api/tracking/click/{id}` | Tracking klik link email |
| GET | `/health` | Health check |
| WS | `/ws` | WebSocket real-time kampanye |

---

## 12. Konfigurasi Lingkungan (.env)

File `.env` menyimpan semua konfigurasi sensitif:

```bash
# ── Database ─────────────────────────────────
DATABASE_URL=postgresql+asyncpg://recruitment:recruitment_pass@postgres:5432/recruitment_db
POSTGRES_USER=recruitment
POSTGRES_PASSWORD=recruitment_pass
POSTGRES_DB=recruitment_db

# ── Redis / Celery ────────────────────────────
REDIS_URL=redis://redis:6379/0

# ── Keamanan ─────────────────────────────────
SECRET_KEY=your-secret-key-here          # Untuk sign JWT token
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080        # 7 hari

# ── Admin Default ─────────────────────────────
ADMIN_EMAIL=admin@president.ac.id
ADMIN_PASSWORD=admin123

# ── AI / API Keys (Diperlukan untuk fitur AI) ─
ANTHROPIC_API_KEY=sk-ant-...             # Claude AI untuk email drafting & chatbot
SERPER_API_KEY=...                       # Serper.dev untuk Phase 1 LinkedIn scraping
RESEND_API_KEY=re_...                    # Resend untuk pengiriman email

# ── LinkedIn Scraping ─────────────────────────
LINKEDIN_LI_AT=...                       # Cookie "li_at" dari LinkedIn yang login

# ── Email Monitoring (IMAP) ───────────────────
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=your-email@gmail.com
IMAP_PASSWORD=your-app-password

# ── Email Sending ─────────────────────────────
EMAIL_FROM=noreply@presidentuniversity.ac.id

# ── App Config ────────────────────────────────
ENVIRONMENT=development
BASE_URL=http://localhost:8000
CORS_ORIGINS=["http://localhost:3000","http://localhost:80"]
```

> ⚠️ **Catatan Penting:** PRISM bisa dijalankan **tanpa API keys** — fitur AI (email drafting, chatbot) tidak akan aktif, tapi semua fitur core (CRUD leads, kampanye, analitik) tetap berjalan normal.

---

## 13. Docker Services

PRISM menggunakan 8 Docker container yang berjalan bersamaan:

| Container | Image | Port | Fungsi |
|-----------|-------|------|--------|
| `prism_postgres` | pgvector/pgvector:pg16 | 5432 | Database PostgreSQL + pgvector extension |
| `prism_redis` | redis:7-alpine | 6379 | Message broker untuk Celery task queue |
| `prism_backend` | prism-main-backend | 8000 | FastAPI REST API + WebSocket server |
| `prism_worker` | prism-main-worker | — | Celery worker untuk background jobs |
| `prism_beat` | prism-main-beat | — | Celery beat untuk scheduled tasks (monitoring) |
| `prism_frontend` | prism-main-frontend | 3000 | React + Vite frontend |
| `prism_adminer` | adminer:latest | 8080 | UI admin database PostgreSQL |
| `prism_nginx` | nginx:alpine | 80 | Reverse proxy |

**Dependency Startup Order:**
```
postgres (healthy) ─┐
                    ├──► backend ──► frontend ──► nginx
redis (healthy)    ─┘
                    └──► worker
                    └──► beat
```

---

## 14. Cara Menjalankan

### Dengan Docker (Rekomendasi)
```bash
# Pastikan Docker Desktop sudah berjalan
cd prism-main

# Build dan jalankan semua services
docker compose up -d --build

# Cek status semua container
docker ps

# Lihat log backend
docker compose logs -f backend

# Isi data dummy (opsional)
docker compose exec backend python -m app.seed_data
```

### Akses Aplikasi
| Service | URL |
|---------|-----|
| Website (Frontend) | http://localhost:3000 |
| API Documentation | http://localhost:8000/docs |
| API ReDoc | http://localhost:8000/redoc |
| Database Admin | http://localhost:8080 |
| Nginx Proxy | http://localhost:80 |

### Hentikan Aplikasi
```bash
docker compose down          # Hentikan semua
docker compose down -v       # Hentikan + hapus semua data
```

---

## 15. Kredensial Default

| Item | Nilai |
|------|-------|
| **Email Login** | `admin@president.ac.id` |
| **Password Login** | `admin123` |
| **DB Host** (Adminer) | `postgres` |
| **DB User** | `recruitment` |
| **DB Password** | `recruitment_pass` |
| **DB Name** | `recruitment_db` |

---

## 📋 Ringkasan Singkat

```
PRISM adalah sistem AI rekrutmen mahasiswa S2 President University yang bekerja dalam 6 tahap:

1. CARI  → Scraping profil LinkedIn secara otomatis (2 fase) atau import CSV alumni
2. NILAI → AI Engine menilai setiap calon: skor profil (0-100) & cocokkan dengan silabus S2
3. KELOMPOKKAN → Clustering otomatis berdasarkan tipe profil (Master/PhD/Professional)
4. KIRIM EMAIL → Kampanye email personal dengan template yang dipersonalisasi per lead
5. PANTAU → Track open rate, click rate, reply rate secara real-time
6. TINDAK LANJUT → Pipeline 9 tahap otomatis dari inquiry hingga LoA diterbitkan

Tech: FastAPI + React + PostgreSQL + Redis + Celery + Claude AI + Resend + Docker
```

---

*Dokumentasi ini dibuat berdasarkan analisis lengkap source code PRISM v2.0.0*  
*Diperbarui: Agustus 2026*
