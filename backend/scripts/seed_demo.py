"""
Demo seed script.
Run this before any demo or presentation.
Pre-loads a complete video with all data so nothing waits on APIs.

Usage:
  cd backend
  python scripts/seed_demo.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from services.database import (
    create_video, save_upload_package, upsert_comments,
    save_clip_opportunity, create_alert, create_notification, get_db
)

VIDEO_ID = "demo-video-001"

DEMO_TRANSCRIPT = """
If your stomach looks flat in the morning but bloated by evening, 
I'm going to show you exactly why that happens and what I did to fix it.
For two years I was eating less, working out more, and my stomach still 
looked bigger at night. I thought it was fat. It wasn't.
The real reason is a combination of three things: water retention, 
digestive timing, and one food most people eat every day without realizing it.
Here's what I changed. First, I stopped eating raw vegetables after 2pm.
Second, I moved my main carbs to before noon. Third, I added a ten-minute 
walk after dinner. Within three weeks my evening bloating dropped by 80%.
The fat wasn't the problem. The timing was. Save this so you remember it.
"""

DEMO_SEGMENTS = [
    {"start": 0.0, "end": 4.2, "text": "If your stomach looks flat in the morning but bloated by evening,"},
    {"start": 4.2, "end": 7.8, "text": "I'm going to show you exactly why that happens and what I did to fix it."},
    {"start": 7.8, "end": 14.0, "text": "For two years I was eating less, working out more, and my stomach still looked bigger at night."},
    {"start": 14.0, "end": 17.5, "text": "I thought it was fat. It wasn't."},
    {"start": 17.5, "end": 26.0, "text": "The real reason is a combination of three things: water retention, digestive timing, and one food most people eat every day."},
    {"start": 26.0, "end": 30.5, "text": "Here's what I changed."},
    {"start": 30.5, "end": 36.0, "text": "First, I stopped eating raw vegetables after 2pm."},
    {"start": 36.0, "end": 41.5, "text": "Second, I moved my main carbs to before noon."},
    {"start": 41.5, "end": 47.0, "text": "Third, I added a ten-minute walk after dinner."},
    {"start": 47.0, "end": 54.0, "text": "Within three weeks my evening bloating dropped by 80%."},
    {"start": 54.0, "end": 60.0, "text": "The fat wasn't the problem. The timing was. Save this so you remember it."},
]

DEMO_TITLES = [
    {"title": "Why Your Stomach Is Flat in the Morning But Bloated at Night", "reasoning": "Directly addresses the pain point viewers already experience — high personal relevance", "rank": 1},
    {"title": "I Was Eating Less and Still Looked Bloated — Here's Why", "reasoning": "Contrarian hook, personal story builds credibility immediately", "rank": 2},
    {"title": "The Real Reason Your Stomach Looks Bigger at Night (Not Fat)", "reasoning": "Myth-busting angle — 'Not Fat' creates curiosity gap", "rank": 3},
    {"title": "3 Timing Changes That Fixed My Bloating in 3 Weeks", "reasoning": "Specific numbers (3 changes, 3 weeks) increase click-through", "rank": 4},
    {"title": "Stop Blaming Your Diet — Your Bloating Is a Timing Problem", "reasoning": "Contrarian reframe that challenges common assumption", "rank": 5},
]

DEMO_DESCRIPTION = """If your stomach looks flat in the morning but bloated by night, this isn't about eating more or less — it's about timing.

In this video I break down the 3 reasons your stomach changes throughout the day and the exact adjustments I made to fix it in under a month.

WHAT I COVER:
00:00 Why your stomach changes throughout the day
00:18 The real cause (it's not what you think)
00:27 Change #1 — Raw vegetables and timing
00:37 Change #2 — Carbohydrates and the clock
00:42 Change #3 — The 10 minute habit
00:48 My results after 3 weeks

This worked for me. Everyone is different — consult a professional if you have ongoing digestive issues.

---
Follow for more honest health content."""

DEMO_TAGS = [
    "bloating", "flat stomach", "belly bloat", "stomach bloating causes",
    "how to reduce bloating", "bloating remedies", "gut health", "digestive health",
    "stomach tips", "flat belly", "bloating at night", "morning vs evening stomach",
    "reduce bloating fast", "bloating fix", "stomach health", "nutrition timing",
    "anti bloating foods", "bloating after eating", "stomach flat tips",
    "health tips", "wellness", "fitness tips", "weight loss tips",
    "stomach transformation", "digestive tips", "bloating solution",
    "healthy habits", "gut tips", "food timing", "carb timing"
]

DEMO_CHAPTERS = """00:00 Why your stomach changes
00:17 The real cause (not fat)
00:26 Change 1: Vegetable timing
00:36 Change 2: Carb timing  
00:41 Change 3: Evening walk
00:47 My 3-week results
00:54 What to do next"""

DEMO_SRT = """1
00:00:00,000 --> 00:00:04,200
If your stomach looks flat in the morning but bloated by evening,

2
00:00:04,200 --> 00:00:07,800
I'm going to show you exactly why that happens and what I did to fix it.

3
00:00:07,800 --> 00:00:14,000
For two years I was eating less, working out more, and my stomach still looked bigger at night.

4
00:00:14,000 --> 00:00:17,500
I thought it was fat. It wasn't.

5
00:00:17,500 --> 00:00:26,000
The real reason is a combination of three things: water retention, digestive timing, and one food most people eat every day.

6
00:00:26,000 --> 00:00:30,500
Here's what I changed.

7
00:00:30,500 --> 00:00:36,000
First, I stopped eating raw vegetables after 2pm.

8
00:00:36,000 --> 00:00:41,500
Second, I moved my main carbs to before noon.

9
00:00:41,500 --> 00:00:47,000
Third, I added a ten-minute walk after dinner.

10
00:00:47,000 --> 00:00:54,000
Within three weeks my evening bloating dropped by 80%.

11
00:00:54,000 --> 00:01:00,000
The fat wasn't the problem. The timing was. Save this so you remember it."""

DEMO_SHORTS = [
    {"start_seconds": 0, "end_seconds": 18, "why_it_works": "Complete hook — opens with relatable problem, creates mystery, standalone without context", "standalone": True, "suggested_title": "Why your stomach changes shape throughout the day"},
    {"start_seconds": 47, "end_seconds": 60, "why_it_works": "Strong payoff — result + reframe + CTA. Works as a standalone punchline clip", "standalone": True, "suggested_title": "I fixed 2 years of bloating in 3 weeks"},
    {"start_seconds": 14, "end_seconds": 30, "why_it_works": "Myth-busting moment — 'I thought it was fat. It wasn't.' creates maximum curiosity", "standalone": True, "suggested_title": "Your bloating isn't what you think it is"},
]

DEMO_COMMENTS = [
    {"youtube_comment_id": "demo_c1", "youtube_video_id": "demo_yt", "video_id": VIDEO_ID, "commenter_name": "Sarah K.", "comment_text": "The morning vs evening stomach thing is literally my life. Never thought it wasn't fat", "posted_at": "2026-09-01T10:00:00Z", "ai_draft_reply": "Right?! It took me so long to figure out it was timing not fat. The vegetable timing was the biggest change for me honestly.", "status": "pending"},
    {"youtube_comment_id": "demo_c2", "youtube_video_id": "demo_yt", "video_id": VIDEO_ID, "commenter_name": "Marcus T.", "comment_text": "Does this work for men too or just women", "posted_at": "2026-09-01T11:00:00Z", "ai_draft_reply": "100% works for men — I'm a guy and this is my own experience. The digestive timing stuff is the same regardless.", "status": "pending"},
    {"youtube_comment_id": "demo_c3", "youtube_video_id": "demo_yt", "video_id": VIDEO_ID, "commenter_name": "Priya M.", "comment_text": "That moment at 0:14 when you said 'I thought it was fat, it wasn't' I literally gasped", "posted_at": "2026-09-01T12:00:00Z", "ai_draft_reply": "That was the moment everything clicked for me too! Two years of blaming the wrong thing.", "status": "pending"},
    {"youtube_comment_id": "demo_c4", "youtube_video_id": "demo_yt", "video_id": VIDEO_ID, "commenter_name": "Jake R.", "comment_text": "Tried the evening walk thing last night, woke up and my stomach was actually noticeably flatter", "posted_at": "2026-09-01T13:00:00Z", "ai_draft_reply": "That's the one that surprised me most too — such a small change with a big difference. Keep it going!", "status": "pending"},
    {"youtube_comment_id": "demo_c5", "youtube_video_id": "demo_yt", "video_id": VIDEO_ID, "commenter_name": "Amara O.", "comment_text": "Wait so what was the one food you mentioned in the beginning", "posted_at": "2026-09-01T14:00:00Z", "ai_draft_reply": "Raw vegetables eaten late — the fiber ferments in your gut overnight and causes the bloating. Moving them to lunch made a huge difference.", "status": "pending"},
    {"youtube_comment_id": "demo_c6", "youtube_video_id": "demo_yt", "video_id": VIDEO_ID, "commenter_name": "Tom B.", "comment_text": "The timing thing at 14 seconds blew my mind. Never connected that to bloating", "posted_at": "2026-09-01T15:00:00Z", "ai_draft_reply": "It took me embarrassingly long to make that connection! Once I did everything started making sense.", "status": "pending"},
    {"youtube_comment_id": "demo_c7", "youtube_video_id": "demo_yt", "video_id": VIDEO_ID, "commenter_name": "Lisa C.", "comment_text": "The part where you said it wasn't fat broke my brain a little ngl", "posted_at": "2026-09-01T16:00:00Z", "ai_draft_reply": "Same when I first figured it out! We're so conditioned to blame food quantity when timing is the real issue.", "status": "pending"},
    {"youtube_comment_id": "demo_c8", "youtube_video_id": "demo_yt", "video_id": VIDEO_ID, "commenter_name": "Nguyen P.", "comment_text": "I kept replaying the 14 second mark. That line is so good", "posted_at": "2026-09-01T17:00:00Z", "ai_draft_reply": "Appreciate that! It's the part that's most true to what I actually experienced.", "status": "pending"},
    {"youtube_comment_id": "demo_c9", "youtube_video_id": "demo_yt", "video_id": VIDEO_ID, "commenter_name": "Rachel F.", "comment_text": "Does this work for people over 40? Asking for myself", "posted_at": "2026-09-01T18:00:00Z", "ai_draft_reply": "Definitely should — digestive timing doesn't really change with age. If anything it becomes more important. Give it a try for 2-3 weeks!", "status": "pending"},
    {"youtube_comment_id": "demo_c10", "youtube_video_id": "demo_yt", "video_id": VIDEO_ID, "commenter_name": "David M.", "comment_text": "Saved. The fat vs timing reframe at the end is exactly what I needed to hear", "posted_at": "2026-09-01T19:00:00Z", "ai_draft_reply": "That reframe was everything for me too. Glad it landed.", "status": "pending"},
]

DEMO_CLIP = {
    "video_id": VIDEO_ID,
    "start_seconds": 14.0,
    "end_seconds": 17.5,
    "comment_count": 47,
    "why_it_resonated": "Multiple commenters replaying and quoting this exact line. The 'I thought it was fat. It wasn't.' moment is the emotional core of the video — maximum curiosity gap in 4 seconds.",
    "example_comments": [
        "That moment at 0:14 when you said 'I thought it was fat, it wasn't' I literally gasped",
        "I kept replaying the 14 second mark. That line is so good",
        "The part where you said it wasn't fat broke my brain a little ngl",
    ],
    "clip_package": {
        "title": "I thought it was fat. It wasn't. 👀",
        "description": "Two years of blaming the wrong thing. Turns out stomach bloating and actual fat are completely different problems with completely different solutions.",
        "hashtags": ["bloating", "guthealth", "stomachtips", "flatstomach", "healthtips"],
        "hook_line": "I thought it was fat. It wasn't.",
        "suggested_post_time": "Tomorrow at 6pm",
        "suggested_post_reason": "Weekday evenings 5-7pm consistently outperform other times for health content",
        "why_it_works": "4-second standalone clip with a complete curiosity loop — problem, twist, open question. Drives traffic back to the full video.",
    },
    "status": "pending_approval",
}


def seed():
    db = get_db()

    # Clear existing demo data
    print("Clearing old demo data...")
    for table in ["clip_opportunities", "comments", "alerts", "notifications", "upload_packages"]:
        try:
            db.table(table).delete().eq("video_id", VIDEO_ID).execute()
        except Exception:
            pass
    try:
        db.table("videos").delete().eq("id", VIDEO_ID).execute()
    except Exception:
        pass

    # Create video
    print("Creating demo video...")
    create_video({
        "id": VIDEO_ID,
        "original_filename": "how-i-fixed-my-bloating.mp4",
        "transcript_text": DEMO_TRANSCRIPT,
        "transcript_segments": DEMO_SEGMENTS,
        "topic": "stomach bloating morning vs night",
        "niche": "health",
        "keywords": ["bloating", "flat stomach", "gut health", "digestive health", "timing"],
        "status": "packaged",
    })
    print("  ✅ Video created")

    # Create upload package
    print("Creating upload package...")
    save_upload_package({
        "video_id": VIDEO_ID,
        "titles": DEMO_TITLES,
        "description": DEMO_DESCRIPTION,
        "tags": DEMO_TAGS,
        "chapters": DEMO_CHAPTERS,
        "srt_content": DEMO_SRT,
        "shorts_moments": DEMO_SHORTS,
    })
    print("  ✅ Upload package created")

    # Create comments
    print("Creating demo comments...")
    upsert_comments(DEMO_COMMENTS)
    print(f"  ✅ {len(DEMO_COMMENTS)} comments created")

    # Create clip opportunity
    print("Creating clip opportunity...")
    save_clip_opportunity(DEMO_CLIP)
    print("  ✅ Clip opportunity created")

    # Create alert
    print("Creating demo alert...")
    create_alert({"video_id": VIDEO_ID, "condition_type": "views_threshold", "threshold_value": 5000})
    print("  ✅ Alert created")

    # Create notification
    print("Creating demo notification...")
    create_notification({
        "video_id": VIDEO_ID,
        "type": "clip_opportunity",
        "message": "🔥 47 comments referencing 0:14-0:17 — clip package ready for approval",
    })
    print("  ✅ Notification created")

    print()
    print("=" * 50)
    print("Demo seeded successfully.")
    print(f"Video ID: {VIDEO_ID}")
    print(f"Dashboard: http://localhost:5173/dashboard/{VIDEO_ID}")
    print("=" * 50)


if __name__ == "__main__":
    seed()
