import os
from supabase import create_client, Client

_client: Client = None


def get_db() -> Client:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
        _client = create_client(url, key)
    return _client


# ── Videos ────────────────────────────────────────────────────────────────────

def create_video(data: dict) -> dict:
    db = get_db()
    result = db.table("videos").insert(data).execute()
    return result.data[0]


def get_video(video_id: str) -> dict | None:
    db = get_db()
    result = db.table("videos").select("*").eq("id", video_id).execute()
    return result.data[0] if result.data else None


def update_video(video_id: str, data: dict) -> dict:
    db = get_db()
    result = db.table("videos").update(data).eq("id", video_id).execute()
    return result.data[0]


def list_videos(user_id: str = None) -> list:
    db = get_db()
    query = db.table("videos").select("*").order("created_at", desc=True)
    if user_id:
        query = query.eq("user_id", user_id)
    return query.execute().data


# ── Upload Packages ────────────────────────────────────────────────────────────

def save_upload_package(data: dict) -> dict:
    db = get_db()
    result = db.table("upload_packages").insert(data).execute()
    return result.data[0]


def get_upload_package(video_id: str) -> dict | None:
    db = get_db()
    result = (
        db.table("upload_packages")
        .select("*")
        .eq("video_id", video_id)
        .execute()
    )
    return result.data[0] if result.data else None


# ── Research Cache ─────────────────────────────────────────────────────────────

def get_research_cache(cache_key: str) -> dict | None:
    db = get_db()
    result = (
        db.table("research_cache")
        .select("data")
        .eq("cache_key", cache_key)
        .gt("expires_at", "now()")
        .execute()
    )
    return result.data[0]["data"] if result.data else None


def set_research_cache(cache_key: str, data: dict, expires_at: str) -> None:
    db = get_db()
    db.table("research_cache").upsert(
        {"cache_key": cache_key, "data": data, "expires_at": expires_at},
        on_conflict="cache_key",
    ).execute()


# ── Comments ──────────────────────────────────────────────────────────────────

def upsert_comments(comments: list) -> None:
    db = get_db()
    if comments:
        db.table("comments").upsert(
            comments, on_conflict="youtube_comment_id"
        ).execute()


def get_comments(video_id: str, status: str = None) -> list:
    db = get_db()
    query = (
        db.table("comments")
        .select("*")
        .eq("video_id", video_id)
        .order("posted_at", desc=True)
    )
    if status:
        query = query.eq("status", status)
    return query.execute().data


def update_comment(comment_id: str, data: dict) -> dict:
    db = get_db()
    result = db.table("comments").update(data).eq("id", comment_id).execute()
    return result.data[0]


# ── Clip Opportunities ─────────────────────────────────────────────────────────

def save_clip_opportunity(data: dict) -> dict:
    db = get_db()
    result = db.table("clip_opportunities").insert(data).execute()
    return result.data[0]


def get_clip_opportunities(video_id: str) -> list:
    db = get_db()
    return (
        db.table("clip_opportunities")
        .select("*")
        .eq("video_id", video_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )


def update_clip_opportunity(clip_id: str, data: dict) -> dict:
    db = get_db()
    result = (
        db.table("clip_opportunities").update(data).eq("id", clip_id).execute()
    )
    return result.data[0]


# ── Alerts ────────────────────────────────────────────────────────────────────

def create_alert(data: dict) -> dict:
    db = get_db()
    result = db.table("alerts").insert(data).execute()
    return result.data[0]


def get_alerts(video_id: str) -> list:
    db = get_db()
    return (
        db.table("alerts")
        .select("*")
        .eq("video_id", video_id)
        .execute()
        .data
    )


def delete_alert(alert_id: str) -> None:
    db = get_db()
    db.table("alerts").delete().eq("id", alert_id).execute()


# ── Notifications ─────────────────────────────────────────────────────────────

def create_notification(data: dict) -> dict:
    db = get_db()
    result = db.table("notifications").insert(data).execute()
    return result.data[0]


def get_notifications(video_id: str = None) -> list:
    db = get_db()
    query = (
        db.table("notifications")
        .select("*")
        .eq("read", False)
        .order("created_at", desc=True)
    )
    if video_id:
        query = query.eq("video_id", video_id)
    return query.execute().data


def mark_notification_read(notification_id: str) -> None:
    db = get_db()
    db.table("notifications").update({"read": True}).eq("id", notification_id).execute()


# ── IP Rate Limiting ──────────────────────────────────────────────────────────

def check_ip_limit(ip: str, endpoint: str, max_per_day: int) -> bool:
    """Returns True if request is allowed, False if limit exceeded."""
    db = get_db()
    result = (
        db.table("request_log")
        .select("id", count="exact")
        .eq("ip_address", ip)
        .eq("endpoint", endpoint)
        .gte("created_at", "now() - interval '1 day'")
        .execute()
    )
    count = result.count or 0
    if count >= max_per_day:
        return False
    db.table("request_log").insert({"ip_address": ip, "endpoint": endpoint}).execute()
    return True


# ── Error Logging ─────────────────────────────────────────────────────────────

def log_error(context: str, error: str) -> None:
    try:
        db = get_db()
        db.table("error_log").insert({"context": context, "error_message": error}).execute()
    except Exception:
        pass  # never let error logging crash the app
