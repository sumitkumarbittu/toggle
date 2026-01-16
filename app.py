import os
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
import logging
from datetime import datetime

# =========================
# LOGGING
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logging.getLogger("apscheduler").setLevel(logging.INFO)

# =========================
# GLOBAL STATE
# =========================

PING_INTERVAL = 10   # minutes

# FULL HEALTH URLs (can be /health, /status, etc)
APIs = [
    "https://togglesk.onrender.com/health",
    "https://paydriveinsurance.onrender.com/health",
    "https://paydriveanalytics.onrender.com/health",
    "https://paydrivechat.onrender.com/healthz",
    "https://db5-nhy1.onrender.com/health",
    "https://db6-c4rn.onrender.com/health",
    "https://db7.onrender.com/health",
    "https://dbi-2xer.onrender.com/health",
    "https://dbi2.onrender.com/health",
    "https://gform2.onrender.com/health",
    "https://tracksk.onrender.com/health",
    "https://chatapi101.onrender.com/health",
    "https://chatapi102.onrender.com/health",
    "https://chatapi103.onrender.com/health",
    "https://chatapi104.onrender.com/health"
]


    #"https://toggle-1811.onrender.com/health",
    #"https://paydriveapi.onrender.com/health",
    #"https://chat-d8ex.onrender.com/healthz",
    #"https://paydrive-analytics.onrender.com/health",
    #"https://webda.onrender.com/health",
    #"https://gform-36w5.onrender.com/health",
    #"https://db-btl1.onrender.com/health"


LAST_PINGS = {}

# =========================
# PING FUNCTION
# =========================

async def ping_all():
    print("PING CYCLE @", datetime.utcnow().isoformat())

    async with httpx.AsyncClient(timeout=5) as client:
        for url in APIs:
            try:
                await client.get(url)
                LAST_PINGS[url] = "ok"
                print(" OK  ", url)
            except Exception as e:
                LAST_PINGS[url] = "down"
                print(" DOWN", url, str(e))

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

# =========================
# FASTAPI
# =========================

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
