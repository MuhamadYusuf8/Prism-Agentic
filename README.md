# PRISM

### President Recruitment Intelligence System & Matcher

> AI-powered student recruitment platform by **President University**

---

## Overview

PRISM automates the entire student recruitment pipeline — from discovering prospects to personalized outreach — using AI and data intelligence. The system is scoped to **Master's (S2) candidates only**.

```
Serper Discovery → LinkedIn Detail Enrichment → Syllabus Matching → Lead Profiling → AI Email → Campaigns → Enrolled
```

## Features

### 🔍 Lead Sourcing

- **Two-Phase LinkedIn Scraper** — Phase 1 discovers profiles via Google Search (Serper API), Phase 2 enriches with full details (skills, education, experience) using an authenticated LinkedIn session
- **Alumni Import** — CSV/Excel bulk import with smart column mapping (Indonesian & English column names)
- **Cikarang Industrial Estate Scraper** — scrapes tenant directories from MM2100, EJIP, KIIC, BIIE
- **Manual Entry** — create leads directly via the API

### 🧠 Syllabus Matching Engine

- **10 Syllabus Subjects** — matches leads against Research Method, Machine Learning, Ubiquitous Computing, Big Data Analysis, Deep Learning, BI & Analytics, Voice & Image Recognition, Information Retrieval, Cybersecurity, NLP & Conversational AI
- **Weighted Scoring Formula** — skills (50%), job title (20%), headline (15%), summary (15%)
- **Per-Subject Confidence** — each subject scored 0–100, overall confidence averaged
- **Headline→Skills Extraction** — auto-extracts tech skills from headline, job title, and summary
- **Score Display** — `X/100` format with hover info panel explaining calculation

### 🤖 AI Profiling Engine

- **CS Relevance Scoring** — keyword-based scoring (0–100) for computer science relevance
- **Weighted Scoring** — academic (35%), engagement (20%), program fit (30%), data completeness (15%)
- **Education Analysis** — degree level extraction, institution recognition, GPA parsing
- **Interest Extraction** — identifies research interests, specializations, and career goals
- **Program Matching** — recommends S2 Manajemen, S2 Teknik Industri, MBA Eksekutif, S2 Ilmu Komputer
- **Tag Generation** — auto-generates tags based on profile data
- **Data Quality Assessment** — validates email, phone, and profile completeness

### 📊 Analytics & Dashboards

- **Unified Dashboard** (`/`) — all features in one scrollable page (10 sections)
- **Dashboard** (`/dashboard`) — KPIs, pipeline status, source breakdown, funnel visualization, trends
- **Analytics** (`/analytics`) — profile distribution, education breakdown, top prospects, email stats
- **Clusters** (`/clusters`) — cluster visualization by type (Master/PhD/Professional)

### ✉️ Email Campaigns

- **Campaign Management** — create, activate, pause campaigns with target filtering
- **AI Email Drafting** — Claude generates personalized outreach emails per lead
- **Email Sending** — via Resend API with open/click tracking
- **Follow-up Sequences** — configurable follow-up delays and max follow-ups
- **Campaign Monitoring** — real-time stats (sent, opened, clicked, replied, interested)
- **WebSocket Updates** — live campaign status updates via `/ws`

### 💬 Inbound Chatbot

- **RAG-powered Q&A** — Claude-powered chatbot for prospective students (Bahasa Indonesia)
- **Streaming Responses** — SSE-based real-time chat responses
- **Document Upload** — upload PDF/text documents into the RAG knowledge base

### 📬 Reply Monitoring & Auto-Responder

- **IMAP Inbox Monitoring** — polls for email replies
- **Intent Classification** — sentiment analysis with positive/negative keyword matching
- **9-Stage Conversation Pipeline** — tracks the full recruitment journey:
  1. Initial Inquiry → 2. Info Requested → 3. Info Received → 4. Application Submitted
  2. Documents Reviewed → 6. Interview Scheduled → 7. Interview Completed
  3. Offer Made → 9. LoA Issued → Follow-up until enrolled
- **Auto-Responses** — sends contextual replies based on conversation stage

### 📥 Data Processing

- **Deduplication** — email and LinkedIn URL based dedup with fuzzy matching
- **Data Cleaning** — phone normalization, email validation, text sanitization
- **Clustering** — groups leads by profile type (Master/PhD/Professional)
- **Export** — download leads as CSV or Excel

### 🔐 Authentication & Settings

- **JWT Authentication** — register, login, profile management
- **Role-based Access** — admin and user roles
- **Application Settings** — Email SMTP config, LinkedIn scraper settings, monitoring config, general settings

## Tech Stack

| Layer    | Technology                         |
| -------- | ---------------------------------- |
| Frontend | React 18 + Vite + JavaScript + Tailwind |
| Backend  | FastAPI + Python 3.12              |
| Database | PostgreSQL 16 + pgvector           |
| Queue    | Redis + Celery                     |
| AI       | Claude API (Anthropic)             |
| Search   | Serper.dev (Google Search API)     |
| Email    | Resend                             |
| Scraping | httpx + BeautifulSoup              |
| Proxy    | Nginx                              |

## Quick Start

### Prerequisites

| Tool               | Version | Check Command            |
| ------------------ | ------- | ------------------------ |
| **Node.js**        | ≥ 18    | `node --version`         |
| **npm**            | ≥ 9     | `npm --version`          |
| **Python**         | ≥ 3.10  | `python --version`       |
| **Docker Desktop** | Latest  | `docker --version`       |
| **Docker Compose** | v2+     | `docker compose version` |

### Docker (Full Stack)

```bash
# 1. Clone
git clone https://github.com/yourusername/prism.git
cd prism

# 2. Configure
copy .env.example .env
# Fill in: ANTHROPIC_API_KEY, SERPER_API_KEY, RESEND_API_KEY

# 3. Run
docker compose up --build
```

**Open:**

- Dashboard → http://localhost:3000
- API Docs → http://localhost:8000/docs
- DB Admin → http://localhost:8080

### Local Development

**Terminal 1 — Backend:**

```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — React Frontend:**

```bash
cd frontend
npm install
npm run dev
```

The React frontend will be available at **http://localhost:5173**.

## Credentials

> ⚠️ **Security:** Credentials are stored in [`CREDENTIALS.md`](CREDENTIALS.md) (gitignored — never committed). See that file for login, database, API keys, and app configuration details.

## Frontend Pages

| Route         | Page                  | Description                                                      |
| ------------- | --------------------- | ---------------------------------------------------------------- |
| `/`           | **Unified Dashboard** | All features in one scrollable page (10 sections)                |
| `/dashboard`  | Dashboard             | KPIs, pipeline status, source breakdown, funnel, trends          |
| `/analytics`  | Analytics             | Profile distribution, education breakdown, top prospects         |
| `/email`      | Campaigns             | Create/manage email campaigns, activate/pause/follow-ups         |
| `/email/:id`  | Campaign Detail       | Campaign monitoring, stats, email logs, replies                  |
| `/clusters`   | Clusters              | Cluster visualization by type (Master/PhD/Professional)          |
| `/leads`      | All Leads             | Searchable/filterable lead table with pagination                 |
| `/leads/:id`  | Lead Detail           | Full lead profile, profiling data, email history, replies        |
| `/linkedin`   | LinkedIn Sourcing     | Real-time LinkedIn scraping with SSE events                      |
| `/campus`     | Campus Intake         | CSV/Excel import with column mapping, candidate track view       |
| `/settings`   | Settings              | Email SMTP, LinkedIn scraper, monitoring, general config         |
| `/login`      | Login                 | JWT authentication                                               |
| `/register`   | Register              | User registration                                                |

## API Routes

| Prefix           | Tags      | Description                                          |
| ---------------- | --------- | ---------------------------------------------------- |
| `/api/auth`      | auth      | Register, login, profile                             |
| `/api/leads`     | leads     | CRUD leads, profiling, clustering, alumni import     |
| `/api/campaigns` | campaigns | Campaign CRUD, activate/pause, send test, follow-ups |
| `/api/analytics` | analytics | Summary stats, funnel, trends, source breakdown      |
| `/api/scraper`   | scraper   | Two-phase LinkedIn SSE streaming + batch enrichment  |
| `/api/email`     | email     | AI draft generation, email sending                   |
| `/api/chatbot`   | chatbot   | RAG chatbot with SSE streaming                       |
| `/api/documents` | documents | Document upload for RAG knowledge base               |
| `/api/export`    | export    | CSV/Excel lead export                                |
| `/api/settings`  | settings  | App settings CRUD                                    |
| `/api/tracking`  | tracking  | Email open tracking pixel, click tracking redirects  |
| `/health`        | —         | Health check endpoint                                |
| `/ws`            | —         | WebSocket for real-time campaign updates             |

## Backend Services

| Service                             | Description                                                                  |
| ----------------------------------- | ---------------------------------------------------------------------------- |
| `services/syllabus_matcher.py`      | Syllabus matching engine — 10 subjects, weighted scoring, confidence calcs   |
| `services/profiling.py`             | CS relevance scoring, weighted scoring, education analysis, program matching |
| `services/clustering.py`            | Lead clustering by profile type (Master/PhD/Professional)                    |
| `services/data_processor.py`        | Data cleaning, validation, deduplication, merging                            |
| `services/email_service.py`         | Email sending with tracking, campaign dispatch, follow-ups                   |
| `services/conversation_pipeline.py` | 9-stage recruitment conversation pipeline                                    |
| `services/reply_monitor.py`         | IMAP inbox monitoring, intent classification, auto-responses                 |

## Scrapers

| Scraper                          | Source                      | Method                                                              |
| -------------------------------- | --------------------------- | ------------------------------------------------------------------- |
| `scrapers/linkedin.py`           | LinkedIn profiles (Phase 1) | Serper.dev Google Search API — discovers profile URLs from snippets |
| `scrapers/linkedin_detail.py`    | LinkedIn profiles (Phase 2) | Authenticated session (`li_at` cookie) — extracts full details      |
| `scrapers/alumni.py`             | Alumni CSV/Excel            | Pandas-based file parsing with smart column mapping                 |
| `scrapers/cikarang.py`           | Cikarang industrial estates | httpx + BeautifulSoup (MM2100, EJIP, KIIC, BIIE)                   |

## AI Agents

| Agent                    | Technology | Purpose                                |
| ------------------------ | ---------- | -------------------------------------- |
| `email_agent/drafter.py` | Claude API | Generates personalized outreach emails |
| `email_agent/sender.py`  | Resend API | Sends emails via Resend                |
| `ai_agent/chatbot.py`    | Claude API | RAG chatbot for prospective students   |

## Database Models

| Model      | Table        | Description                                                  |
| ---------- | ------------ | ------------------------------------------------------------ |
| `Lead`     | `leads`      | Prospect data with syllabus scores, profiling, status, source tracking |
| `Campaign` | `campaigns`  | Email campaigns with templates, targeting, follow-up config  |
| `EmailLog` | `email_logs` | Email send history with open/click/reply tracking            |
| `Reply`    | `replies`    | Inbound email replies with intent classification             |
| `Cluster`  | `clusters`   | Lead groupings by profile type                               |
| `User`     | `users`      | Application users with roles                                 |

## Environment Variables

| Variable               | Description                                                  |
| ---------------------- | ------------------------------------------------------------ |
| `ANTHROPIC_API_KEY`    | Claude API key                                               |
| `SERPER_API_KEY`       | Google Search via serper.dev (free 2500/mo) — Phase 1        |
| `LINKEDIN_LI_AT`       | LinkedIn session cookie — Phase 2 detail enrichment          |
| `RESEND_API_KEY`       | Email sending via Resend                                     |
| `BRAVE_SEARCH_API_KEY` | Brave Search API (alternative search)                        |
| `DATABASE_URL`         | PostgreSQL connection string                                 |
| `REDIS_URL`            | Redis connection string                                      |
| `POSTGRES_USER`        | Database user                                                |
| `POSTGRES_PASSWORD`    | Database password                                            |
| `POSTGRES_DB`          | Database name                                                |
| `EMAIL_FROM`           | Sender email address                                         |
| `SECRET_KEY`           | JWT secret key                                               |
| `ENVIRONMENT`          | `development` or `production`                                |
| `CORS_ORIGINS`         | Allowed CORS origins                                         |
| `NEXT_PUBLIC_API_URL`  | Frontend API URL                                             |
| `BACKEND_URL`          | Internal backend URL                                         |

## Project Structure

```
prism/
├── react-frontend/           # React + Vite dashboard (PRIMARY)
│   └── src/
│       ├── pages/            # Page components
│       ├── components/ui/    # Shared components (Sidebar, StatCard, Charts)
│       └── lib/              # API client, auth context
├── frontend/                 # Next.js 15 dashboard (LEGACY)
│   └── src/
│       ├── app/              # Pages (App Router)
│       ├── components/ui/    # Shared components
│       └── lib/              # API client, auth context
├── backend/
│   ├── app/
│   │   ├── api/routes/       # FastAPI route handlers
│   │   ├── core/             # Config, database, auth, Celery
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── services/         # Business logic (profiling, clustering, email, etc.)
│   │   ├── scrapers/         # LinkedIn, Alumni, Cikarang scrapers
│   │   ├── email_agent/      # AI email drafter + sender
│   │   ├── ai_agent/         # RAG chatbot
│   │   └── workers/          # Celery background tasks
│   ├── requirements.txt
│   └── Dockerfile
├── scripts/                  # DB init SQL, sample data CSV, debug scripts
├── nginx/                    # Reverse proxy config
├── plans/                    # Architecture and planning docs
├── docker-compose.yml        # All 8 services
├── .env.example              # Environment template
├── CREDENTIALS.md            # All credentials in one file
└── RUNNING_LOCALLY.md        # Detailed local setup guide
```

## Docker Services

| Container        | Purpose                     | Port |
| ---------------- | --------------------------- | ---- |
| `prism_postgres` | PostgreSQL 16 + pgvector    | 5432 |
| `prism_redis`    | Redis (Celery broker)       | 6379 |
| `prism_backend`  | FastAPI backend             | 8000 |
| `prism_worker`   | Celery worker (async tasks) | —    |
| `prism_beat`     | Celery beat (scheduler)     | —    |
| `prism_frontend` | Next.js frontend            | 3000 |
| `prism_adminer`  | Database admin UI           | 8080 |
| `prism_nginx`    | Nginx reverse proxy         | 80   |

## Seed Data

The project includes a comprehensive seed script that generates realistic demo data (Master candidates only):

```bash
docker compose exec backend python -m app.seed_data
```

Generates: **60 leads**, **6 campaigns**, **4 clusters**, **200+ email logs**, **40+ replies**.

---

_Built with ❤️ for President University_
