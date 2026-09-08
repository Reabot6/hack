# CreatorOS — Phase Pseudocode

## PHASE 1: Core Pipeline

### Goal
Creator uploads file → we have a clean transcript stored in DB.
Everything else in the product depends on this being rock solid.

```
ENDPOINT: POST /api/upload

INPUT:
  file: MP4 or audio file (MP3, WAV, M4A)
  user_id: string

STEP 1 — RECEIVE FILE
  validate file type (MP4, MP3, WAV, M4A only)
  validate file size (max 500MB)
  generate unique video_id
  save file temporarily to /tmp/{video_id}

STEP 2 — EXTRACT AUDIO (if MP4)
  run FFmpeg:
    ffmpeg -i input.mp4 -vn -acodec mp3 output.mp3
    (extract audio only, discard video)
    (audio file is much smaller, faster to process)
  if already audio file: skip this step

STEP 3 — TRANSCRIBE
  send audio file to Whisper API
  model: whisper-1
  response_format: verbose_json (includes timestamps per word)
  store:
    full transcript text
    timestamped segments (each sentence with start/end time)
    detected language

STEP 4 — STORE
  save to Supabase videos table:
    video_id
    user_id
    original_filename
    transcript_text
    transcript_segments (JSON array with timestamps)
    status: "transcribed"
    created_at

STEP 5 — CLEANUP
  delete temp file from /tmp
  return video_id to frontend

OUTPUT:
  video_id
  transcript preview (first 500 chars)
  status: success

FRONTEND BEHAVIOUR:
  show upload progress bar
  show "Extracting audio..." 
  show "Transcribing..." with animated indicator
  show transcript appearing when done
  never show blank screen at any point
```

---

## PHASE 2: Research + Generation

### Goal
Use transcript topic to research what works in the niche.
Mix competitor intelligence with the creator's actual content.
Output a complete upload-ready package.

```
ENDPOINT: POST /api/generate/{video_id}

INPUT:
  video_id: string
  (transcript already stored from Phase 1)

STEP 1 — EXTRACT TOPIC
  send transcript to Claude:
    "What is the main topic of this video?
     Return: topic (5 words max), niche, keywords (10)"
  store topic + keywords

STEP 2 — CHECK CACHE
  look up Supabase research_cache table
  cache key: topic + today's date
  if cache hit: skip Steps 3-5, use cached data

STEP 3 — YOUTUBE RESEARCH (if no cache)
  call YouTube Data API v3 search endpoint:
    query: topic + keywords
    order: viewCount
    maxResults: 30
    type: video
    publishedAfter: 90 days ago (keep it recent)
  
  for each video returned:
    call videos.list endpoint (batch, max 50 per call):
      parts: snippet, statistics, contentDetails
      get: title, description, tags, duration,
           viewCount, likeCount, commentCount,
           publishedAt, channelId
    
    call youtube-transcript-api:
      get transcript for each video_id
      if unavailable: skip that video
    
    call commentThreads.list:
      maxResults: 50 per video
      order: relevance
      get top comments

STEP 4 — NORMALIZE PERFORMANCE
  for each video calculate performance score:
    
    fetch channel subscriber count (channels.list)
    
    view_ratio = views / subscribers
    engagement_rate = (likes + comments) / views
    recency_boost = 1 + (1 / days_since_published)
    
    performance_score = (
      view_ratio * 0.4 +
      engagement_rate * 0.4 +
      recency_boost * 0.2
    )
  
  sort videos by performance_score descending
  take top 20 for analysis

STEP 5 — ANALYZE PATTERNS
  send to Claude (top 20 videos data):
    transcripts, titles, descriptions, tags,
    top comments, performance scores
  
  Claude returns:
    winning_hooks: [list of actual hook patterns with examples]
    winning_structures: [how videos are organized]
    common_tags: [tags appearing in top performers]
    description_patterns: [what SEO descriptions look like]
    content_gaps: [what nobody is covering well]
    audience_questions: [what comments keep asking]
    average_duration: seconds
    tone: educational/entertainment/personal/etc

STEP 6 — CACHE RESEARCH
  save to research_cache:
    cache_key: topic + date
    data: all patterns found
    expires_at: tomorrow midnight

STEP 7 — GENERATE UPLOAD PACKAGE
  send to Claude:
    creator_transcript: full transcript
    research_data: patterns from Step 5
  
  Claude generates:
    
    TITLES (5 options):
      each title informed by winning patterns
      each title uses creator's actual content
      each title has a one-line reasoning
      ranked by predicted CTR
    
    DESCRIPTION:
      opening hook (2 sentences)
      what the video covers
      timestamps placeholder (filled in Step 8)
      keywords woven in naturally
      links section placeholder
      call to action
    
    TAGS (30):
      pulled from top performer tags
      mixed with creator's specific keywords
      formatted as comma-separated list
    
    CHAPTERS:
      read transcript segments
      identify natural topic breaks
      format as YouTube chapter timestamps:
        00:00 Introduction
        01:23 [topic]
        etc.
    
    CAPTIONS (.srt):
      use timestamped transcript segments
      format as proper .srt file:
        1
        00:00:01,000 --> 00:00:04,500
        [transcript text]
    
    SHORTS_MOMENTS (3):
      identify 3 best clip moments
      each with:
        start_timestamp
        end_timestamp
        why_it_works (reasoning)
        standalone_hook (does it make sense without context?)

STEP 8 — STORE AND RETURN
  save upload_package to Supabase
  return to frontend:
    all 5 titles
    full description
    tags array
    chapters formatted
    srt file content (downloadable)
    3 clip moments with reasoning

FRONTEND BEHAVIOUR:
  show research happening with live status:
    "Analyzing 30 videos in your niche..."
    "Finding winning patterns..."
    "Generating your upload package..."
  show each section appearing as generated
  every section has a copy button
  srt file has download button
  titles show reasoning on hover/expand
```

---

## PHASE 3: Video Dashboard

### Goal
One page per video. Everything about that video in one place.
Creator should be able to manage the entire life of a video from here.
Works whether they're there live or coming back hours later.

```
PAGE: /dashboard/{video_id}

LAYOUT:
  top: video title + platform status badges
  left column: analytics panel
  right column: comment inbox
  bottom: clips section + alerts

SECTION 1 — ANALYTICS PANEL
  
  ENDPOINT: GET /api/analytics/{video_id}
  
  call YouTube videos.list:
    parts: statistics
    fields: viewCount, likeCount, commentCount
  
  display:
    views (with change since last check)
    likes
    comments
    like ratio (likes/views as %)
    
  refresh: every 30 minutes automatically
  show last updated timestamp

SECTION 2 — COMMENT INBOX
  
  ENDPOINT: GET /api/comments/{video_id}
  
  call YouTube commentThreads.list:
    videoId: video_id
    maxResults: 100
    order: time (newest first)
    
  for new comments (not yet seen):
    send batch to Claude:
      "Draft a reply for each comment.
       Match the creator's tone.
       Keep replies under 3 sentences.
       Be genuine not robotic."
    store drafts in Supabase
  
  display each comment with:
    commenter name
    comment text
    time posted
    AI drafted reply (editable text field)
    [Approve] button → posts reply via YouTube API
    [Edit + Approve] button → opens edit then posts
    [Skip] button → marks as skipped
  
  top of inbox:
    [Approve All] button → posts all drafts at once
    filter: All | Pending | Approved | Skipped
  
  POSTING REPLY:
    ENDPOINT: POST /api/comments/{comment_id}/reply
    call YouTube comments.insert
    mark comment as replied in Supabase

SECTION 3 — ALERTS
  
  creator configures:
    "Notify me when views pass [X]"
    "Notify me if engagement drops below [X%]"
    "Notify me when comment count passes [X]"
    "Notify me if comment spike (more than [X] in an hour)"
  
  store alert conditions in Supabase alerts table
  
  background worker checks every 30 minutes:
    pull current stats
    compare against alert conditions
    if triggered: send notification
      (in-app notification badge + optional email)
  
  ENDPOINT: POST /api/alerts/{video_id}
  ENDPOINT: DELETE /api/alerts/{alert_id}
```

---

## PHASE 4: Background Worker + Clip Intelligence

### Goal
The tool works while the creator is away.
Comments come in → worker reads them → finds what's resonating →
generates clip packages → waits for creator approval.
Creator comes back to find work done.

```
BACKGROUND WORKER: runs every 2 hours via APScheduler

FOR EACH active video:

  STEP 1 — PULL FRESH COMMENTS
    call YouTube commentThreads.list
    get all comments since last check
    store new comments in Supabase
    update last_checked timestamp

  STEP 2 — CLIP OPPORTUNITY DETECTION
    
    collect all comments for this video
    send to Claude with transcript:
    
      PROMPT:
      "Here are YouTube comments for a video.
       Here is the full transcript with timestamps.
       
       Find comments that reference a specific moment,
       quote something said in the video, or ask about
       a specific part. Group them by which part of the
       video they reference.
       
       For any moment referenced by 5 or more comments:
       return:
         moment_description: what they're referencing
         start_timestamp: estimated from transcript
         end_timestamp: estimated from transcript
         comment_count: how many reference this
         example_comments: 3 examples
         why_this_resonated: one sentence reasoning"
    
    if Claude finds moments with 5+ comment references:
      create clip_opportunity in Supabase:
        video_id
        start_timestamp
        end_timestamp  
        comment_count
        why_it_resonated
        status: "pending_approval"
        generated_at: now

  STEP 3 — GENERATE CLIP PACKAGE (for each new opportunity)
    
    extract transcript segment for that timestamp range
    
    send to Claude:
      segment_transcript
      video_topic
      niche_research (from cache)
    
    Claude generates:
      short_title: (YouTube Shorts optimized, <60 chars)
      short_description: (2-3 sentences)
      hashtags: 5-8 relevant hashtags
      hook_line: first line to display as caption overlay
      why_it_works: reasoning for creator
      suggested_post_time: based on channel patterns
    
    store clip_package in Supabase
    
    send in-app notification:
      "🔥 Clip opportunity detected
       47 comments referencing 4:23-5:01
       Package ready for your approval"

  STEP 4 — DRAFT COMMENT REPLIES
    (same as Phase 3 Section 2 but runs in background)
    any new comments without drafts → generate drafts
    creator sees them waiting on next visit

  STEP 5 — CHECK ALERTS
    pull current video stats
    compare against creator's alert conditions
    trigger notifications if conditions met
```

### Clip Package — What Creator Sees

```
CLIP OPPORTUNITY CARD on dashboard:

🔥 CLIP OPPORTUNITY DETECTED
──────────────────────────────
47 comments referencing this moment
"Your bloating explanation is being 
quoted repeatedly in comments"

Timestamp: 4:23 - 5:01 (38 seconds)

Why it works:
Complete hook-payoff. No context needed.
Strong emotional response in comments.

Generated package:
  Title:       "Why your stomach looks bigger at night"
  Description: [2-3 sentences]
  Hashtags:    #stomachbloating #healthtips #flattummy
  
Suggested post time: Tomorrow, Wednesday 6pm
Reason: Your last 3 posts performed best 5-7pm weekdays

[Preview Package]  [Schedule]  [Download]  [Dismiss]
```

---

## PHASE 5: Polish + Demo Prep

```
CACHING:
  all YouTube API responses cached in Supabase
  research results cached by topic + date
  never hit YouTube API twice for same data
  
IP LIMITING:
  store request_log: ip_address + endpoint + timestamp
  max 1 research request per IP per day
  max 3 upload requests per IP per day
  return clear error: "Demo limit reached. Contact us for full access."

PRE-LOADED DEMO DATA:
  create seed script: scripts/seed_demo.py
  pre-transcribe demo video
  pre-run competitor research  
  pre-generate upload package
  pre-load comment inbox with drafts
  pre-create 2 clip opportunities
  
  demo runs against this cached data instantly
  no waiting for APIs during presentation

ERROR STATES:
  every API call has try/catch
  every error shows human-readable message
  never show stack traces to user
  log errors to Supabase error_log table

DEMO CHECKLIST (run before presenting):
  [ ] seed_demo.py executed successfully
  [ ] all demo data in Supabase
  [ ] API keys in .env verified
  [ ] IP limit reset for demo IPs
  [ ] all download buttons tested
  [ ] copy buttons tested
  [ ] comment approve flow tested end to end
  [ ] clip package display tested
  [ ] no console errors in browser
```
