from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Report(BaseModel):
    id: str
    title: str
    category: str
    tags: List[str]
    published_at: str


class User(BaseModel):
    id: str
    name: str
    role: str
    focus_categories: List[str] = Field(default_factory=list)
    focus_tags: List[str] = Field(default_factory=list)


class FeedItem(BaseModel):
    id: str
    title: str
    category: str
    tags: List[str]
    published_at: str
    score: float
    reason: str
    signals: Dict[str, float]
    why_it_matters: Optional[str] = None


class FeedResponse(BaseModel):
    user_id: str
    page: int
    page_size: int
    total: int
    items: List[FeedItem]
