import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from routers import upload, generate, dashboard, clips
from workers.background import run_for_all_videos

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background worker on app startup
    scheduler.add_job(run_for_all_videos, "interval", hours=2, id="main_worker")
    scheduler.start()
    print("[CreatorOS] Background worker started — runs every 2 hours")
    yield
    scheduler.shutdown()
    print("[CreatorOS] Background worker stopped")


app = FastAPI(
    title="CreatorOS API",
    description="AI-powered post-production automation for YouTube creators",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(upload.router)
app.include_router(generate.router)
app.include_router(dashboard.router)
app.include_router(clips.router)


@app.get("/")
async def root():
    return {
        "name": "CreatorOS",
        "status": "running",
        "version": "1.0.0",
        "message": "While you sleep, we handle the busywork.",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
