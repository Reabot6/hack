# CreatorOS — API Reference + Gotchas

## YouTube Data API v3

### Setup
```
Console: console.developers.google.com
Enable: YouTube Data API v3
Create: API Key (restrict to YouTube Data API)
Quota: 10,000 units/day free
```

### Endpoints We Use

```python
# SEARCH — find competitor videos
# Cost: 100 units per call
GET https://www.googleapis.com/youtube/v3/search
params:
  part: snippet
  q: {topic}
  type: video
  order: viewCount
  maxResults: 30
  publishedAfter: {90_days_ago_RFC3339}
  key: {API_KEY}

# VIDEOS — get metadata + stats (batch up to 50)
# Cost: 1 unit per call regardless of how many IDs
GET https://www.googleapis.com/youtube/v3/videos
params:
  part: snippet,statistics,contentDetails
  id: {comma_separated_video_ids}  # up to 50
  key: {API_KEY}

# CHANNELS — get subscriber count
# Cost: 1 unit per call
GET https://www.googleapis.com/youtube/v3/channels
params:
  part: statistics
  id: {channel_id}
  key: {API_KEY}

# COMMENTS — read comments
# Cost: 1 unit per call
GET https://www.googleapis.com/youtube/v3/commentThreads
params:
  part: snippet
  videoId: {video_id}
  maxResults: 100
  order: relevance
  key: {API_KEY}

# POST COMMENT REPLY — requires OAuth (not API key)
# Cost: 50 units per insert
POST https://www.googleapis.com/youtube/v3/comments
  requires: OAuth 2.0 user token
  body: {snippet: {parentId, textOriginal}}
```

### Critical Gotchas

```
1. COMMENT REPLIES NEED OAUTH
   Reading comments: API key works fine
   Posting replies: needs user OAuth token
   
   Solution for hackathon:
   Add Google OAuth login button
   Store user token in Supabase (encrypted)
   Use token only for posting replies
   Reading is still API key

2. SEARCH QUOTA IS EXPENSIVE
   search.list = 100 units (1% of daily budget)
   Maximum 100 research requests per day total
   Always cache results — never search same topic twice same day

3. publishedAfter FORMAT
   Must be RFC3339: "2024-06-01T00:00:00Z"
   Not a regular date string

4. BATCH VIDEO REQUESTS
   Always batch — never loop individual video ID requests
   ids: "id1,id2,id3,..." up to 50 per call
   Saves 49 units vs fetching one at a time

5. COMMENTS MAY BE DISABLED
   Some videos have comments disabled
   Always wrap in try/catch
   If comments unavailable: skip that video silently
```

---

## Whisper API (OpenAI)

### Setup
```
API Key: platform.openai.com
Model: whisper-1
Cost: $0.006 per minute
```

### Usage
```python
import openai

def transcribe_audio(audio_path: str) -> dict:
    with open(audio_path, "rb") as f:
        response = openai.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",  # includes timestamps
            timestamp_granularities=["segment"]
        )
    return {
        "text": response.text,
        "segments": [
            {
                "start": s.start,
                "end": s.end,
                "text": s.text
            }
            for s in response.segments
        ]
    }
```

### Gotchas
```
1. FILE SIZE LIMIT: 25MB max
   Solution: compress audio with FFmpeg before sending
   ffmpeg -i input.mp3 -b:a 64k compressed.mp3
   Reduces file size ~4x

2. SUPPORTED FORMATS: mp3, mp4, mpeg, mpga, m4a, wav, webm
   We convert everything to mp3 first with FFmpeg

3. VERBOSE_JSON gives segments with timestamps
   Use this — not plain text — we need timestamps for chapters
   and clip moment matching

4. CACHE TRANSCRIPTS
   Never transcribe same file twice
   Store in Supabase permanently by video_id
```

---

## FFmpeg (Audio Extraction)

### Installation
```bash
# Ubuntu/Debian (server)
apt-get install ffmpeg

# Mac (local dev)
brew install ffmpeg
```

### Commands We Use
```python
import subprocess

def extract_audio(video_path: str, output_path: str):
    subprocess.run([
        "ffmpeg",
        "-i", video_path,
        "-vn",              # no video
        "-acodec", "mp3",   # mp3 output
        "-b:a", "64k",      # compress to 64kbps (small file)
        "-y",               # overwrite if exists
        output_path
    ], check=True)

def compress_audio(audio_path: str, output_path: str):
    subprocess.run([
        "ffmpeg",
        "-i", audio_path,
        "-b:a", "64k",
        "-y",
        output_path
    ], check=True)
```

---

## youtube-transcript-api (Python)

### Installation
```bash
pip install youtube-transcript-api
```

### Usage
```python
from youtube_transcript_api import YouTubeTranscriptApi

def get_competitor_transcript(video_id: str) -> str:
    try:
        segments = YouTubeTranscriptApi.get_transcript(video_id)
        # segments: [{text, start, duration}]
        full_text = " ".join([s["text"] for s in segments])
        return full_text
    except Exception:
        # transcript unavailable or disabled
        return None
```

### Gotchas
```
1. NO AUTH NEEDED — mimics web request
   Works on any video with auto-captions enabled

2. NOT ALL VIDEOS HAVE TRANSCRIPTS
   Always wrap in try/catch
   Return None if unavailable, skip that video

3. MAY BREAK IF YOUTUBE CHANGES WEB FORMAT
   It's unofficial — has broken before and been fixed
   If it fails: fall back to title + description only for analysis
   
4. LANGUAGE
   Default returns English if available
   Can specify: get_transcript(id, languages=["en"])
```

---

## Anthropic Claude API

### Setup
```
API Key: console.anthropic.com
Model: claude-sonnet-4-6
```

### Key Prompts Structure

```python
import anthropic

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def call_claude(system_prompt: str, user_message: str) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )
    return response.content[0].text
```

### Prompt Templates

```python
# TOPIC EXTRACTION
EXTRACT_TOPIC_PROMPT = """
You are analyzing a video transcript.
Return ONLY a JSON object with no other text:
{
  "topic": "main topic in 5 words or less",
  "niche": "content niche (fitness/finance/tech/etc)",
  "keywords": ["keyword1", "keyword2", ...10 total]
}
"""

# PATTERN ANALYSIS
ANALYZE_PATTERNS_PROMPT = """
You are a content intelligence analyst.
Analyze these top-performing YouTube videos and find patterns.
Return ONLY a JSON object:
{
  "winning_hooks": [{"pattern": "...", "example": "..."}],
  "winning_structures": ["structure description"],
  "common_tags": ["tag1", "tag2"],
  "description_patterns": ["pattern description"],
  "content_gaps": ["gap description"],
  "audience_questions": ["question from comments"],
  "average_duration_seconds": 0,
  "dominant_tone": "educational|entertainment|personal"
}
"""

# UPLOAD PACKAGE GENERATION
GENERATE_PACKAGE_PROMPT = """
You are a YouTube growth strategist.
Given a creator's transcript and research on what works in their niche,
generate a complete upload package.
Return ONLY a JSON object:
{
  "titles": [
    {"title": "...", "reasoning": "...", "rank": 1},
    ... 5 total
  ],
  "description": "full description text",
  "tags": ["tag1", "tag2", ...30 total],
  "chapters": "00:00 Intro\n01:23 Topic\n...",
  "shorts_moments": [
    {
      "start_seconds": 0,
      "end_seconds": 0,
      "why_it_works": "...",
      "standalone": true
    }
    ... 3 total
  ]
}
"""

# CLIP OPPORTUNITY DETECTION
DETECT_CLIPS_PROMPT = """
You are analyzing YouTube comments to find which moments in a video
are resonating most with the audience.

Given the video transcript (with timestamps) and all comments,
find moments referenced by 5 or more comments.

Return ONLY a JSON array:
[
  {
    "moment_description": "what they are referencing",
    "start_seconds": 0,
    "end_seconds": 0,
    "comment_count": 0,
    "example_comments": ["comment1", "comment2", "comment3"],
    "why_it_resonated": "one sentence"
  }
]

Return empty array [] if no moments meet the threshold.
"""

# COMMENT REPLY DRAFTS
DRAFT_REPLIES_PROMPT = """
You are helping a YouTube creator reply to comments.
Draft genuine, human replies (not robotic or overly positive).
Match a conversational tone. Keep replies under 3 sentences.
Return ONLY a JSON array:
[
  {
    "comment_id": "...",
    "draft_reply": "..."
  }
]
"""
```

### Gotchas
```
1. ALWAYS REQUEST JSON OUTPUT
   Tell Claude to return ONLY JSON with no other text
   Still wrap JSON.parse in try/catch
   
2. LARGE TRANSCRIPTS
   30 video transcripts may be large
   Summarize each transcript to 500 words before batching
   Then send all summaries in one call

3. RATE LIMITS
   claude-sonnet-4-6: 50 requests/min on most plans
   For batch comment drafting: chunk into groups of 20
```

---

## Supabase

### Setup
```
Create project: supabase.com
Get: SUPABASE_URL and service_role key (not anon)
Run: schema.sql from db/schema.sql
Enable: Supabase Storage for temp file uploads
```

### Python Client
```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Insert
supabase.table("videos").insert({...}).execute()

# Select
supabase.table("videos").select("*").eq("id", video_id).execute()

# Update
supabase.table("videos").update({...}).eq("id", video_id).execute()

# Cache check
result = supabase.table("research_cache")\
  .select("data")\
  .eq("cache_key", cache_key)\
  .gt("expires_at", "now()")\
  .execute()
```

---

## APScheduler (Background Worker)

### Setup
```bash
pip install apscheduler
```

### Usage
```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('interval', hours=2)
def run_background_worker():
    # pull all active videos
    # for each: check comments, detect clips, draft replies, check alerts
    pass

scheduler.start()
# attach to FastAPI lifespan event
```
