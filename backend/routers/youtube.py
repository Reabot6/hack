from html import escape
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from services import database as db
from services.media import source_path
from services.media import clip_path
from services import youtube_publish


router = APIRouter(prefix="/api/youtube", tags=["youtube"])


@router.get("/connection")
async def connection():
    return youtube_publish.connection_status()


@router.get("/connect")
async def connect():
    try:
        return {"authorization_url": youtube_publish.authorization_url()}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/oauth/callback", response_class=HTMLResponse)
async def oauth_callback(code: str = "", state: str = "", error: str = ""):
    try:
        if error:
            raise RuntimeError(error)
        youtube_publish.complete_authorization(code, state)
        message, color = "YouTube connected. You can close this window and return to CreatorOS.", "#22c55e"
    except Exception as exc:
        message, color = f"Connection failed: {exc}", "#ef4444"
    return HTMLResponse(f"<main style='font:16px system-ui;max-width:540px;margin:80px auto;color:{color}'>{escape(message)}</main>")


class PublishRequest(BaseModel):
    title: str
    description: str = ""
    tags: list[str] = []
    privacy: str = "private"


@router.post("/{video_id}/publish")
async def publish(video_id: str, body: PublishRequest):
    video = db.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    source = source_path(video_id)
    if not source:
        raise HTTPException(status_code=400, detail="Original source video is unavailable. Upload it again before publishing.")
    package = db.get_upload_package(video_id)
    try:
        db.update_video(video_id, {"status": "publishing"})
        published = youtube_publish.publish_video(source, body.title, body.description, body.tags, body.privacy)
        if package and package.get("srt_content"):
            srt_path = source.with_suffix(".srt")
            srt_path.write_text(package["srt_content"], encoding="utf-8")
            youtube_publish.upload_captions(published["youtube_video_id"], srt_path)
        db.update_video(video_id, {"youtube_video_id": published["youtube_video_id"], "status": "published"})
        return {"video_id": video_id, "status": "published", **published, "captions_uploaded": bool(package and package.get("srt_content"))}
    except Exception as exc:
        db.update_video(video_id, {"status": "transcribed"})
        raise HTTPException(status_code=400, detail=f"Publish failed: {exc}")


@router.post("/{video_id}/clips/{clip_id}/publish")
async def publish_short(video_id: str, clip_id: str, body: PublishRequest):
    clip = next((item for item in db.get_clip_opportunities(video_id) if item["id"] == clip_id), None)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip opportunity not found")
    source = clip_path(video_id, clip_id)
    if not source.exists():
        raise HTTPException(status_code=400, detail="Render this clip before publishing it.")
    try:
        published = youtube_publish.publish_video(source, body.title, body.description, body.tags, body.privacy)
        package = clip.get("clip_package") or {}
        package["youtube_url"] = published["url"]
        db.update_clip_opportunity(clip_id, {"status": "published", "clip_package": package})
        return {"video_id": video_id, "clip_id": clip_id, "status": "published", **published}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Short publish failed: {exc}")
