import os
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi

_youtube = None


def get_youtube():
    global _youtube
    if _youtube is None:
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            raise RuntimeError("YOUTUBE_API_KEY not set in .env")
        _youtube = build("youtube", "v3", developerKey=api_key)
    return _youtube


# ── Search ────────────────────────────────────────────────────────────────────

def search_videos(topic: str, max_results: int = 30) -> list[str]:
    """
    Search YouTube for videos on a topic.
    Returns list of video IDs ordered by view count.
    Costs: 100 units per call.
    """
    published_after = (
        datetime.now(timezone.utc) - timedelta(days=90)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    yt = get_youtube()
    response = yt.search().list(
        part="snippet",
        q=topic,
        type="video",
        order="viewCount",
        maxResults=max_results,
        publishedAfter=published_after,
    ).execute()

    return [item["id"]["videoId"] for item in response.get("items", [])]


# ── Video Metadata ─────────────────────────────────────────────────────────────

def get_videos_metadata(video_ids: list[str]) -> list[dict]:
    """
    Batch fetch metadata + stats for up to 50 videos.
    Returns list of video dicts.
    Costs: 1 unit per call regardless of count.
    """
    if not video_ids:
        return []

    # YouTube allows max 50 per call
    results = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        yt = get_youtube()
        response = yt.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(batch),
        ).execute()

        for item in response.get("items", []):
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})
            results.append({
                "video_id": item["id"],
                "title": snippet.get("title", ""),
                "description": snippet.get("description", "")[:500],
                "tags": snippet.get("tags", []),
                "channel_id": snippet.get("channelId", ""),
                "published_at": snippet.get("publishedAt", ""),
                "duration": item.get("contentDetails", {}).get("duration", ""),
                "view_count": int(stats.get("viewCount", 0)),
                "like_count": int(stats.get("likeCount", 0)),
                "comment_count": int(stats.get("commentCount", 0)),
            })
    return results


# ── Channel Stats ──────────────────────────────────────────────────────────────

def get_channel_subscriber_counts(channel_ids: list[str]) -> dict[str, int]:
    """
    Batch fetch subscriber counts.
    Returns {channel_id: subscriber_count}
    """
    if not channel_ids:
        return {}

    unique_ids = list(set(channel_ids))
    result = {}

    for i in range(0, len(unique_ids), 50):
        batch = unique_ids[i:i+50]
        yt = get_youtube()
        response = yt.channels().list(
            part="statistics",
            id=",".join(batch),
        ).execute()

        for item in response.get("items", []):
            subs = int(item.get("statistics", {}).get("subscriberCount", 1))
            result[item["id"]] = subs

    return result


# ── Comments ──────────────────────────────────────────────────────────────────

def get_video_comments(youtube_video_id: str, max_results: int = 100) -> list[dict]:
    """
    Fetch top comments for a YouTube video.
    Returns list of comment dicts.
    """
    try:
        yt = get_youtube()
        response = yt.commentThreads().list(
            part="snippet",
            videoId=youtube_video_id,
            maxResults=max_results,
            order="relevance",
        ).execute()

        comments = []
        for item in response.get("items", []):
            top = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "youtube_comment_id": item["id"],
                "youtube_video_id": youtube_video_id,
                "commenter_name": top.get("authorDisplayName", ""),
                "comment_text": top.get("textDisplay", ""),
                "posted_at": top.get("publishedAt", ""),
            })
        return comments
    except Exception:
        # Comments may be disabled on this video
        return []


# ── Video Stats (for dashboard) ───────────────────────────────────────────────

def get_video_stats(youtube_video_id: str) -> dict:
    """
    Get current stats for a single video.
    Used for dashboard analytics refresh.
    """
    try:
        yt = get_youtube()
        response = yt.videos().list(
            part="statistics",
            id=youtube_video_id,
        ).execute()

        items = response.get("items", [])
        if not items:
            return {}

        stats = items[0].get("statistics", {})
        return {
            "view_count": int(stats.get("viewCount", 0)),
            "like_count": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "like_ratio": round(
                int(stats.get("likeCount", 0)) / max(int(stats.get("viewCount", 1)), 1) * 100, 2
            ),
        }
    except Exception:
        return {}


# ── Competitor Transcripts ─────────────────────────────────────────────────────

def get_competitor_transcript(video_id: str) -> str | None:
    """
    Pull auto-generated transcript for a competitor video.
    Returns full text or None if unavailable.
    """
    try:
        segments = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
        return " ".join(s["text"] for s in segments)
    except Exception:
        return None


# ── Performance Scoring ────────────────────────────────────────────────────────

def calculate_performance_score(video: dict, subscriber_count: int) -> float:
    """
    Normalize video performance against channel size.
    A 50K-view video from a 3K-follower creator can outrank
    a 2M-view video from a 10M-follower creator.
    """
    views = video.get("view_count", 0)
    likes = video.get("like_count", 0)
    comments = video.get("comment_count", 0)
    subscribers = max(subscriber_count, 1)

    # Parse days since published
    try:
        published = datetime.fromisoformat(
            video.get("published_at", "").replace("Z", "+00:00")
        )
        days_old = max((datetime.now(timezone.utc) - published).days, 1)
    except Exception:
        days_old = 30

    view_ratio = views / subscribers
    engagement_rate = (likes + comments) / max(views, 1)
    recency_boost = 1 + (1 / days_old)

    score = (view_ratio * 0.4) + (engagement_rate * 0.4) + (recency_boost * 0.2)
    return round(score, 4)
