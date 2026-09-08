from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import database as db, claude, youtube as yt_service
from services.media import render_vertical_clip

router = APIRouter(prefix="/api", tags=["clips"])


@router.post("/clips/{video_id}/detect")
async def detect_clips(video_id: str):
    """
    Manually trigger clip opportunity detection for a video.
    The background worker runs this automatically every 2 hours.
    """
    video = db.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    transcript_segments = video.get("transcript_segments", [])
    if not transcript_segments:
        raise HTTPException(status_code=400, detail="No transcript found. Upload and transcribe first.")

    # Get all comments for this video
    comments = db.get_comments(video_id)
    if len(comments) < 5:
        return {
            "video_id": video_id,
            "message": "Not enough comments yet (need at least 5). Check back later.",
            "opportunities": [],
        }

    # Detect opportunities using Claude
    opportunities = claude.detect_clip_opportunities(transcript_segments, comments)

    if not opportunities:
        return {
            "video_id": video_id,
            "message": "No clip opportunities detected yet. Comments don't reference specific moments yet.",
            "opportunities": [],
        }

    # Generate clip packages and save each opportunity
    saved_opportunities = []
    topic = video.get("topic", "content")

    for opp in opportunities:
        # Find the transcript text for this segment
        start = opp.get("start_seconds", 0)
        end = opp.get("end_seconds", 60)
        segment_text = _extract_segment_text(transcript_segments, start, end)

        # Generate posting package
        try:
            clip_package = claude.generate_clip_package(
                segment_text=segment_text,
                video_topic=topic,
                why_it_resonated=opp.get("why_it_resonated", ""),
            )
        except Exception:
            clip_package = {}

        # Save to database
        saved = db.save_clip_opportunity({
            "video_id": video_id,
            "start_seconds": opp.get("start_seconds"),
            "end_seconds": opp.get("end_seconds"),
            "comment_count": opp.get("comment_count", 0),
            "why_it_resonated": opp.get("why_it_resonated", ""),
            "example_comments": opp.get("example_comments", []),
            "clip_package": clip_package,
            "status": "pending_approval",
        })
        # Render the actual vertical asset when a source video exists. A failed
        # render never discards the useful audience-signal recommendation.
        try:
            rendered = render_vertical_clip(
                video_id, saved["id"], float(opp.get("start_seconds", 0)),
                float(opp.get("end_seconds", 60)), transcript_segments,
            )
            clip_package["rendered_url"] = f"/media/{rendered.name}"
            saved = db.update_clip_opportunity(saved["id"], {"clip_package": clip_package})
        except Exception as render_error:
            clip_package["render_error"] = str(render_error)
            saved = db.update_clip_opportunity(saved["id"], {"clip_package": clip_package})

        # Create notification
        db.create_notification({
            "video_id": video_id,
            "type": "clip_opportunity",
            "message": (
                f"🔥 Clip opportunity detected: "
                f"{opp.get('comment_count', 0)} comments referencing "
                f"{_format_timestamp(opp.get('start_seconds', 0))}-"
                f"{_format_timestamp(opp.get('end_seconds', 0))}"
            ),
        })

        saved_opportunities.append(saved)

    return {
        "video_id": video_id,
        "opportunities_found": len(saved_opportunities),
        "opportunities": saved_opportunities,
    }


@router.get("/clips/{video_id}")
async def get_clips(video_id: str):
    """Get all clip opportunities for a video."""
    opportunities = db.get_clip_opportunities(video_id)
    return {
        "video_id": video_id,
        "clips": opportunities,
    }


class UpdateClipRequest(BaseModel):
    status: str  # approved | scheduled | dismissed
    scheduled_for: str = None


@router.patch("/clips/{video_id}/{clip_id}")
async def update_clip(video_id: str, clip_id: str, body: UpdateClipRequest):
    """Update clip status — approve, schedule, or dismiss."""
    update_data = {"status": body.status}
    if body.scheduled_for:
        update_data["scheduled_for"] = body.scheduled_for

    clip = db.update_clip_opportunity(clip_id, update_data)
    return clip


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_segment_text(segments: list, start: float, end: float) -> str:
    """Extract transcript text between two timestamps."""
    matching = [
        s["text"] for s in segments
        if s.get("start", 0) >= start - 5 and s.get("end", 0) <= end + 5
    ]
    return " ".join(matching) if matching else ""


def _format_timestamp(seconds: float) -> str:
    """Format seconds as MM:SS."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"
