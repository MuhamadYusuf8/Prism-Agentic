from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.core.database import engine, Base
from app.api.routes import (
    leads, analytics, scraper, email, chatbot, documents, export,
    auth, campaigns, tracking, monitoring, settings as settings_routes,
    users,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables if they don't exist yet
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Ensure the default admin exists so login works on a fresh database
    from app.core.bootstrap import ensure_default_admin

    await ensure_default_admin()
    yield
    await engine.dispose()


app = FastAPI(
    title="PRISM — President Recruitment Intelligence System & Matcher",
    description="AI-powered student recruitment platform by President University",
    version="2.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Health check / API root."""
    return {
        "name": "PRISM API",
        "version": "2.0.0",
        "status": "ok",
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public routes
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(tracking.router, prefix="/api", tags=["tracking"])

# Protected routes
app.include_router(leads.router, prefix="/api/leads", tags=["leads"])
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["campaigns"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(scraper.router, prefix="/api/scraper", tags=["scraper"])
app.include_router(email.router, prefix="/api/email", tags=["email"])
app.include_router(monitoring.router, prefix="/api/email/monitoring", tags=["email-monitoring"])
app.include_router(chatbot.router, prefix="/api/chatbot", tags=["chatbot"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(export.router, prefix="/api/export", tags=["export"])
app.include_router(settings_routes.router, prefix="/api", tags=["settings"])
app.include_router(users.router, prefix="/api/users", tags=["users"])


# ── Socket.IO-style WebSocket for real-time updates ──────────────────────────
# Ported from recruit-Z server.js (Socket.IO subscribe:campaign / unsubscribe:campaign)


connected_clients: dict[str, set[WebSocket]] = {}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_id = f"client_{id(websocket)}"
    connected_clients[client_id] = set()
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            if action == "subscribe:campaign":
                campaign_id = data.get("campaign_id")
                if campaign_id:
                    connected_clients[client_id].add(campaign_id)
            elif action == "unsubscribe:campaign":
                campaign_id = data.get("campaign_id")
                if campaign_id and campaign_id in connected_clients[client_id]:
                    connected_clients[client_id].discard(campaign_id)
    except WebSocketDisconnect:
        pass
    finally:
        connected_clients.pop(client_id, None)


async def broadcast_campaign_update(campaign_id: str, payload: dict):
    """Broadcast a campaign update to all subscribed WebSocket clients."""
    import json
    for cid, subs in list(connected_clients.items()):
        if campaign_id in subs:
            for ws in list(subs):
                try:
                    await ws.send_json({"type": "campaign_update", "campaign_id": campaign_id, **payload})
                except Exception:
                    pass


@app.get("/health")
async def health():
    return {"status": "ok"}
