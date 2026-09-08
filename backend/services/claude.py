import os
import json
import re
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"


def _call(system: str, user: str, max_tokens: int = 4096) -> str:
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text.strip()


def _parse_json(raw: str) -> dict | list:
    """Strip markdown fences and parse JSON safely."""
    cleaned = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
    return json.loads(cleaned)


# ── Topic Extraction ──────────────────────────────────────────────────────────

def extract_topic(transcript: str) -> dict:
    """
    Extract topic, niche, and keywords from transcript.
    Returns: {topic, niche, keywords}
    """
    system = (
        "You are analyzing a video transcript. "
        "Return ONLY a valid JSON object with no other text, preamble, or markdown."
    )
    user = f"""Extract the main topic from this transcript:

{transcript[:3000]}

Return this exact JSON structure:
{{
  "topic": "main topic in 5 words or less",
  "niche": "content niche (fitness/finance/tech/cooking/etc)",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "keyword8", "keyword9", "keyword10"]
}}"""
    raw = _call(system, user, max_tokens=500)
    return _parse_json(raw)


# ── Pattern Analysis ──────────────────────────────────────────────────────────

def analyze_patterns(videos_data: list) -> dict:
    """
    Analyze top performing videos to find winning patterns.
    videos_data: list of {title, description, tags, transcript_summary, view_score, top_comments}
    Returns pattern dict.
    """
    system = (
        "You are a content intelligence analyst. "
        "Analyze YouTube videos and find what makes them perform well. "
        "Return ONLY valid JSON with no other text or markdown."
    )

    videos_summary = json.dumps(videos_data[:15], indent=2)  # top 15

    user = f"""Analyze these top-performing YouTube videos and find winning patterns:

{videos_summary}

Return this exact JSON structure:
{{
  "winning_hooks": [
    {{"pattern": "pattern description", "example": "actual example from data"}}
  ],
  "winning_structures": ["structure description"],
  "common_tags": ["tag1", "tag2", "tag3"],
  "description_patterns": ["pattern description"],
  "content_gaps": ["gap: what nobody is covering well"],
  "audience_questions": ["question that appears in comments"],
  "average_duration_seconds": 0,
  "dominant_tone": "educational"
}}"""
    raw = _call(system, user, max_tokens=2000)
    return _parse_json(raw)


# ── Upload Package Generation ──────────────────────────────────────────────────

def generate_upload_package(transcript: str, segments: list, research: dict) -> dict:
    """
    Generate complete upload-ready package for YouTube.
    Returns {titles, description, tags, chapters, shorts_moments}
    """
    system = (
        "You are a YouTube growth strategist. "
        "Generate upload-ready content using the creator's actual transcript and niche research. "
        "Everything must be data-backed, not generic. "
        "Return ONLY valid JSON with no other text or markdown."
    )

    # Build chapters from segments
    chapters_hint = _build_chapters_hint(segments)

    user = f"""Generate a complete YouTube upload package.

CREATOR'S TRANSCRIPT:
{transcript[:4000]}

WHAT WORKS IN THIS NICHE:
{json.dumps(research, indent=2)}

TRANSCRIPT TIMING HINT (for chapters):
{chapters_hint}

Return this exact JSON structure:
{{
  "titles": [
    {{"title": "title text", "reasoning": "why this will get clicks", "rank": 1}},
    {{"title": "title text", "reasoning": "why this will get clicks", "rank": 2}},
    {{"title": "title text", "reasoning": "why this will get clicks", "rank": 3}},
    {{"title": "title text", "reasoning": "why this will get clicks", "rank": 4}},
    {{"title": "title text", "reasoning": "why this will get clicks", "rank": 5}}
  ],
  "description": "full YouTube description with hook, what video covers, and call to action",
  "tags": ["tag1", "tag2"],
  "chapters": "00:00 Introduction\\n01:30 Topic\\n03:00 Main Point\\n05:00 Conclusion",
  "shorts_moments": [
    {{
      "start_seconds": 0,
      "end_seconds": 45,
      "why_it_works": "complete hook-payoff, no context needed",
      "standalone": true,
      "suggested_title": "short title for this clip"
    }}
  ]
}}

Rules:
- 5 titles, each using a different proven hook pattern from the research
- Description must include the creator's actual talking points, not generic text
- 25-30 tags mixing niche tags + specific topic tags
- Chapters auto-detected from transcript structure
- 3 shorts_moments, each 30-60 seconds, truly standalone"""

    raw = _call(system, user, max_tokens=4096)
    return _parse_json(raw)


def _build_chapters_hint(segments: list) -> str:
    """Build a rough timing hint from transcript segments."""
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


# ── Comment Reply Drafts ──────────────────────────────────────────────────────

def draft_comment_replies(comments: list) -> list:
    """
    Draft replies for a batch of comments.
    comments: list of {id, commenter_name, comment_text}
    Returns list of {comment_id, draft_reply}
    """
    if not comments:
        return []

    system = (
        "You are helping a YouTube creator reply to comments. "
        "Replies must sound genuine and human, not robotic or overly positive. "
        "Keep each reply under 3 sentences. Match a conversational tone. "
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


# ── Clip Opportunity Detection ─────────────────────────────────────────────────

def detect_clip_opportunities(transcript_segments: list, comments: list) -> list:
    """
    Find moments in the video that are being referenced by many comments.
    Returns list of clip opportunities.
    """
    if len(comments) < 5:
        return []

    system = (
        "You are analyzing YouTube comments to find which video moments resonate most. "
        "Only flag moments referenced by 5 or more comments. "
        "Return ONLY valid JSON with no other text or markdown."
    )

    # Summarize segments for context
    seg_summary = []
    for seg in transcript_segments[::3]:  # every 3rd segment for brevity
        minutes = int(seg["start"] // 60)
        seconds = int(seg["start"] % 60)
        seg_summary.append(f"{minutes:02d}:{seconds:02d} — {seg['text'][:100]}")

    comment_texts = [c["comment_text"] for c in comments[:200]]  # max 200 comments

    user = f"""Find video moments referenced by 5+ comments.

TRANSCRIPT TIMELINE:
{chr(10).join(seg_summary)}

COMMENTS ({len(comment_texts)} total):
{json.dumps(comment_texts, indent=2)}

Return JSON array (empty array [] if no moments meet threshold):
[
  {{
    "moment_description": "what they are referencing",
    "start_seconds": 0,
    "end_seconds": 60,
    "comment_count": 0,
    "example_comments": ["comment1", "comment2", "comment3"],
    "why_it_resonated": "one sentence explanation"
  }}
]"""

    raw = _call(system, user, max_tokens=2000)
    return _parse_json(raw)


# ── Clip Package Generation ────────────────────────────────────────────────────

def generate_clip_package(
    segment_text: str,
    video_topic: str,
    why_it_resonated: str,
    research: dict = None,
) -> dict:
    """
    Generate ready-to-post clip package for a detected opportunity.
    Returns {title, description, hashtags, hook_line, suggested_post_time, why_it_works}
    """
    system = (
        "You are a short-form content strategist. "
        "Generate a complete posting package for a YouTube Short or social clip. "
        "Return ONLY valid JSON with no other text or markdown."
    )

    user = f"""Generate a complete clip posting package.

CLIP CONTENT:
{segment_text}

TOPIC: {video_topic}
WHY AUDIENCE LOVED THIS: {why_it_resonated}

Return this exact JSON:
{{
  "title": "YouTube Shorts title under 60 chars",
  "description": "2-3 sentence description",
  "hashtags": ["hashtag1", "hashtag2", "hashtag3", "hashtag4", "hashtag5"],
  "hook_line": "first line to show as caption overlay on the clip",
  "suggested_post_time": "e.g. Tomorrow at 6pm",
  "suggested_post_reason": "brief reason why that time",
  "why_it_works": "one sentence for the creator explaining the clip potential"
}}"""

    raw = _call(system, user, max_tokens=800)
    return _parse_json(raw)
