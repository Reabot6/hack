-- CreatorOS public-V1 launch migration
-- Run this once in Supabase: SQL Editor > New query > Run.

-- Durable location for the original upload. The API, not the browser, reads it.
alter table public.videos add column if not exists source_storage_path text;

-- One encrypted-at-rest JSON token record per authenticated creator.
-- This table is server-only: it has RLS enabled and no client policies.
create table if not exists public.youtube_connections (
  user_id uuid primary key references auth.users(id) on delete cascade,
  token_data jsonb not null,
  connected_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- OAuth state ties Google's callback to the correct signed-in CreatorOS user.
create table if not exists public.youtube_oauth_states (
  state text primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  expires_at timestamptz not null,
  created_at timestamptz not null default now()
);

alter table public.videos enable row level security;
alter table public.upload_packages enable row level security;
alter table public.comments enable row level security;
alter table public.clip_opportunities enable row level security;
alter table public.alerts enable row level security;
alter table public.notifications enable row level security;
alter table public.youtube_connections enable row level security;
alter table public.youtube_oauth_states enable row level security;

-- The CreatorOS API uses the Supabase service-role key and therefore bypasses
-- RLS. Deliberately create no browser policies for creator data or tokens.

-- Create a private bucket for originals and rendered clips. It is idempotent.
insert into storage.buckets (id, name, public)
values ('creator-media', 'creator-media', false)
on conflict (id) do update set public = false;

-- No storage.objects policies: browser clients never access this bucket;
-- the API creates time-limited signed links only after checking ownership.
