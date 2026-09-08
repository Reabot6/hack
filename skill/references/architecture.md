# CreatorOS — Architecture

## Stack

```
BACKEND:    Python 3.11 + FastAPI
FRONTEND:   React 18 + TailwindCSS
DATABASE:   Supabase (PostgreSQL + Storage)
AI:         Anthropic Claude API (claude-sonnet-4-6)
TRANSCRIBE: OpenAI Whisper API
AUDIO:      FFmpeg (server-side)
SCHEDULER:  APScheduler (background cron jobs)
```

## Folder Structure

```
creatorOS/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── routers/
│   │   ├── upload.py            # Phase 1: file upload + transcription
│   │   ├── generate.py          # Phase 2: research + package generation
│   │   ├── dashboard.py         # Phase 3: analytics + comments + alerts
│   │   └── clips.py             # Phase 4: clip opportunities
│   ├── services/
│   │   ├── whisper.py           # Whisper API wrapper
│   │   ├── ffmpeg.py            # audio extraction
│   │   ├── youtube.py           # YouTube Data API v3 wrapper
│   │   ├── transcripts.py       # youtube-transcript-api wrapper
│   │   ├── claude.py            # Claude API wrapper + all prompts
│   │   └── cache.py             # Supabase cache read/write
│   ├── workers/
│   │   └── background.py        # APScheduler cron jobs
│   ├── db/
│   │   └── schema.sql           # Supabase table definitions
│   └── scripts/
│       └── seed_demo.py         # Pre-load demo data
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Upload.jsx       # Phase 1+2: upload + generation
│   │   │   └── Dashboard.jsx    # Phase 3+4: per-video dashboard
│   │   ├── components/
│   │   │   ├── UploadZone.jsx
│   │   │   ├── TranscriptView.jsx
│   │   │   ├── UploadPackage.jsx
│   │   │   ├── AnalyticsPanel.jsx
│   │   │   ├── CommentInbox.jsx
│   │   │   ├── ClipOpportunityCard.jsx
│   │   │   └── AlertsPanel.jsx
│   │   └── lib/
│   │       └── api.js           # all fetch calls to backend
│   └── public/
│
├── skill/                       # this skill
└── README.md
```

## Database Schema

```sql
-- videos: core record for each uploaded video
CREATE TABLE videos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT,
  original_filename TEXT,
  transcript_text TEXT,
  transcript_segments JSONB,  -- [{start, end, text}]
  topic TEXT,
  niche TEXT,
  keywords JSONB,             -- string array
  status TEXT,                -- transcribed | researched | packaged
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- upload_packages: generated metadata for YouTube upload
CREATE TABLE upload_packages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  video_id UUID REFERENCES videos(id),
  titles JSONB,               -- [{title, reasoning, rank}]
  description TEXT,
  tags JSONB,                 -- string array
  chapters TEXT,              -- formatted timestamp string
  srt_content TEXT,           -- full .srt file content
  shorts_moments JSONB,       -- [{start, end, why, standalone}]
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- research_cache: competitor research by topic
CREATE TABLE research_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cache_key TEXT UNIQUE,      -- topic + date
  data JSONB,                 -- full patterns object
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- comments: all YouTube comments per video
CREATE TABLE comments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  video_id UUID REFERENCES videos(id),
  youtube_comment_id TEXT UNIQUE,
  commenter_name TEXT,
  comment_text TEXT,
  posted_at TIMESTAMPTZ,
  ai_draft_reply TEXT,
  status TEXT DEFAULT 'pending', -- pending | approved | skipped
  replied_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- clip_opportunities: detected from comment analysis
CREATE TABLE clip_opportunities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  video_id UUID REFERENCES videos(id),
  start_timestamp NUMERIC,    -- seconds
  end_timestamp NUMERIC,      -- seconds
  comment_count INTEGER,
  why_it_resonated TEXT,
  example_comments JSONB,     -- string array
  clip_package JSONB,         -- {title, description, hashtags, hook_line, suggested_post_time}
  status TEXT DEFAULT 'pending_approval', -- pending_approval | scheduled | dismissed
  scheduled_for TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- alerts: creator-configured notification conditions
CREATE TABLE alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  video_id UUID REFERENCES videos(id),
  condition_type TEXT,        -- views_threshold | engagement_drop | comment_spike
  threshold_value NUMERIC,
  triggered BOOLEAN DEFAULT FALSE,
  triggered_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- request_log: IP limiting
CREATE TABLE request_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ip_address TEXT,
  endpoint TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- error_log: track failures silently
CREATE TABLE error_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  context TEXT,
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Environment Variables

```
# backend/.env

ANTHROPIC_API_KEY=
OPENAI_API_KEY=          # for Whisper
YOUTUBE_API_KEY=         # YouTube Data API v3
SUPABASE_URL=
SUPABASE_SERVICE_KEY=    # server-side, not anon key
```

## API Quota Management

```
YouTube Data API v3:
  daily limit: 10,000 units free
  
  costs:
    search.list:           100 units per call
    videos.list:           1 unit per video
    commentThreads.list:   1 unit per call
    comments.insert:       50 units per comment
  
  strategy:
    1. Always check cache before any API call
    2. Batch videos.list calls (max 50 IDs per call)
    3. IP limit research requests (most expensive)
    4. Cache research results for 24 hours
    5. Cache video metadata permanently
    6. Cache comments for 6 hours

Whisper API:
  cost: $0.006 per minute of audio
  strategy: 
    1. Extract audio first (smaller file)
    2. Cache transcripts permanently (never re-transcribe)

Claude API:
  strategy:
    1. Batch multiple tasks in single prompts where possible
    2. Cache generated packages (never re-generate same video)
```
