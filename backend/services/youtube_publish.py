import json
import os
import secrets
from pathlib import Path
from urllib.parse import urlencode

import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"]
TOKEN_PATH = Path(__file__).parent.parent / "data" / "youtube_token.json"
_pending_states: set[str] = set()


def _client_config() -> tuple[str, str, str]:
    client_id = os.getenv("YOUTUBE_OAUTH_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_OAUTH_CLIENT_SECRET")
    redirect_uri = os.getenv("YOUTUBE_OAUTH_REDIRECT_URI", "http://127.0.0.1:8000/api/youtube/oauth/callback")
    if not client_id or not client_secret:
        raise RuntimeError("Set YOUTUBE_OAUTH_CLIENT_ID and YOUTUBE_OAUTH_CLIENT_SECRET in backend/.env to connect YouTube.")
    return client_id, client_secret, redirect_uri


def connection_status() -> dict:
    configured = bool(os.getenv("YOUTUBE_OAUTH_CLIENT_ID") and os.getenv("YOUTUBE_OAUTH_CLIENT_SECRET"))
    return {"configured": configured, "connected": configured and TOKEN_PATH.exists()}


def authorization_url() -> str:
    client_id, _, redirect_uri = _client_config()
    state = secrets.token_urlsafe(24)
    _pending_states.add(state)
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    })


def complete_authorization(code: str, state: str) -> None:
    if state not in _pending_states:
        raise RuntimeError("The YouTube connection request expired. Start it again from CreatorOS.")
    _pending_states.remove(state)
    client_id, client_secret, redirect_uri = _client_config()
    response = requests.post("https://oauth2.googleapis.com/token", data={
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }, timeout=20)
    if not response.ok:
        raise RuntimeError(f"Google authorization failed: {response.text}")
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(json.dumps(response.json()), encoding="utf-8")


def _service():
    if not TOKEN_PATH.exists():
        raise RuntimeError("Connect your YouTube channel before publishing or replying to comments.")
    client_id, client_secret, _ = _client_config()
    data = json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
    credentials = Credentials(
        token=data.get("access_token"), refresh_token=data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token", client_id=client_id,
        client_secret=client_secret, scopes=SCOPES,
    )
    return build("youtube", "v3", credentials=credentials)


def publish_video(source: Path, title: str, description: str, tags: list[str], privacy: str) -> dict:
    if source.suffix.lower() not in {".mp4", ".mov", ".avi", ".mkv", ".webm"}:
        raise RuntimeError("YouTube publishing requires a video file, not an audio-only upload.")
    if privacy not in {"private", "unlisted", "public"}:
        raise RuntimeError("Visibility must be private, unlisted, or public.")
    result = _service().videos().insert(
        part="snippet,status",
        body={"snippet": {"title": title[:100], "description": description, "tags": tags[:30], "categoryId": "22"},
              "status": {"privacyStatus": privacy}},
        media_body=MediaFileUpload(str(source), chunksize=8 * 1024 * 1024, resumable=True),
    ).execute()
    return {"youtube_video_id": result["id"], "url": f"https://www.youtube.com/watch?v={result['id']}"}


def upload_captions(video_id: str, srt_path: Path) -> None:
    _service().captions().insert(
        part="snippet",
        body={"snippet": {"videoId": video_id, "language": "en", "name": "CreatorOS captions", "isDraft": False}},
        media_body=MediaFileUpload(str(srt_path), mimetype="application/octet-stream", resumable=False),
    ).execute()


def reply_to_comment(parent_id: str, text: str) -> None:
    _service().comments().insert(
        part="snippet", body={"snippet": {"parentId": parent_id, "textOriginal": text}}
    ).execute()
