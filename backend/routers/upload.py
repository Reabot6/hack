import os
import uuid
import asyncio
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse
import aiofiles

from services.ffmpeg import extract_audio, compress_audio, is_video_file, is_audio_file, get_file_size_mb
from services.whisper import transcribe, format_srt
from services import database as db

router = APIRouter(prefix="/api", tags=["upload"])

TMP_DIR = Path("/tmp/creatorOS")
TMP_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".mp3", ".wav", ".m4a", ".aac"}
MAX_UPLOAD_MB = 500


@router.post("/upload")
async def upload_video(request: Request, file: UploadFile = File(...)):
    """
    Phase 1: Accept MP4 or audio file, extract audio, transcribe, store.
    Returns video_id and transcript preview immediately.
    """
    # Validate file type
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Upload MP4, MOV, MP3, WAV, or M4A."
        )

    video_id = str(uuid.uuid4())
    tmp_input = TMP_DIR / f"{video_id}_input{suffix}"
    tmp_audio = TMP_DIR / f"{video_id}_audio.mp3"

    try:
        # Save uploaded file to disk
        async with aiofiles.open(tmp_input, "wb") as f:
            content = await file.read()
            await f.write(content)

        # Check size
        size_mb = get_file_size_mb(str(tmp_input))
        if size_mb > MAX_UPLOAD_MB:
            raise HTTPException(
                status_code=400,
                detail=f"File is {size_mb:.0f}MB. Maximum upload size is {MAX_UPLOAD_MB}MB."
            )

        # Create video record immediately so frontend can poll status
        video_record = db.create_video({
            "id": video_id,
            "original_filename": file.filename,
            "status": "extracting_audio",
        })

        # Extract or compress audio
        loop = asyncio.get_event_loop()
        if is_video_file(file.filename):
            await loop.run_in_executor(
                None, extract_audio, str(tmp_input), str(tmp_audio)
            )
        else:
            # Already audio — compress to keep under Whisper limit
            await loop.run_in_executor(
                None, compress_audio, str(tmp_input), str(tmp_audio)
            )

        # Update status
        db.update_video(video_id, {"status": "transcribing"})

        # Transcribe
        result = await loop.run_in_executor(None, transcribe, str(tmp_audio))

        # Generate SRT from segments
        srt_content = format_srt(result["segments"])

        # Store transcript
        db.update_video(video_id, {
            "transcript_text": result["text"],
            "transcript_segments": result["segments"],
            "status": "transcribed",
        })

        # Save SRT to upload_package placeholder so it's immediately available
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
        db.log_error("upload", str(e))
        # Update status to failed if record exists
        try:
            db.update_video(video_id, {"status": "failed"})
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    finally:
        # Always clean up temp files
        for path in [tmp_input, tmp_audio]:
            try:
                if path.exists():
                    path.unlink()
            except Exception:
                pass


@router.get("/upload/{video_id}/status")
async def get_upload_status(video_id: str):
    """Poll this to get current processing status."""
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
    """Get all videos for the dashboard."""
    videos = db.list_videos()
    return {"videos": videos}


@router.get("/videos/{video_id}")
async def get_video(video_id: str):
    """Get full video record including transcript."""
    video = db.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video
