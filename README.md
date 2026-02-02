# Tactical Report Feed Backend

Backend service for the Tactical Report multi-signal, personalized intelligence feed. It scores reports for each user using historical engagements, stated interests, publication recency, and a short LLM-generated "why it matters" blurb with caching.

## How the implementation meets the assignment
- Multi-signal ranking: `scoring.py` builds per-user profiles from purchases, views (with dwell-time bonus), campaign interactions, bookmarks, and stated focus. Each action has explicit weights in `settings.py`.
- Recency-aware: `recency_decay` applies half-life decay per signal and per-publication to surface timely items.
- Explainable results: `compute_reason` assembles a human-readable reason for every feed item (category/tag affinity, prior views, bookmarks, campaign actions, or popularity fallback).
- AI "why it matters": `why_it_matters` fetches a 1-sentence impact summary from Gemini (OpenAI-compatible SDK) and caches it in SQLite (`ai_insights`) to avoid repeated calls.
- Cold start protection: users start with category/tag interest seeded from their `focus_categories`/`focus_tags`.
- Production-ready API: FastAPI app with Pydantic models, CORS open for quick testing, and pagination/filtering on the feed.

## Repository layout
- `api.py` — FastAPI routes (`/api/feed`, `/api/reports`, `/api/users`) and CORS.
- `api/index.py` — Vercel entrypoint that imports the same FastAPI app.
- `scoring.py` — Profile building, signal weights, recency decay, scoring, reasons, popularity backstop, and AI summary with SQLite cache.
- `data_loader.py` — Ensures SQLite schema, loads reports/users/engagements/AI cache into memory, provides getters/setters for `ai_insights`.
- `models.py` — Pydantic request/response schemas (FeedItem includes score, reason, signals, why_it_matters).
- `settings.py` — Paths, dotenv load, and tunable weights.
- `data/app.db` — SQLite database seeded with reports, users, engagements, and AI cache table.
- `main.py` — Local dev entry (uvicorn reload).
- `vercel.json` — Serverless configuration to deploy `api/index.py` on Vercel.

## Personalization details
- Signal weights (see `settings.py`): purchases carry the most weight; views include a dwell-time bonus; campaign clicks/opens and bookmarks add smaller boosts; tag matches get an extra fixed bump; focus categories/tags seed initial interest.
- Recency decay: exponential half-life per signal type (e.g., purchases 90d, views 60d, campaigns 45d, bookmarks 90d) plus publication recency (120d) folded into the final score.
- Popularity fallback: light popularity term prevents empty feeds for sparse users.
- Why/Reason: `compute_reason` builds a transparent sentence, while `why_it_matters` adds the optional AI-generated impact sentence (skips if no API key or SDK).

## API
- `GET /api/feed`
  - Query params: `user_id` (required), `page` (default 1), `page_size` (default 10, max 50), `category` (optional filter).
  - Response: `FeedResponse` with `items[]` containing `score`, `reason`, `signals`, and `why_it_matters`.
- `GET /api/reports` — All reports.
- `GET /api/users` — All users.

Example:
```
curl "http://localhost:8000/api/feed?user_id=u1&page=1&page_size=10"
```

## Running locally
Prereqs: Python 3.9+, SQLite (bundled), optional Gemini API key for AI blurbs.

1) Install deps  
```bash
pip install -r requirements.txt
```

2) Configure env (optional but recommended for AI summaries)  
```
GEMINI_API_KEY=your_api_key
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
GEMINI_MODEL=gemini-3-flash-preview
```

3) Start the API  
```bash
python main.py
# or: uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

The database schema is created automatically on startup, and data is loaded from `data/app.db`.

## Deployment
- Serverless target: Vercel Python with `api/index.py` as the entry and `vercel.json` rewrite for `/api/*`.
- Set env vars in the Vercel dashboard (`GEMINI_API_KEY`, `GEMINI_BASE_URL`, `GEMINI_MODEL`).
- Live deployment URL: `https://tactical-report-backend.vercel.app/`.

## Future improvements
- Add rate limiting for feed endpoints.
- Add background job to prefill/refresh AI summaries and to age out stale cache rows.
- Auto-tagging and tag filters: extract tags from report content, persist them on reports, expose available tags, and let users filter feeds by desired tags to sharpen relevance.
