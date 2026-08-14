# PRISM Docker Containers

Brief explanation of every container defined in [`docker-compose.yml`](docker-compose.yml).

---

## 1. `prism_postgres` (PostgreSQL + pgvector)

- **Image:** `pgvector/pgvector:pg16`
- **Port:** `5432`
- **Role:** Primary database. Stores leads, campaigns, emails, users, clusters, etc.
- **Why pgvector:** Adds vector/embedding support used for similarity search (e.g., syllabus matching, lead clustering).
- **Notes:**
  - Data is persisted in the named volume `postgres_data`.
  - Runs `scripts/init.sql` on first boot to create tables/extensions.
  - Health-checked (`pg_isready`) — backend/worker wait for it before starting.

## 2. `prism_redis` (Redis)

- **Image:** `redis:7-alpine`
- **Port:** `6379`
- **Role:** Message broker & cache.
  - Acts as the **Celery broker** (queues background jobs).
  - Used as the Celery result backend / cache.
- **Notes:**
  - Data persisted in the named volume `redis_data`.
  - Health-checked (`redis-cli ping`).

## 3. `prism_backend` (FastAPI API)

- **Build:** [`backend/Dockerfile`](backend/Dockerfile)
- **Port:** `8000`
- **Role:** The REST API backend (FastAPI + SQLAlchemy async).
- **Command:** `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- **Notes:**
  - Code is bind-mounted (`./backend:/app`) so edits hot-reload.
  - Auto-creates the default admin user on first startup.
  - Depends on healthy Postgres & Redis.

## 4. `prism_worker` (Celery Worker)

- **Build:** same [`backend/Dockerfile`](backend/Dockerfile)
- **Port:** none exposed
- **Role:** Processes background jobs from the queue — email sending, scraping, clustering, etc.
- **Command:** `celery -A app.core.celery_app worker --loglevel=info --concurrency=2`
- **Notes:**
  - Shares the backend code via bind mount.
  - Requires Redis (broker) + Postgres.

## 5. `prism_beat` (Celery Beat / Scheduler)

- **Build:** same [`backend/Dockerfile`](backend/Dockerfile)
- **Port:** none exposed
- **Role:** Periodic task scheduler — fires recurring jobs (e.g., reply monitoring, follow-ups) by publishing them to the worker.
- **Command:** `celery -A app.core.celery_app beat --loglevel=info`
- **Notes:** Depends on Redis.

## 6. `prism_frontend` (Vite + React)

- **Build:** [`frontend/Dockerfile`](frontend/Dockerfile)
- **Port:** `3000`
- **Role:** The React (Vite) SPA served to the browser; proxies `/api` to the backend.
- **Notes:**
  - Code bind-mounted (`./frontend:/app`) with `CHOKIDAR_USEPOLLING=true` so edits hot-reload on Windows/macOS.
  - `node_modules` and `.next` are excluded from the mount (anonymous volumes).

## 7. `prism_adminer` (DB UI)

- **Image:** `adminer:latest`
- **Port:** `8080`
- **Role:** Lightweight web UI to browse/manage the Postgres database (useful for debugging).
- **Notes:** Connects to `prism_postgres`; login with the Postgres credentials from `.env`.

## 8. `prism_nginx` (Reverse Proxy)

- **Image:** `nginx:alpine`
- **Port:** `80`
- **Role:** Front-door reverse proxy; routes traffic to the frontend and backend from a single entry point (`http://localhost:80`).
- **Config:** [`nginx/nginx.conf`](nginx/nginx.conf) is bind-mounted read-only.
- **Notes:** Depends on `frontend` and `backend`.

---

## Quick Reference

| Container       | Role                        | Port  |
| --------------- | --------------------------- | ----- |
| postgres        | Database (pgvector)         | 5432  |
| redis           | Broker / cache              | 6379  |
| backend         | FastAPI API                 | 8000  |
| worker          | Celery background worker    | —     |
| beat            | Celery task scheduler       | —     |
| frontend        | Vite + React SPA            | 3000  |
| adminer         | DB management UI            | 8080  |
| nginx           | Reverse proxy               | 80    |

## Common Commands

```bash
docker compose up -d --build    # build & start everything
docker compose ps               # show container status
docker compose logs -f backend  # follow backend logs
docker compose down             # stop all containers
docker compose down -v          # stop + wipe DB/Redis volumes
```
