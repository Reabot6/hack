import os
import json
import re
import random
from groq import Groq

# `llama-3.3-70b-versatile` was retired for Groq free/developer accounts.
# Keep this configurable so deployments can select an enabled Groq model.
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

def get_client():
    keys = [
        os.getenv("GROQ_API_KEY_1"),
        os.getenv("GROQ_API_KEY_2"),
        os.getenv("GROQ_API_KEY_3"),
        os.getenv("GROQ_API_KEY_4"),
        os.getenv("GROQ_API_KEY_5"),
    ]
    available = [k for k in keys if k]
    if not available:
        raise RuntimeError("No Groq API keys found in .env")
    key = random.choice(available)
    return Groq(api_key=key)

def _call(system: str, user: str, max_tokens: int = 4096) -> str:
    # Try each key on rate limit
    keys = [
        os.getenv("GROQ_API_KEY_1"),
        os.getenv("GROQ_API_KEY_2"),
        os.getenv("GROQ_API_KEY_3"),
        os.getenv("GROQ_API_KEY_4"),
        os.getenv("GROQ_API_KEY_5"),
    ]
    available = [k for k in keys if k]
    random.shuffle(available)

    last_error = None
    for key in available:
        try:
            client = Groq(api_key=key)
            response = client.chat.completions.create(
                model=MODEL,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            last_error = e
            if "rate_limit" in str(e).lower():
                continue
            raise e

    raise RuntimeError(f"All Groq keys exhausted: {last_error}")

def _parse_json(raw: str) -> dict | list:
    cleaned = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
    # Find first { or [
    start = min(
        (cleaned.find("{") if "{" in cleaned else len(cleaned)),
        (cleaned.find("[") if "[" in cleaned else len(cleaned))
    )
    cleaned = cleaned[start:]
    return json.loads(cleaned)

def extract_topic(transcript: str) -> dict:
    system = (
        "You are analyzing a video transcript. "
        "Return ONLY a valid JSON object with no other text or markdown."
    )
    user = f"""Extract the main topic from this transcript:

{transcript[:3000]}

Return exactly this JSON:
{{
  "topic": "main topic in 5 words or less",
  "niche": "content niche (fitness/finance/tech/cooking/etc)",
  "keywords": ["kw1","kw2","kw3","kw4","kw5","kw6","kw7","kw8","kw9","kw10"]
}}"""
    raw = _call(system, user, max_tokens=500)
    return _parse_json(raw)

def analyze_patterns(videos_data: list) -> dict:
    system = (
        "You are a content intelligence analyst. "
        "Analyze YouTube videos and find winning patterns. "
        "Return ONLY valid JSON with no other text or markdown."
    )
    videos_summary = json.dumps(videos_data[:15], indent=2)
    user = f"""Analyze these top-performing YouTube videos:

{videos_summary}

Return exactly this JSON:
{{
  "winning_hooks": [{{"pattern": "...", "example": "..."}}],
  "winning_structures": ["..."],
  "common_tags": ["..."],
  "description_patterns": ["..."],
  "content_gaps": ["..."],
  "audience_questions": ["..."],
  "average_duration_seconds": 0,
  "dominant_tone": "educational"
}}"""
    raw = _call(system, user, max_tokens=2000)
    return _parse_json(raw)

def generate_upload_package(transcript: str, segments: list, research: dict) -> dict:
    system = (
        "You are a YouTube growth strategist. "
        "Generate upload-ready content using the creator's transcript and niche research. "
        "Return ONLY valid JSON with no other text or markdown."
    )
    chapters_hint = _build_chapters_hint(segments)
    user = f"""Generate a complete YouTube upload package.

CREATOR TRANSCRIPT:
{transcript[:4000]}

NICHE RESEARCH:
{json.dumps(research, indent=2)}

TIMING HINT:
{chapters_hint}

Return exactly this JSON:
{{
  "titles": [
    {{"title": "...", "reasoning": "...", "rank": 1}},
    {{"title": "...", "reasoning": "...", "rank": 2}},
    {{"title": "...", "reasoning": "...", "rank": 3}},
    {{"title": "...", "reasoning": "...", "rank": 4}},
    {{"title": "...", "reasoning": "...", "rank": 5}}
  ],
  "description": "full YouTube description",
  "tags": ["tag1","tag2"],
  "chapters": "00:00 Intro\\n01:30 Topic\\n03:00 Main Point",
  "shorts_moments": [
    {{
      "start_seconds": 0,
      "end_seconds": 45,
      "why_it_works": "...",
      "standalone": true,
      "suggested_title": "..."
    }}
  ]
}}

Rules:
- Exactly 5 titles using different hook patterns
- 25-30 tags
- 3 shorts moments each 30-60 seconds"""
    raw = _call(system, user, max_tokens=4096)
    return _parse_json(raw)

def _build_chapters_hint(segments: list) -> str:
    if not segments:
        return "No timing data available"
    hints = []
    step = max(1, len(segments) // 8)
    for i in range(0, len(segments), step):
        seg = segments[i]
        minutes = int(seg["start"] // 60)
        seconds = int(seg["start"] % 60)
        preview = seg["text"][:60]
        hints.append(f"{minutes:02d}:{seconds:02d} — {preview}")
    return "\n".join(hints)

def draft_comment_replies(comments: list) -> list:
    if not comments:
        return []
    system = (
        "You are helping a YouTube creator reply to comments. "
        "Replies must sound genuine and human, not robotic. "
        "Under 3 sentences each. "
        "Return ONLY valid JSON with no other text or markdown."
    )
    comments_text = json.dumps(
        [{"id": c["id"], "name": c.get("commenter_name", ""), "comment": c["comment_text"]}
         for c in comments],
        indent=2
    )
    user = f"""Draft genuine replies for these YouTube comments:

{comments_text}

Return a JSON array:
[
  {{"comment_id": "...", "draft_reply": "..."}}
]"""
    raw = _call(system, user, max_tokens=2000)
    return _parse_json(raw)

def detect_clip_opportunities(transcript_segments: list, comments: list) -> list:
    if len(comments) < 5:
        return []
    system = (
        "You are analyzing YouTube comments to find which video moments resonate most. "
        "Only flag moments referenced by 5 or more comments. "
        "Return ONLY valid JSON with no other text or markdown."
    )
    seg_summary = []
    for seg in transcript_segments[::3]:
        minutes = int(seg["start"] // 60)
        seconds = int(seg["start"] % 60)
        seg_summary.append(f"{minutes:02d}:{seconds:02d} — {seg['text'][:100]}")

    comment_texts = [c["comment_text"] for c in comments[:200]]
    user = f"""Find video moments referenced by 5+ comments.

TRANSCRIPT TIMELINE:
{chr(10).join(seg_summary)}

COMMENTS:
{json.dumps(comment_texts, indent=2)}

Return JSON array (empty [] if none meet threshold):
[
  {{
    "moment_description": "...",
    "start_seconds": 0,
    "end_seconds": 60,
    "comment_count": 0,
    "example_comments": ["...", "...", "..."],
    "why_it_resonated": "..."
  }}
]"""
    raw = _call(system, user, max_tokens=2000)
    return _parse_json(raw)

def generate_clip_package(segment_text: str, video_topic: str, why_it_resonated: str, research: dict = None) -> dict:
    system = (
        "You are a short-form content strategist. "
        "Generate a complete posting package for a YouTube Short. "
        "Return ONLY valid JSON with no other text or markdown."
    )
    user = f"""Generate a clip posting package.

CLIP CONTENT: {segment_text}
TOPIC: {video_topic}
WHY AUDIENCE LOVED THIS: {why_it_resonated}

Return exactly this JSON:
{{
  "title": "YouTube Shorts title under 60 chars",
  "description": "2-3 sentence description",
  "hashtags": ["tag1","tag2","tag3","tag4","tag5"],
  "hook_line": "first caption line for the clip",
  "suggested_post_time": "e.g. Tomorrow at 6pm",
  "suggested_post_reason": "brief reason",
  "why_it_works": "one sentence for the creator"
}}"""
    raw = _call(system, user, max_tokens=800)
    return _parse_json(raw)
