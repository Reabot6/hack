---
name: creatorOS-dev
description: >
  Engineering standard for building CreatorOS — an AI-powered post-production
  automation tool for YouTube creators. Use this skill on every file change,
  every new feature, every architectural decision in the CreatorOS project.
  Triggers whenever the user mentions CreatorOS, asks to build any phase of
  the pipeline (upload, transcription, research, generation, dashboard,
  background worker, comment inbox, clip intelligence), or asks to review,
  check, or continue building the codebase. This skill is the engineering
  team. Every output must pass it.
---

# CreatorOS — Dev Skill

## What We Are Building

CreatorOS automates everything a YouTube creator does AFTER filming.
The creator uploads their video. The tool handles the rest in the background.
They come back to find clip packages ready, comment replies drafted,
and upload metadata generated — all waiting for approval.

**One sentence:** While you sleep, we watched your comments, found what
resonated, built the clips, and drafted your replies. Come back when ready.

---

## Product Phases

Read `references/phases.md` for the full pseudocode of each phase.
Read `references/architecture.md` for stack decisions and folder structure.
Read `references/apis.md` for every external API, quota limits, and gotchas.

### Phase Overview

```
PHASE 1 — CORE PIPELINE
File upload → audio extraction → Whisper transcription → store

PHASE 2 — RESEARCH + GENERATION  
YouTube competitor research → pattern analysis → generate upload package

PHASE 3 — VIDEO DASHBOARD
Per-video page → analytics → comment inbox → alert system

PHASE 4 — BACKGROUND WORKER + CLIP INTELLIGENCE
Cron job → comment monitoring → clip opportunity detection → packages

PHASE 5 — POLISH + DEMO PREP
Cache aggressively → pre-load demo data → IP limiting → clean UI
```

---

## Non-Negotiable Engineering Rules

### 1. Build Order Is Strict
Never start Phase 2 until Phase 1 works perfectly end to end.
Never start Phase 3 until Phase 2 output is verified.
Each phase must be demoed and confirmed before the next begins.

### 2. Every Feature Needs a Fallback
If YouTube API quota is hit → serve from Supabase cache.
If Whisper API is slow → show progress indicator, never blank screen.
If file upload fails → clear error message with retry button.
Demo must never show a broken state to judges.

### 3. Pre-load Demo Data
Before any demo or presentation:
- Pre-transcribe a real video and cache the result
- Pre-run competitor research and cache it
- Pre-generate a full upload package
- Pre-load comment drafts
Demo should feel instant. Never wait for APIs during a live demo.

### 4. Cache Everything
```python
# Before any YouTube API call, check Supabase cache first
# Cache key: topic + date (daily expiry for research)
# Cache key: video_id (permanent for metadata)
# Cache key: video_id + "comments" (6hr expiry)
```

### 5. IP Limiting on Demo Endpoints
```python
# One research request per IP per day
# Prevents quota exhaustion during hackathon judging
# Store IP + timestamp in Supabase
```

### 6. Claude Does All Intelligence Work
No hardcoded pattern matching. No regex for hook detection.
Claude reads transcripts and reasons about them.
Claude reads comments and finds moment references.
Claude generates all copy: titles, descriptions, captions, replies.

### 7. Creator Is Always In Control
Nothing posts automatically without approval.
Every clip, every reply, every scheduled post needs one click to confirm.
The tool suggests. The creator decides.

---

## V1 Scope (Hackathon — YouTube Only)

```
IN SCOPE:
✅ MP4 or audio file upload
✅ Audio extraction (FFmpeg)
✅ Transcription (Whisper API)
✅ YouTube competitor research
✅ Upload package generation
✅ Per-video dashboard
✅ YouTube analytics display
✅ Comment inbox with AI replies
✅ Batch approve comments
✅ Alert system
✅ Clip opportunity detection from comments
✅ Clip package generation (timestamp + copy)
✅ Scheduling suggestion

OUT OF SCOPE (V2):
❌ TikTok integration
❌ Instagram integration  
❌ Actual video processing (crop, caption burn)
❌ Direct clip auto-posting
❌ Script studio / pre-production research
❌ Performance prediction scores
```

---

## Demo Flow (8 Minutes)

```
1. Upload audio file (1 min)
   → Transcribes in real time
   → Show transcript appearing

2. Research layer (1 min)  
   → "Checking what works in your niche"
   → Show competitor patterns found

3. Upload package generated (1 min)
   → Title options with reasoning
   → Description, tags, chapters
   → .srt captions file download

4. Video dashboard (2 min)
   → Analytics panel
   → Comment inbox + batch approve
   → Alert configuration

5. Clip intelligence (2 min)
   → "47 comments referencing 4:23-5:01"
   → Clip opportunity flagged
   → Full clip package ready
   → Schedule with suggested time

6. Close (1 min)
   → "You never had to be there"
   → V2 roadmap slide
```

---

## What Good Output Looks Like

When generating any feature, ask:
- Does the creator have to do manual work this replaces?
- Is the output copy-pasteable or downloadable immediately?
- Does it work if the creator is not watching?
- Would a real YouTuber actually use this?

If any answer is no, the feature is not done.

---

## Reference Files

- `references/phases.md` — Full pseudocode for all 5 phases
- `references/architecture.md` — Stack, folder structure, DB schema
- `references/apis.md` — API docs, quotas, gotchas, workarounds
