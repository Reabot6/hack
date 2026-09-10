from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Request
from services import database as db
from services import claude, youtube as yt_service

router = APIRouter(prefix="/api", tags=["generate"])


@router.post("/generate/{video_id}")
async def generate_package(video_id: str, request: Request):
    """
    Phase 2: Research niche + generate complete upload package.
    Uses cached research if available for same topic today.
    """
    video = db.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if video["status"] not in ("transcribed", "researched", "packaged"):
        raise HTTPException(status_code=400, detail="Video must be transcribed first")

    transcript = video.get("transcript_text", "")
    segments = video.get("transcript_segments", [])

    try:
        # Step 1: Extract topic from transcript
        topic_data = claude.extract_topic(transcript)
        topic = topic_data.get("topic", "general content")
        keywords = topic_data.get("keywords", [])

        db.update_video(video_id, {
            "topic": topic,
            "niche": topic_data.get("niche", ""),
            "keywords": keywords,
            "status": "researching",
        })

        # Step 2: Check research cache
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cache_key = f"{topic}_{today}"
        research_data = db.get_research_cache(cache_key)
        research_source = "cached" if research_data else "live"

        if not research_data:
            # Step 3: Pull competitor videos
            search_query = f"{topic} {' '.join(keywords[:3])}"
            video_ids = yt_service.search_videos(search_query, max_results=30)

            if not video_ids:
                raise RuntimeError("No competitor videos were returned for this topic")

            # Step 4: Fetch metadata in batch
            videos_meta = yt_service.get_videos_metadata(video_ids)

            # Step 5: Get subscriber counts and calculate performance scores
            channel_ids = [v["channel_id"] for v in videos_meta]
            sub_counts = yt_service.get_channel_subscriber_counts(channel_ids)

            for v in videos_meta:
                subs = sub_counts.get(v["channel_id"], 1000)
                v["performance_score"] = yt_service.calculate_performance_score(v, subs)

            # Sort by performance score, take top 20
            videos_meta.sort(key=lambda x: x["performance_score"], reverse=True)
            top_videos = videos_meta[:20]

            # Step 6: Get transcripts for top videos
            videos_for_analysis = []
            for v in top_videos:
                transcript_text = yt_service.get_competitor_transcript(v["video_id"])
                transcript_summary = (transcript_text or "")[:500]  # first 500 chars

                # Get top comments
                comments = yt_service.get_video_comments(v["video_id"], max_results=20)
                top_comment_texts = [c["comment_text"] for c in comments[:10]]

                videos_for_analysis.append({
                    "title": v["title"],
                    "description": v["description"],
                    "tags": v["tags"][:20],
                    "transcript_summary": transcript_summary,
                    "view_count": v["view_count"],
                    "performance_score": v["performance_score"],
                    "top_comments": top_comment_texts,
                })

            # Step 7: Analyze patterns with Claude
            research_data = claude.analyze_patterns(videos_for_analysis)

            # Step 8: Cache for today
            expires_at = (
                datetime.now(timezone.utc) + timedelta(days=1)
            ).isoformat()
            db.set_research_cache(cache_key, research_data, expires_at)

        db.update_video(video_id, {"status": "generating"})

        # Step 9: Generate upload package
        package = claude.generate_upload_package(transcript, segments, research_data)

        # Step 10: Save package (update existing record created during upload)
        existing = db.get_upload_package(video_id)
        if existing:
            db.get_db().table("upload_packages").update({
                "titles": package.get("titles", []),
                "description": package.get("description", ""),
                "tags": package.get("tags", []),
                "chapters": package.get("chapters", ""),
                "shorts_moments": package.get("shorts_moments", []),
            }).eq("video_id", video_id).execute()
        else:
            db.save_upload_package({
                "video_id": video_id,
                "titles": package.get("titles", []),
                "description": package.get("description", ""),
                "tags": package.get("tags", []),
                "chapters": package.get("chapters", ""),
                "shorts_moments": package.get("shorts_moments", []),
            })

        db.update_video(video_id, {"status": "packaged"})

        return {
            "video_id": video_id,
            "status": "packaged",
            "topic": topic,
            "research_source": research_source,
            "package": package,
        }

    except HTTPException:
        raise
    except Exception as e:
        # A YouTube quota or transcript-provider outage must not make a
        # creator's upload unusable. Generate from the creator's transcript
        # with an explicitly labelled empty research context instead.
        db.log_error("generate.research", str(e))
        try:
            fallback_research = {
                "winning_hooks": [], "winning_structures": [], "common_tags": [],
                "description_patterns": [], "content_gaps": [], "audience_questions": [],
                "average_duration_seconds": 0, "dominant_tone": "creator-led",
                "note": "Live YouTube research was temporarily unavailable.",
            }
            db.update_video(video_id, {"status": "generating"})
            package = claude.generate_upload_package(transcript, segments, fallback_research)
            existing = db.get_upload_package(video_id)
            package_fields = {
                "titles": package.get("titles", []), "description": package.get("description", ""),
                "tags": package.get("tags", []), "chapters": package.get("chapters", ""),
                "shorts_moments": package.get("shorts_moments", []),
            }
            if existing:
                db.get_db().table("upload_packages").update(package_fields).eq("video_id", video_id).execute()
            else:
                db.save_upload_package({"video_id": video_id, **package_fields})
            db.update_video(video_id, {"status": "packaged"})
            return {
                "video_id": video_id, "status": "packaged", "topic": video.get("topic", ""),
                "research_source": "transcript_only", "package": package,
                "notice": "Live YouTube research was unavailable, so this package was generated from your transcript only.",
            }
        except Exception as fallback_error:
            db.log_error("generate.fallback", str(fallback_error))
            db.update_video(video_id, {"status": "transcribed"})
            raise HTTPException(status_code=500, detail="We transcribed your file, but could not generate the package. Please retry in a moment.")


@router.get("/generate/{video_id}/package")
async def get_package(video_id: str):
    """Fetch existing upload package for a video."""
    package = db.get_upload_package(video_id)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found. Run generation first.")
    return package
