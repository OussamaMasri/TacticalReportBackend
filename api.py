from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from data_loader import reports, users
from models import FeedResponse, Report, User
from scoring import build_feed

app = FastAPI(title="Tactical Report Feed API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/reports", response_model=list[Report])
def list_reports():
    return reports


@app.get("/api/users", response_model=list[User])
def list_users():
    return list(users.values())


@app.get("/api/feed", response_model=FeedResponse)
def get_feed(
    user_id: str = Query(..., description="User id"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    category: str | None = Query(None, description="Optional category filter"),
):
    try:
        scored = build_feed(user_id, category)
    except ValueError:
        raise HTTPException(status_code=404, detail="user not found")

    total = len(scored)
    start = (page - 1) * page_size
    end = start + page_size
    return FeedResponse(
        user_id=user_id,
        page=page,
        page_size=page_size,
        total=total,
        items=scored[start:end],
    )
