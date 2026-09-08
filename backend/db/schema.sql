-- CreatorOS Database Schema
-- Run this entire file in your Supabase SQL editor

-- videos: core record for each uploaded video
CREATE TABLE IF NOT EXISTS videos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT,
  original_filename TEXT,
  transcript_text TEXT,
  transcript_segments JSONB,
  topic TEXT,
  niche TEXT,
  keywords JSONB,
  status TEXT DEFAULT 'uploading',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- upload_packages: generated metadata for YouTube upload
CREATE TABLE IF NOT EXISTS upload_packages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
  titles JSONB,
  description TEXT,
  tags JSONB,
  chapters TEXT,
  srt_content TEXT,
  shorts_moments JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- research_cache: competitor research by topic+date
CREATE TABLE IF NOT EXISTS research_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cache_key TEXT UNIQUE,
  data JSONB,
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- comments: all YouTube comments per video
CREATE TABLE IF NOT EXISTS comments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
  youtube_comment_id TEXT UNIQUE,
  youtube_video_id TEXT,
  commenter_name TEXT,
  comment_text TEXT,
  posted_at TIMESTAMPTZ,
  ai_draft_reply TEXT,
  status TEXT DEFAULT 'pending',
  replied_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- clip_opportunities: detected from comment analysis
CREATE TABLE IF NOT EXISTS clip_opportunities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
  start_seconds NUMERIC,
  end_seconds NUMERIC,
  comment_count INTEGER,
  why_it_resonated TEXT,
  example_comments JSONB,
  clip_package JSONB,
  status TEXT DEFAULT 'pending_approval',
  scheduled_for TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- alerts: creator-configured notification conditions
CREATE TABLE IF NOT EXISTS alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
  condition_type TEXT,
  threshold_value NUMERIC,
  triggered BOOLEAN DEFAULT FALSE,
  triggered_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- request_log: IP rate limiting
CREATE TABLE IF NOT EXISTS request_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ip_address TEXT,
  endpoint TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- error_log: silent error tracking
CREATE TABLE IF NOT EXISTS error_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  context TEXT,
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- notifications: in-app notifications
CREATE TABLE IF NOT EXISTS notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
  type TEXT,
  message TEXT,
  read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- V1 publishing migration. Safe to run against an existing CreatorOS database.
ALTER TABLE videos ADD COLUMN IF NOT EXISTS youtube_video_id TEXT;
