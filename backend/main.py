import os
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from routers import upload, generate, dashboard, clips, youtube
from workers.background import run_for_all_videos

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(run_for_all_videos, "interval", hours=2, id="main_worker")
    scheduler.start()
    print("[CreatorOS] Background worker started")
    yield
    scheduler.shutdown()

app = FastAPI(
    title="CreatorOS API",
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

app.include_router(upload.router)
app.include_router(generate.router)
app.include_router(dashboard.router)
app.include_router(clips.router)
app.include_router(youtube.router)
app.mount("/media", StaticFiles(directory=str(Path(__file__).parent / "media")), name="media")

@app.get("/")
async def root():
    return {"name": "CreatorOS", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
