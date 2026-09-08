from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import database as db, claude, youtube as yt_service
from services import youtube_publish

router = APIRouter(prefix="/api", tags=["dashboard"])


# ── Analytics ─────────────────────────────────────────────────────────────────

@router.get("/dashboard/{video_id}/analytics")
async def get_analytics(video_id: str):
    """
    Get current YouTube analytics for a video.
    Reads youtube_video_id stored on the video record.
    """
    video = db.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    youtube_video_id = video.get("youtube_video_id")
    if not youtube_video_id:
        return {
            "video_id": video_id,
            "message": "No YouTube video ID linked yet. Add it after uploading to YouTube.",
            "stats": None,
        }

    stats = yt_service.get_video_stats(youtube_video_id)
    return {"video_id": video_id, "stats": stats}


class LinkYouTubeRequest(BaseModel):
    youtube_video_id: str


@router.post("/dashboard/{video_id}/link-youtube")
async def link_youtube_video(video_id: str, body: LinkYouTubeRequest):
    """Link a YouTube video ID to a CreatorOS video record after upload."""
    video = db.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    db.update_video(video_id, {"youtube_video_id": body.youtube_video_id})
    return {"video_id": video_id, "youtube_video_id": body.youtube_video_id, "linked": True}


# ── Comments ──────────────────────────────────────────────────────────────────

@router.get("/dashboard/{video_id}/comments")
async def get_comments(video_id: str, status: str = None):
    """
    Get all comments for a video with AI draft replies.
    Fetches fresh comments from YouTube and drafts replies for new ones.
    """
    video = db.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    youtube_video_id = video.get("youtube_video_id")

    # Pull fresh comments from YouTube if linked
    if youtube_video_id:
        fresh_comments = yt_service.get_video_comments(youtube_video_id, max_results=100)

        # Add video_id to each comment
        for c in fresh_comments:
            c["video_id"] = video_id

        # Upsert into Supabase (won't duplicate)
        db.upsert_comments(fresh_comments)

        # Draft replies for comments that don't have one
        all_comments = db.get_comments(video_id)
        needs_draft = [c for c in all_comments if not c.get("ai_draft_reply")]

        if needs_draft:
            drafts = claude.draft_comment_replies(needs_draft[:20])  # batch of 20
            for draft in drafts:
                db.update_comment(
                    draft["comment_id"],
                    {"ai_draft_reply": draft["draft_reply"]}
                )

    comments = db.get_comments(video_id, status=status)
    return {
        "video_id": video_id,
        "total": len(comments),
        "comments": comments,
    }


class ApproveCommentRequest(BaseModel):
    reply_text: str


@router.post("/dashboard/{video_id}/comments/{comment_id}/approve")
async def approve_comment(video_id: str, comment_id: str, body: ApproveCommentRequest):
    """
    Approve a comment reply. Marks as approved in DB.
    Note: actual posting to YouTube requires OAuth token (added in next iteration).
    """
    comment = next((c for c in db.get_comments(video_id) if c["id"] == comment_id), None)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    try:
        youtube_publish.reply_to_comment(comment["youtube_comment_id"], body.reply_text)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not post reply: {exc}")
    db.update_comment(comment_id, {
        "ai_draft_reply": body.reply_text,
        "status": "approved",
    })
    return {"comment_id": comment_id, "status": "approved"}


@router.post("/dashboard/{video_id}/comments/{comment_id}/skip")
async def skip_comment(video_id: str, comment_id: str):
    """Mark a comment as skipped."""
    db.update_comment(comment_id, {"status": "skipped"})
    return {"comment_id": comment_id, "status": "skipped"}


@router.post("/dashboard/{video_id}/comments/batch-approve")
async def batch_approve_comments(video_id: str):
    """Post every approved draft that can be sent to the connected channel."""
    pending = db.get_comments(video_id, status="pending")
    approved_count = 0
    failures = []
    for comment in pending:
        if comment.get("ai_draft_reply"):
            try:
                youtube_publish.reply_to_comment(comment["youtube_comment_id"], comment["ai_draft_reply"])
                db.update_comment(comment["id"], {"status": "approved"})
                approved_count += 1
            except Exception as exc:
                failures.append({"comment_id": comment["id"], "error": str(exc)})
    return {"approved_count": approved_count, "failures": failures}


# ── Alerts ────────────────────────────────────────────────────────────────────

class CreateAlertRequest(BaseModel):
    condition_type: str   # views_threshold | engagement_drop | comment_spike
    threshold_value: float


@router.post("/dashboard/{video_id}/alerts")
async def create_alert(video_id: str, body: CreateAlertRequest):
    """Create a new alert condition for a video."""
    video = db.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    alert = db.create_alert({
        "video_id": video_id,
        "condition_type": body.condition_type,
        "threshold_value": body.threshold_value,
    })
    return alert


@router.get("/dashboard/{video_id}/alerts")
async def get_alerts(video_id: str):
    """Get all alerts for a video."""
    alerts = db.get_alerts(video_id)
    return {"video_id": video_id, "alerts": alerts}


@router.delete("/dashboard/{video_id}/alerts/{alert_id}")
async def delete_alert(video_id: str, alert_id: str):
    """Delete an alert."""
    db.delete_alert(alert_id)
    return {"alert_id": alert_id, "deleted": True}


# ── Notifications ─────────────────────────────────────────────────────────────

@router.get("/notifications")
async def get_notifications(video_id: str = None):
    """Get unread notifications, optionally filtered by video."""
    notifications = db.get_notifications(video_id=video_id)
    return {"notifications": notifications, "count": len(notifications)}


@router.post("/notifications/{notification_id}/read")
async def mark_read(notification_id: str):
    """Mark a notification as read."""
    db.mark_notification_read(notification_id)
    return {"notification_id": notification_id, "read": True}
