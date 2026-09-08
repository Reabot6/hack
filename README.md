# CreatorOS

> While you sleep, we watched your comments, found what resonated,
> built the clips, and drafted your replies. Come back when ready.

---

## What This Is

CreatorOS automates everything a YouTube creator does after filming.

Upload your video. Close your laptop. The tool works in the background —
reading comments, finding what your audience loved most, generating clip
packages, drafting replies. You come back and approve. Nothing posts
without you.

**The problem it solves:**
Every creator knows the drill. Filming is the creative part.
Everything after — title, description, tags, timestamps, captions,
finding which moment to clip, replying to 80 comments — that's
hours of mechanical work that has nothing to do with making great content.

**This tool kills that busywork.**

---

## How It Works

```
UPLOAD
Creator uploads MP4 or audio file
         ↓
TRANSCRIBE
Extract audio → Whisper → full transcript with timestamps
         ↓
RESEARCH
YouTube API pulls top 30 videos in your niche
Analyzes transcripts, titles, tags, comments
Finds what's winning and why
         ↓
GENERATE UPLOAD PACKAGE
Data-backed title options (not AI guesses)
SEO description using your actual talking points
Tags from what top performers actually use
Chapters auto-generated from transcript
Clean .srt captions file ready to upload
         ↓
POST YOUR VIDEO (you do this on YouTube)
         ↓
BACKGROUND WORKER (runs every 2 hours, you don't have to be there)
Reads new comments
Finds which moments are being quoted and referenced
Flags clip opportunities when 5+ comments reference same moment
Drafts replies for every comment
Checks your alert conditions
         ↓
YOU COME BACK
Clip packages are waiting → approve or dismiss
Comment replies are drafted → approve all or review one by one
Alerts fired if anything significant happened
         ↓
CLIPS
Download clip package (timestamp + title + caption + hashtags)
Cut in CapCut using exact timestamp
Post anywhere
```

---

## V1 Scope (Hackathon Build)

Platform: **YouTube only**

| Feature | Status |
|---------|--------|
| MP4 / audio upload | ✅ V1 |
| Whisper transcription | ✅ V1 |
| YouTube competitor research | ✅ V1 |
| Upload package generation | ✅ V1 |
| Captions .srt file | ✅ V1 |
| Per-video dashboard | ✅ V1 |
| YouTube analytics display | ✅ V1 |
| Comment inbox + AI replies | ✅ V1 |
| Batch approve comments | ✅ V1 |
| Alert system | ✅ V1 |
| Comment-driven clip detection | ✅ V1 |
| Clip package generation | ✅ V1 |
| Scheduling suggestion | ✅ V1 |
| TikTok integration | 🔜 V2 |
| Instagram integration | 🔜 V2 |
| Auto video crop + caption burn | 🔜 V2 |
| Script studio (pre-production) | 🔜 V2 |
| Cross-platform unified inbox | 🔜 V2 |

---

## Tech Stack

```
Backend:    Python 3.11 + FastAPI
Frontend:   React 18 + TailwindCSS
Database:   Supabase (PostgreSQL)
AI:         Anthropic Claude API
Transcribe: OpenAI Whisper API
Research:   YouTube Data API v3 + youtube-transcript-api
Audio:      FFmpeg
Scheduler:  APScheduler
```

---

## Build Phases

### Phase 1 — Core Pipeline *(build first, verify before moving on)*
```
[ ] File upload endpoint (MP4 + audio)
[ ] FFmpeg audio extraction
[ ] Whisper API transcription
[ ] Timestamped transcript storage in Supabase
[ ] Upload progress UI (never blank screen)
[ ] Transcript display on frontend
```

### Phase 2 — Research + Generation *(depends on Phase 1)*
```
[ ] Topic extraction from transcript (Claude)
[ ] Supabase cache check before YouTube API calls
[ ] YouTube search (top 30 videos by topic)
[ ] Batch metadata fetch (videos.list)
[ ] Competitor transcript pull (youtube-transcript-api)
[ ] Performance score normalization
    (views/subscribers + engagement + recency)
[ ] Pattern analysis (Claude)
[ ] Upload package generation (Claude):
    - 5 title options with reasoning
    - Full SEO description
    - 30 tags
    - Auto-chapters from transcript
    - .srt captions file
    - 3 clip moment recommendations
[ ] Research cache write (24hr expiry)
[ ] All outputs copy-pasteable + downloadable
```

### Phase 3 — Video Dashboard *(depends on Phase 2)*
```
[ ] Per-video page route /dashboard/{video_id}
[ ] YouTube analytics pull + display
    (views, likes, comments, like ratio)
[ ] Auto-refresh every 30 minutes
[ ] Comment inbox:
    - Pull all comments from YouTube API
    - Claude drafts reply for each
    - Approve / Edit+Approve / Skip buttons
    - Batch approve all
    - Filter: All | Pending | Approved | Skipped
[ ] Post approved replies via YouTube API (OAuth)
[ ] Alert system:
    - Creator sets conditions
    - Background check every 30 min
    - In-app notification on trigger
```

### Phase 4 — Background Worker + Clip Intelligence *(depends on Phase 3)*
```
[ ] APScheduler setup (runs every 2 hours)
[ ] For each active video:
    [ ] Pull new comments since last check
    [ ] Send comments + transcript to Claude
    [ ] Detect moments referenced by 5+ comments
    [ ] Generate clip package for each opportunity:
        - Short title
        - Description
        - Hashtags
        - Hook line
        - Suggested post time
    [ ] Store as pending_approval in Supabase
    [ ] In-app notification to creator
[ ] Clip opportunity cards on dashboard
[ ] Approve → download package
[ ] Schedule → set post time reminder
[ ] Dismiss → remove card
[ ] Clip performance tracking (separate from original video)
```

### Phase 5 — Polish + Demo Prep
```
[ ] seed_demo.py script (pre-load all demo data)
[ ] IP limiting (1 research/day per IP)
[ ] All API calls wrapped in try/catch
[ ] Human-readable error messages
[ ] Error logging to Supabase
[ ] Demo checklist verified (see below)
```

---

## Pseudocode: Comment-Driven Clip Detection

This is the core differentiator. Read carefully.

```
EVERY 2 HOURS, for each active video:

1. Pull all comments from YouTube API
   Store new ones in Supabase

2. Send to Claude:
   - Full transcript with timestamps
   - All comments for this video
   
   Ask Claude:
   "Find comments that reference a specific moment,
    quote something said, or ask about a specific part.
    Group by which part of video they reference.
    For any moment with 5+ comments: return timestamp range."

3. If Claude finds moments with 5+ references:
   - Create clip_opportunity record
   - Send to Claude again with just that transcript segment:
     "Generate: short title, description, hashtags,
      hook line, why it works, suggested post time"
   - Store clip_package
   - Send creator notification

4. Creator opens dashboard:
   - Sees "🔥 CLIP OPPORTUNITY DETECTED"
   - 47 comments referencing 4:23-5:01
   - Full package ready
   - [Schedule] [Download] [Dismiss]
```

---

## Demo Flow (8 Minutes)

```
1. Upload audio file (1 min)
   "Here's a video I just finished editing"
   Show transcription happening in real time

2. Research layer (1 min)
   "Analyzing 30 videos in your niche..."
   Show patterns found

3. Upload package (1 min)
   Title options with reasoning
   Description, tags, chapters
   Download .srt captions

4. Video dashboard (2 min)
   Analytics panel
   Comment inbox + batch approve
   Alert configuration

5. Clip intelligence (2 min)
   "47 comments referencing this moment"
   Clip opportunity card
   Full package ready + schedule

6. Close (1 min)
   "You never had to be there"
   V2 roadmap
```

---

## Demo Checklist (Run Before Presenting)

```
[ ] seed_demo.py executed successfully
[ ] All demo data confirmed in Supabase
[ ] API keys in .env verified
[ ] IP limit reset for demo location
[ ] Upload flow tested end to end
[ ] All download buttons work
[ ] All copy buttons work
[ ] Comment approve flow tested
[ ] Clip package display working
[ ] Notifications showing
[ ] Zero console errors in browser
[ ] Backup: all demo data pre-cached
     (demo must work if YouTube API is down)
```

---

## Environment Setup

```bash
# Clone
git clone {repo}
cd creatorOS

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Environment variables
cp .env.example .env
# Fill in: ANTHROPIC_API_KEY, OPENAI_API_KEY,
#           YOUTUBE_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY

# Run DB schema
# Copy contents of db/schema.sql into Supabase SQL editor and run

# Start backend
uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd ../frontend
npm install
npm run dev
```

---

## API Quota Notes

```
YouTube Data API v3: 10,000 units/day free
  search.list:        100 units (most expensive)
  videos.list:        1 unit (batch up to 50)
  commentThreads:     1 unit per call
  comments.insert:    50 units per reply

Strategy:
  Always cache. Never call same thing twice.
  IP limit research requests.
  Batch all video metadata calls.
```

---

## Skill Reference

The `skill/` folder contains the development skill for this project.
Every file change and architectural decision should be checked against
`skill/SKILL.md` and its reference files:

- `skill/references/phases.md` — Full pseudocode for all 5 phases
- `skill/references/architecture.md` — Stack, folder structure, DB schema
- `skill/references/apis.md` — API docs, quotas, gotchas, workarounds
