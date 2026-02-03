# Tactical Report Feed Backend

> **Multi-signal personalized intelligence feed** — Backend solution for the Tactical Report Senior Platform Engineer take-home assignment.

**Live Demo:** [https://tactical-report-frontend.vercel.app](https://tactical-report-frontend.vercel.app)

---

## Problem Statement

**The Challenge:** Build a personalized intelligence feed system that combines multiple user engagement signals (purchases, views, campaigns, bookmarks) to deliver relevant content recommendations.

**Requirements:**
- Multi-signal ranking with weighted scoring
- Time-decay (recent actions matter more)
- Explainability (transparent "why recommended" reasoning)
- Cold-start handling for new users
- Pagination and filtering
- AI-powered insights
- Production deployment

This backend implements a recommendation engine that learns from user behavior to surface the most relevant intelligence reports for each individual.

---

## Solution Overview

A **FastAPI-based personalization engine** featuring:

- **Multi-Signal Scoring** — Combines 5 engagement types: purchases (10×), views (4×), bookmarks (2.5×), campaign clicks (2×), and stated interests
- **Time Decay** — Exponential half-life decay ensures recent actions carry more weight than older ones
- **Explainable AI** — Every recommendation includes a human-readable reason ("Because you engage with Technology content...")
- **AI Summaries** — Google Gemini generates "why it matters" impact statements, cached in SQLite to minimize API costs
- **Cold Start Handling** — New users without history receive recommendations based on their stated focus areas
- **Production Ready** — Deployed on Vercel with CORS enabled, pagination, error handling, and API documentation  

---

## Quick Start

### Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Create .env file for AI summaries
# Copy the example below and add your Gemini API key

# 3. Run the server
python main.py
```

**`.env` example (optional for AI features):**
```env
GEMINI_API_KEY=your_api_key_here
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
GEMINI_MODEL=gemini-3-flash-preview
```

**Access API at:** `http://localhost:8000`

**API Docs:** `http://localhost:8000/docs`

---

## How It Works

### 1. User Profile Building

The system analyzes each user's engagement history to build an interest profile:

```python
Profile = {
  category_interest: {
    "Technology": 15.2,  # High interest (purchases + views)
    "Finance": 8.4,      # Medium interest (views + bookmarks)
    "Healthcare": 3.0    # Low interest (stated focus only)
  },
  tag_interest: {
    "AI": 12.8,
    "Blockchain": 5.2,
    "Crypto": 4.1
  }
}
```

**Signal Weights:**
| Signal | Category Weight | Tag Weight | Half-life |
|--------|----------------|------------|-----------|
| Purchase | 10.0 | 6.0 | 90 days |
| View (150+ sec) | 4.0 + bonus | 2.5 | 60 days |
| Bookmark | 2.5 | 1.8 | 90 days |
| Campaign Click | 2.0 | 1.0 | 45 days |
| Campaign Open | 1.0 | 0.5 | 45 days |
| Stated Focus | 3.0 | 2.0 | no decay |

### 2. Report Scoring

For each candidate report (excluding already purchased):

```
score = (category_match + tag_matches + direct_signals) × (1 + 0.5 × recency)
        + 0.5 × recency_boost
        + 0.2 × popularity_fallback
```

**Example:**
```json
{
  "id": "r123",
  "title": "AI Regulation Impact on Tech Platforms",
  "category": "Technology",
  "tags": ["AI", "Regulation"],
  "score": 42.5,
  "signals": {
    "category_match": 15.2,
    "tag_match": 12.8,
    "recency_boost": 8.3,
    "popularity": 2.1
  }
}
```

### 3. AI Enhancement

Gemini generates a 1-sentence impact summary per report:

```
"AI regulation threatens platform revenue models and accelerates compliance costs."
```

**Smart Caching:** Results stored in SQLite — API only called once per report.

---

## API Reference

### `GET /api/feed`

**Description:** Get personalized feed for a user

**Query Parameters:**
- `user_id` (required) — User identifier (e.g., `u1`)
- `page` (optional, default: 1) — Page number
- `page_size` (optional, default: 10, max: 50) — Items per page
- `category` (optional) — Filter by category

**Response:**
```json
{
  "user_id": "u1",
  "page": 1,
  "page_size": 10,
  "total": 245,
  "items": [
    {
      "id": "r123",
      "title": "Q4 AI Market Analysis",
      "category": "Technology",
      "tags": ["AI", "Startups"],
      "published_at": "2026-01-15T10:00:00+00:00",
      "score": 42.5,
      "reason": "Because you engage with Technology content and tags you follow (AI, Startups)",
      "signals": {
        "category_match": 15.2,
        "tag_match": 12.8,
        "recency_boost": 8.3,
        "popularity": 2.1
      },
      "why_it_matters": "AI advancement accelerates regulatory pressure on tech platforms."
    }
  ]
}
```

### `GET /api/reports`

Returns all available reports (no personalization).

### `GET /api/users`

Returns all users with their profile information.

---

## Architecture

### Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **API** | FastAPI 0.115.5 | REST endpoints, auto-docs, async support |
| **Database** | SQLite | Lightweight, serverless persistence |
| **AI** | Google Gemini | Impact summary generation |
| **Deployment** | Vercel | Serverless hosting |
| **Language** | Python 3.9+ | Core implementation |

## Future Improvements

- Add rate limiting for feed endpoints.
- Add background job to prefill/refresh AI summaries and to age out stale cache rows.
- Auto-tagging and tag filters: extract tags from report content, persist them on reports, expose available tags, and let users filter feeds by desired tags to sharpen relevance.
- Embedding-based rerank (real or mocked) to blend semantic similarity with the existing signal/recency score.

### Using embeddings to enhance ranking
- Where AI fits: compute a sentence embedding for each report title/summary plus a user-interest embedding (from focus tags + top signals). During feed build, merge the semantic similarity score with the existing multi-signal score (e.g., weighted sum or rerank top-N).
- Latency / cost considerations: batch or precompute report embeddings; cache user embeddings; cap rerank to top-N (e.g., 100) to avoid per-request model calls.
- Caching strategy: store report embeddings in SQLite (new table) or a vector store; store user embeddings keyed by user_id and regenerate when engagements change; memoize similarity results for stable user/report pairs when feasible; fall back to mocked vectors in local/dev to avoid API costs.
