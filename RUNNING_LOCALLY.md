# Running PRISM Locally

> **PRISM** — President Recruitment Intelligence System & Matcher

---

## Prerequisites

| Tool               | Version | Check Command            |
| ------------------ | ------- | ------------------------ |
| **Node.js**        | ≥ 18    | `node --version`         |
| **npm**            | ≥ 9     | `npm --version`          |
| **Python**         | ≥ 3.10  | `python --version`       |
| **Docker Desktop** | Latest  | `docker --version`       |
| **Docker Compose** | v2+     | `docker compose version` |

---

## 🐳 Run With Docker (Full Stack — Recommended)

### Start

```bash
# 1. Create .env from example (if not exists)
copy .env.example .env

# 2. Build & start all services
docker compose up -d --build
```

### Access

| Service                   | URL                         |
| ------------------------- | --------------------------- |
| **Frontend**              | http://localhost:3000       |
| **Backend API**           | http://localhost:8000       |
| **API Docs (Swagger)**    | http://localhost:8000/docs  |
| **API Docs (ReDoc)**      | http://localhost:8000/redoc |
| **Adminer (DB UI)**       | http://localhost:8080       |
| **Nginx (reverse proxy)** | http://localhost:80         |

### Default login

The backend auto-creates a default admin on first startup, so you can log in
immediately (no manual seeding required):

| Email                   | Password   | Role  |
| ----------------------- | ---------- | ----- |
| `admin@president.ac.id` | `admin123` | admin |

Override via `ADMIN_EMAIL` / `ADMIN_PASSWORD` in `.env`.

### Seed sample data (optional)

```bash
docker compose exec backend python -m app.seed_data            # seed
docker compose exec backend env FORCE_SEED=1 python -m app.seed_data  # force re-seed
```

### Stop / restart

```bash
docker compose down          # stop all
docker compose down -v       # stop + wipe DB volumes
docker compose logs -f backend
docker compose restart backend
docker compose up -d --build backend
```

---

## 💻 Run Without Docker (Frontend + Backend)

Requires a **local PostgreSQL** instance and Python ≥ 3.10.

> **Note:** Redis is optional. Basic API works without it, but Celery tasks (email sending, background scraping) need it.

### 1. Start PostgreSQL

```powershell
sc query postgresql-x64-16        # check status
net start postgresql-x64-16       # start if stopped (admin shell)
```

If the `recruitment` user / `recruitment_db` don't exist yet:

```powershell
psql -U postgres -c "CREATE USER recruitment WITH PASSWORD 'recruitment_pass';"
psql -U postgres -c "CREATE DATABASE recruitment_db OWNER recruitment;"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE recruitment_db TO recruitment;"
psql -U recruitment -d recruitment_db -f scripts/init.sql
```

### 2. Set up the Python environment

```bash
# conda (recommended)
conda create -n prism python=3.12 -y && conda activate prism

# or venv
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac
```

### 3. Start the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

> Vite serves on **http://localhost:3000** and proxies `/api` → `http://localhost:8000` (see [`frontend/vite.config.js`](frontend/vite.config.js)).

### 5. Seed sample data (optional)

```bash
cd backend
python -m app.seed_data            # seed
env FORCE_SEED=1 python -m app.seed_data  # force re-seed
```

---

## Frontend Pages

| Route        | Page                  | Description                                                      |
| ------------ | --------------------- | ---------------------------------------------------------------- |
| `/`          | **Unified Dashboard** | All features in one scrollable page (10 sections)                |
| `/dashboard` | Dashboard             | KPIs, pipeline status, source breakdown, funnel, trends          |
| `/analytics` | Analytics             | Profile distribution, education breakdown, top prospects         |
| `/email`     | Campaigns             | Create/manage email campaigns, activate/pause/follow-ups         |
| `/clusters`  | Clusters              | Cluster visualization by type (Bachelor/Master/PhD/Professional) |
| `/leads`     | All Leads             | Searchable/filterable lead table                                 |
| `/linkedin`  | LinkedIn Sourcing     | Real-time LinkedIn scraping with SSE events                      |
| `/campus`    | Campus Intake         | CSV/Excel import with column mapping                             |
| `/login`     | Login                 | JWT authentication                                               |
| `/register`  | Register              | User registration                                                |

---

## Troubleshooting

### Docker daemon not running

```
Error: error during connect — The system cannot find the file specified.
```

**Fix:** Open Docker Desktop and wait for it to show **"Running"**.

### Port already in use

- Docker: change the `ports` mapping in `docker-compose.yml` (e.g. `"3001:3000"`).
- Local: `uvicorn app.main:app --port 8001` or `cd frontend && npx vite --port 3001`.

### Frontend can't reach backend

1. `curl http://localhost:8000/health` should return `{"status":"ok"}`.
2. Check the proxy target in [`frontend/vite.config.js`](frontend/vite.config.js) is `http://localhost:8000`.
3. Check backend logs.

### Database connection refused

1. Ensure PostgreSQL is running: `sc query postgresql-x64-16`.
2. Verify credentials in `.env` match your local PostgreSQL setup.

### Python version too old

Use Docker: `docker compose up -d backend`.

---

## Project Structure

```
prism/
├── backend/        # FastAPI + SQLAlchemy + Celery
│   ├── app/
│   │   ├── api/routes/   # API endpoints
│   │   ├── core/         # Config, database, auth
│   │   ├── models/       # SQLAlchemy models
│   │   └── services/     # Business logic
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/       # Vite + React (React Router)
│   ├── src/
│   │   ├── components/   # Shared UI
│   │   ├── lib/          # API client, auth context
│   │   └── pages/        # Route pages
│   ├── package.json
│   └── Dockerfile
├── nginx/          # Reverse proxy config
├── scripts/        # DB init scripts (init.sql, check_db.py)
├── docker-compose.yml
└── .env            # Environment variables
```
