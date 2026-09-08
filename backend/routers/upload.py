import os
import uuid
import asyncio
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
import aiofiles

from services.ffmpeg import extract_audio, compress_audio, is_video_file, is_audio_file, get_file_size_mb
from services.whisper import transcribe, format_srt
from services import database as db
from services.media import MEDIA_DIR

router = APIRouter(prefix="/api", tags=["upload"])

TMP_DIR = Path(__file__).parent.parent / "temp_uploads"
TMP_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".mp3", ".wav", ".m4a", ".aac"}
MAX_UPLOAD_MB = 500


def _cleanup(*paths):
    for path in paths:
        try:
            p = Path(path)
            if p.exists():
                p.unlink()
        except Exception:
            pass


@router.post("/upload")
async def upload_video(request: Request, file: UploadFile = File(...)):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Upload MP4, MOV, MP3, WAV, or M4A."
        )

    video_id = str(uuid.uuid4())
    # Keep the original source asset: publishing and clip rendering happen after
    # transcription, not during the upload request.
    tmp_input = MEDIA_DIR / f"{video_id}_source{suffix}"
    tmp_audio = TMP_DIR / f"{video_id}_audio.mp3"

    try:
        # Save uploaded file
        async with aiofiles.open(str(tmp_input), "wb") as f:
            content = await file.read()
            await f.write(content)

        print(f"[DEBUG] File saved: {tmp_input.stat().st_size} bytes at {tmp_input}")

        size_mb = get_file_size_mb(str(tmp_input))
        if size_mb > MAX_UPLOAD_MB:
            _cleanup(tmp_input)
            raise HTTPException(status_code=400, detail=f"File is {size_mb:.0f}MB. Max is {MAX_UPLOAD_MB}MB.")

        db.create_video({
            "id": video_id,
            "original_filename": file.filename,
            "status": "extracting_audio",
        })

        loop = asyncio.get_event_loop()

        # Extract or compress audio
        print(f"[DEBUG] Extracting audio to {tmp_audio}")
        if is_video_file(file.filename):
            await loop.run_in_executor(None, extract_audio, str(tmp_input), str(tmp_audio))
        else:
            await loop.run_in_executor(None, compress_audio, str(tmp_input), str(tmp_audio))

        print(f"[DEBUG] Audio extracted. File exists: {tmp_audio.exists()} size: {tmp_audio.stat().st_size if tmp_audio.exists() else 0}")

        db.update_video(video_id, {"status": "transcribing"})

        # Transcribe — audio file must still exist here
        print(f"[DEBUG] Starting transcription of {tmp_audio}")
        result = await loop.run_in_executor(None, transcribe, str(tmp_audio))
        print(f"[DEBUG] Transcription done: {len(result['text'])} chars")

        # Delete audio file after transcription
        _cleanup(tmp_audio)

        srt_content = format_srt(result["segments"])

        db.update_video(video_id, {
            "transcript_text": result["text"],
            "transcript_segments": result["segments"],
            "status": "transcribed",
        })

        db.save_upload_package({
            "video_id": video_id,
            "srt_content": srt_content,
        })

        return {
            "video_id": video_id,
            "status": "transcribed",
            "filename": file.filename,
            "transcript_preview": result["text"][:500] + ("..." if len(result["text"]) > 500 else ""),
            "transcript_length": len(result["text"]),
            "segment_count": len(result["segments"]),
        }

    except HTTPException:
        raise
    except Exception as e:
        _cleanup(tmp_input, tmp_audio)
        db.log_error("upload", str(e))
        try:
            db.update_video(video_id, {"status": "failed"})
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/upload/{video_id}/status")
async def get_upload_status(video_id: str):
    video = db.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return {
        "video_id": video_id,
        "status": video["status"],
        "transcript_preview": (video.get("transcript_text") or "")[:500],
    }


@router.get("/videos")
async def list_videos():
    videos = db.list_videos()
    return {"videos": videos}


@router.get("/videos/{video_id}")
async def get_video(video_id: str):
    video = db.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video
