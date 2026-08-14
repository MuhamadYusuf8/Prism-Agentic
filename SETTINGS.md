# Settings Guide

This document explains everything you need to configure for the Prism student
recruitment system. There are **two** places where settings live:

1. **The in-app Settings page** (`/settings` in the frontend) — used by the
   running app at runtime (SMTP, LinkedIn scraping, monitoring, general info).
2. **The backend `.env` file** (`backend/.env`) — environment variables loaded
   when the backend starts (database, API keys, secrets).

---

## 1. In-App Settings Page (`/settings`)

The settings page is split into 4 sections. Fields are stored in the backend
(`backend/app/api/routes/settings.py`) and are exposed through
`GET /api/settings` and `PUT /api/settings`.

> ⚠️ **Important:** These settings are currently stored **in memory** on the
> backend. They reset whenever the backend restarts. For anything that must
> survive a restart, put it in `backend/.env` instead (Section 2).

### 1.1 Email Configuration

Used to send outreach emails to leads.

| Field | Description | Required? | Example |
|-------|-------------|-----------|---------|
| **SMTP Host** | The SMTP server that sends your emails | Yes (to send email) | `smtp.gmail.com` |
| **SMTP Port** | Port for the SMTP server (587 = TLS, 465 = SSL) | Yes | `587` |
| **SMTP User** | Username / email used to authenticate to SMTP | Yes | `admissions@president.ac.id` |
| **SMTP Password** | App password (not your normal password; use an app-specific password) | Yes | `xxxx xxxx xxxx xxxx` |
| **From Name** | Display name shown on outgoing emails | Yes | `Admissions Team` |
| **From Email** | Address emails are sent from | Yes | `admissions@president.ac.id` |

**Gmail example:**
- Host: `smtp.gmail.com`
- Port: `587`
- User: your Gmail address
- Password: an **App Password** (Google Account → Security → 2-Step Verification → App passwords)

### 1.2 LinkedIn Scraper

Used for scraping leads from LinkedIn.

| Field | Description | Required? | Example |
|-------|-------------|-----------|---------|
| **LinkedIn Email** | LinkedIn account email used for scraping | Yes (to log in) | `you@example.com` |
| **LinkedIn Password** | LinkedIn account password | Yes (to log in) | `••••••••` |
| **Max Requests per Session** | Cap on requests per scrape session to avoid rate-limit blocks | Yes | `50` |
| **LinkedIn Session Cookie (`li_at`)** | Session cookie enabling Phase 2 detail scraping (skills, education, experience) | Recommended | `AQED...` |

**How to get the `li_at` cookie:**
1. Log into `linkedin.com` in your browser.
2. Open DevTools (`F12`) → **Application** → **Cookies** → `linkedin.com`.
3. Copy the value of the `li_at` cookie and paste it here.

> ⚠️ Use a **dedicated/throwaway** LinkedIn account. Automated scraping can get
> accounts flagged or temporarily restricted.

### 1.3 Email Monitoring

Controls automatic reply/response monitoring.

| Field | Description | Required? | Example |
|-------|-------------|-----------|---------|
| **Check Interval (minutes)** | How often the system checks for email replies | No | `5` |
| **Auto Follow-up** | Automatically send follow-up emails when no reply is received | No | On / Off |
| **Notify on Reply** | Flag/notify when a lead replies | No | On / Off |

### 1.4 General Settings

Institution-level information used in emails and campaign content.

| Field | Description | Required? | Example |
|-------|-------------|-----------|---------|
| **Institution Name** | Your school/university name | Yes | `President University` |
| **Program URL** | Link to your program/academic pages | No | `https://president.ac.id/programs` |
| **Reply-to Email** | Address used as the reply-to on outgoing emails | Recommended | `admissions@president.ac.id` |

---

## 2. Backend Environment Variables (`backend/.env`)

These are loaded by `backend/app/core/config.py` when the backend starts.
Copy `backend/.env` values from `.env.example` as needed.

### 2.1 Required for a working stack

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string (asyncpg driver) | `postgresql+asyncpg://recruitment:recruitment_pass@localhost:5432/recruitment_db` |
| `REDIS_URL` | Redis connection for Celery tasks | `redis://localhost:6379/0` |
| `SECRET_KEY` | JWT / signing secret — **change in production** to a random 32+ char string | `dev_secret_key_change_in_production` |
| `ENVIRONMENT` | `development` or `production` | `development` |

### 2.2 API Keys

| Variable | Purpose | Required? | Where to get it |
|----------|---------|-----------|-----------------|
| `ANTHROPIC_API_KEY` | Claude AI for the chatbot / AI features | Recommended | https://console.anthropic.com |
| `BRAVE_SEARCH_API_KEY` | Brave Search for lead enrichment (free: ~2000 queries/month) | Optional | https://api.search.brave.com/app/keys |
| `SERPER_API_KEY` | Serper.dev Google Search API (free: 2500 queries) | Optional | https://serper.dev |
| `HUNTER_API_KEY` | Hunter.io email finder for leads (25 free/mo) | Optional | https://hunter.io |
| `RESEND_API_KEY` | Resend for sending email (alternative to SMTP) | Optional | https://resend.com |

### 2.3 Email, LinkedIn & Email Monitoring

| Variable | Description | Example |
|----------|-------------|---------|
| `EMAIL_FROM` | Default sender address for emails | `mit@president.ac.id` |
| `IMAP_HOST` | IMAP server of the mailbox where replies are received (e.g. `imap.google.com` for Google Workspace) | `imap.google.com` |
| `IMAP_PORT` | IMAP port (`993` SSL or `143` STARTTLS) | `993` |
| `IMAP_USERNAME` | Mailbox address used for monitoring (usually equals `EMAIL_FROM`) | `mit@president.ac.id` |
| `IMAP_PASSWORD` | Mailbox password / app password (Google: create an App Password) | `xxxx xxxx xxxx xxxx` |
| `IMAP_USE_SSL` | `true` for port 993, `false` for 143 | `true` |
| `LINKEDIN_LI_AT` | LinkedIn `li_at` cookie (same value as in the Settings page) | `AQED...` |

> ⚠️ `EMAIL_FROM` must be a domain **verified in Resend** (or use SMTP in the
> Settings page). Until `president.ac.id` is verified on
> https://resend.com/domains, emails sent from `mit@president.ac.id` will be
> tracked as **failed** (with the error shown in Email Monitoring).

---

## 4. Email Tracking & Conversation Monitoring

The **Email Monitoring** page (`/email-monitoring`, sidebar → **Email Monitoring**)
tracks every outreach email and the conversation with each student.

### What it shows

- **Overview** — aggregate stats and an engagement funnel: sent → opened → clicked
  → replied, plus bounced/failed and open/click/reply rates.
- **Conversations** — one row per student (or recipient) with the latest status,
  subject, email/reply counts, and last activity.
- **Thread view** — a chat-style view merging every outgoing email (with open/click/
  reply status), the student's replies (with intent/sentiment classification), and
  any auto-responses sent back.

### How tracking works

- Sending adds an **open-tracking pixel** and **click-tracking links** to every
  email (`/api/tracking/open/{id}` and `/api/tracking/click/{id}`).
- Status lifecycle: `pending → sent → opened → clicked → replied`, or
  `bounced` / `failed`.
- Replies are ingested from the configured mailbox via **Sync Inbox**
  (`POST /api/email/monitoring/sync-inbox`), which polls IMAP for unread messages,
  matches them to the student lead, classifies intent/sentiment, and stores them.

### API

| Endpoint | Description |
|----------|-------------|
| `GET /api/email/monitoring/overview` | Aggregate tracking stats + rates |
| `GET /api/email/monitoring/conversations` | List conversations (search/filter/paginate) |
| `GET /api/email/monitoring/conversations/{key}` | Full thread (lead UUID or recipient email) |
| `POST /api/email/monitoring/sync-inbox` | Fetch unread replies from IMAP mailbox |

### 2.4 Admin account (auto-created on startup)

| Variable | Description | Example |
|----------|-------------|---------|
| `ADMIN_EMAIL` | Default admin email used to log in | `admin@president.ac.id` |
| `ADMIN_PASSWORD` | Default admin password | `admin123` |

> **Login:** The admin account is created automatically at backend startup if it
> doesn't exist. Default credentials: `admin@president.ac.id` / `admin123`.

---

## 3. Recommended Setup Checklist

To get a fully working system:

1. **Backend `.env`** — set a real `SECRET_KEY`, configure `DATABASE_URL` /
   `REDIS_URL`, and add the API keys you plan to use.
2. **Login** with the admin account (or register a new user).
3. **General Settings** — set your Institution Name, Program URL, Reply-to Email.
4. **Email Configuration** — enter your SMTP host/port/user/password and the
   From name/email so outreach emails actually send.
5. **LinkedIn Scraper** — enter your LinkedIn credentials and paste the `li_at`
   cookie for full detail scraping.
6. **Email Monitoring** — set a check interval and toggle auto-follow-up /
   notify-on-reply as desired.
7. Click **Save All**.

> Remember: in-app Settings are held **in memory** and reset on backend restart.
> For persistent configuration, prefer environment variables in `backend/.env`.
