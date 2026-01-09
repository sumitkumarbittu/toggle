import os
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager

# =========================
# GLOBAL STATE
# =========================

PING_INTERVAL = 10   # minutes

APIs = [
    "https://toggle-1811.onrender.com",
    "https://paydriveapi.onrender.com",
    "https://chat-d8ex.onrender.com",
    "https://paydrive-analytics.onrender.com",
    "https://webda.onrender.com"
]

LAST_PINGS = {}

# =========================
# PING FUNCTION
# =========================

async def ping_all():
    async with httpx.AsyncClient(timeout=5) as client:
        for base in APIs:
            url = base + "/health"
            try:
                await client.get(url)
                LAST_PINGS[base] = "ok"
            except:
                LAST_PINGS[base] = "down"

# =========================
# SCHEDULER
# =========================

scheduler = AsyncIOScheduler()
scheduler.add_job(ping_all, "interval", minutes=PING_INTERVAL)

# =========================
# FASTAPI LIFESPAN (RENDER SAFE)
# =========================

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    await ping_all()   # run immediately on boot
    yield
    scheduler.shutdown()

# ⚠️ DEFINE FASTAPI ONLY ONCE
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# ENDPOINTS
# =========================

@app.get("/health")
def health():
    return {
        "interval_minutes": PING_INTERVAL,
        "apis": LAST_PINGS
    }

@app.get("/toggle")
async def toggle():
    await ping_all()
    return {
        "status": "refreshed",
        "apis": LAST_PINGS
    }

# =========================
# RUN
# =========================

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
