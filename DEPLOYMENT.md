# CreatorOS public V1 launch

## 1. Supabase (do this first)

1. In **SQL Editor**, run `backend/db/schema.sql`, then run
   `backend/db/launch_migration.sql`.
2. In **Authentication > Providers**, enable **Email**. For a fast private
   beta, disable **Confirm email**. Re-enable it before a broad public launch.
3. In **Authentication > URL Configuration**, add your future Vercel URL to
   **Site URL** and **Redirect URLs** after it exists.
4. In **Project Settings > API**, copy:
   - Project URL
   - publishable/anon key (frontend only)
   - service-role key (Railway only; never Vercel)

The `creator-media` bucket is private. The API has the service key and checks
the creator identity before it serves a short-lived media URL.

## 2. Google / YouTube

1. In Google Cloud, create a project and enable **YouTube Data API v3**.
2. Configure the OAuth consent screen as **External** and add yourself and
   other demo users as test users. Add a privacy-policy URL and support email.
3. Create **OAuth client ID > Web application**. Add this authorized redirect
   URI after Railway creates a public domain:
   `https://YOUR-RAILWAY-DOMAIN/api/youtube/oauth/callback`
4. Copy the client ID and client secret to Railway only.

For the deadline, users added as Google test users can authorize the app. A
public YouTube app requesting upload/comment-management scopes requires Google
verification; until then, uploads from newly created unverified API projects
are restricted to private visibility.

## 3. Railway API

1. Create a service from this GitHub repository. Set the root directory to
   `backend`; Railway will use `backend/Dockerfile`.
2. Add these variables:

```text
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
GROQ_API_KEY_1=
GROQ_API_KEY_2=               # optional
GROQ_API_KEY_3=               # optional
GROQ_API_KEY_4=               # optional
GROQ_API_KEY_5=               # optional
GROQ_MODEL=openai/gpt-oss-120b
YOUTUBE_API_KEY=
YOUTUBE_OAUTH_CLIENT_ID=
YOUTUBE_OAUTH_CLIENT_SECRET=
YOUTUBE_OAUTH_REDIRECT_URI=https://YOUR-RAILWAY-DOMAIN/api/youtube/oauth/callback
FRONTEND_ORIGINS=https://YOUR-VERCEL-DOMAIN
```

3. Generate a public Railway domain. Confirm `https://YOUR-RAILWAY-DOMAIN/health`
   returns `{"status":"ok"}`.

## 4. Vercel frontend

1. Import the same repository, with root directory `frontend`.
2. Add build-time variables:

```text
VITE_API_BASE=https://YOUR-RAILWAY-DOMAIN/api
VITE_SUPABASE_URL=https://YOUR-PROJECT.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_SUPABASE_PUBLISHABLE_KEY
```

3. Deploy. Then put the final Vercel domain in Railway's `FRONTEND_ORIGINS`
   and Supabase Auth URL Configuration; redeploy Railway.

## Smoke test

Use a real 10–30 second spoken MP3. Sign up, sign in, upload it, and confirm
the transcript and upload package appear. Then connect one Google test user,
publish as **private**, and verify the video appears on that same test user's
YouTube channel.
