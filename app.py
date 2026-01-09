import os
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

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
# FASTAPI
# =========================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# PING LOOP
# =========================

async def toggle_job():
    async with httpx.AsyncClient(timeout=5) as client:
        for base in APIs:
            url = base + "/health"
            try:
                await client.get(url)
                LAST_PINGS[base] = "ok"
            except:
                LAST_PINGS[base] = "down"

scheduler = AsyncIOScheduler()
scheduler.add_job(toggle_job, "interval", minutes=PING_INTERVAL)

@app.on_event("startup")
def start():
    scheduler.start()

@app.on_event("shutdown")
def stop():
    scheduler.shutdown()

# =========================
# ENDPOINT
# =========================

@app.get("/health")
def health():
    return {
        "interval_minutes": PING_INTERVAL,
        "apis": LAST_PINGS
    }

# =========================
# RUN
# =========================

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
