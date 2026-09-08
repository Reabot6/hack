"""
Background worker — runs every 2 hours.
For each active video:
  1. Pull fresh comments from YouTube
  2. Detect clip opportunities
  3. Draft replies for new comments
  4. Check alert conditions
"""
from services import database as db, claude, youtube as yt_service


def run_for_all_videos():
    """Entry point called by scheduler every 2 hours."""
    try:
        videos = db.list_videos()
        active = [v for v in videos if v.get("status") == "packaged"]
        print(f"[Worker] Running for {len(active)} active videos")

        for video in active:
            try:
                _process_video(video)
            except Exception as e:
                db.log_error(f"worker_video_{video['id']}", str(e))
                print(f"[Worker] Error processing video {video['id']}: {e}")

    except Exception as e:
        db.log_error("worker_main", str(e))
        print(f"[Worker] Fatal error: {e}")


def _process_video(video: dict):
    video_id = video["id"]
    youtube_video_id = video.get("youtube_video_id")
    print(f"[Worker] Processing video {video_id}")

    # 1. Pull fresh comments if YouTube linked
    if youtube_video_id:
        fresh_comments = yt_service.get_video_comments(youtube_video_id, max_results=100)
        for c in fresh_comments:
            c["video_id"] = video_id
        db.upsert_comments(fresh_comments)

    # 2. Check for clip opportunities
    all_comments = db.get_comments(video_id)
    segments = video.get("transcript_segments", [])

    if len(all_comments) >= 5 and segments:
        opportunities = claude.detect_clip_opportunities(segments, all_comments)

        # Only create new opportunities (check by timestamp range)
        existing = db.get_clip_opportunities(video_id)
        existing_ranges = {
            (o["start_seconds"], o["end_seconds"]) for o in existing
        }

        topic = video.get("topic", "content")
        for opp in opportunities:
            start = opp.get("start_seconds", 0)
            end = opp.get("end_seconds", 0)

            if (start, end) in existing_ranges:
                continue  # Already detected this one

            # Build segment text
            segment_text = " ".join(
                s["text"] for s in segments
                if s.get("start", 0) >= start - 5 and s.get("end", 0) <= end + 5
            )

            try:
                clip_package = claude.generate_clip_package(
                    segment_text=segment_text,
                    video_topic=topic,
                    why_it_resonated=opp.get("why_it_resonated", ""),
                )
            except Exception:
                clip_package = {}

            db.save_clip_opportunity({
                "video_id": video_id,
                "start_seconds": start,
                "end_seconds": end,
                "comment_count": opp.get("comment_count", 0),
                "why_it_resonated": opp.get("why_it_resonated", ""),
                "example_comments": opp.get("example_comments", []),
                "clip_package": clip_package,
                "status": "pending_approval",
            })

            db.create_notification({
                "video_id": video_id,
                "type": "clip_opportunity",
                "message": (
                    f"🔥 {opp.get('comment_count', 0)} comments referencing "
                    f"{int(start//60):02d}:{int(start%60):02d} — clip package ready"
                ),
            })

    # 3. Draft replies for any new comments without drafts
    needs_draft = [c for c in all_comments if not c.get("ai_draft_reply")]
    if needs_draft:
        try:
            drafts = claude.draft_comment_replies(needs_draft[:20])
            for draft in drafts:
                db.update_comment(draft["comment_id"], {"ai_draft_reply": draft["draft_reply"]})
        except Exception as e:
            db.log_error(f"worker_draft_replies_{video_id}", str(e))

    # 4. Check alert conditions
    if youtube_video_id:
        _check_alerts(video_id, youtube_video_id)

    print(f"[Worker] Done with video {video_id}")


def _check_alerts(video_id: str, youtube_video_id: str):
    alerts = db.get_alerts(video_id)
    untriggered = [a for a in alerts if not a.get("triggered")]
    if not untriggered:
        return

    stats = yt_service.get_video_stats(youtube_video_id)
    if not stats:
        return

    for alert in untriggered:
        condition = alert.get("condition_type")
        threshold = float(alert.get("threshold_value", 0))
        triggered = False
        message = ""

        if condition == "views_threshold" and stats.get("view_count", 0) >= threshold:
            triggered = True
            message = f"🎉 Your video crossed {int(threshold):,} views!"

        elif condition == "engagement_drop" and stats.get("like_ratio", 100) < threshold:
            triggered = True
            message = f"⚠️ Engagement dropped below {threshold}%"

        elif condition == "comment_spike":
            comments = db.get_comments(video_id)
            if len(comments) >= threshold:
                triggered = True
                message = f"💬 Your video has {len(comments)} comments — reply now for algorithm boost"

        if triggered:
            db.get_db().table("alerts").update({
                "triggered": True,
                "triggered_at": "now()",
            }).eq("id", alert["id"]).execute()

            db.create_notification({
                "video_id": video_id,
                "type": "alert",
                "message": message,
            })
