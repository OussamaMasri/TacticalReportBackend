import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from models import Report, User
from settings import DB_PATH


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema(conn: sqlite3.Connection):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            tags TEXT NOT NULL,
            published_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            focus_categories TEXT NOT NULL,
            focus_tags TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS purchases (
            user_id TEXT NOT NULL,
            report_id TEXT NOT NULL,
            purchased_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS views (
            user_id TEXT NOT NULL,
            report_id TEXT NOT NULL,
            viewed_at TEXT NOT NULL,
            dwell_time_seconds INTEGER
        );
        CREATE TABLE IF NOT EXISTS campaigns (
            user_id TEXT NOT NULL,
            report_id TEXT NOT NULL,
            campaign_type TEXT,
            action TEXT,
            occurred_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS bookmarks (
            user_id TEXT NOT NULL,
            report_id TEXT NOT NULL,
            bookmarked_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS ai_insights (
            report_id TEXT PRIMARY KEY,
            content TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_purchases_user ON purchases(user_id);
        CREATE INDEX IF NOT EXISTS idx_views_user ON views(user_id);
        CREATE INDEX IF NOT EXISTS idx_campaigns_user ON campaigns(user_id);
        CREATE INDEX IF NOT EXISTS idx_bookmarks_user ON bookmarks(user_id);
        """
    )


def _load_reports(conn: sqlite3.Connection) -> List[Report]:
    rows = conn.execute("SELECT id, title, category, tags, published_at FROM reports").fetchall()
    return [
        Report(id=row["id"], title=row["title"], category=row["category"], tags=json.loads(row["tags"]), published_at=row["published_at"])
        for row in rows
    ]


def _load_users(conn: sqlite3.Connection) -> Dict[str, User]:
    rows = conn.execute("SELECT id, name, role, focus_categories, focus_tags FROM users").fetchall()
    return {
        row["id"]: User(
            id=row["id"],
            name=row["name"],
            role=row["role"],
            focus_categories=json.loads(row["focus_categories"]),
            focus_tags=json.loads(row["focus_tags"]),
        )
        for row in rows
    }


def _load_engagements(conn: sqlite3.Connection):
    purchases = [
        dict(user_id=row["user_id"], report_id=row["report_id"], purchased_at=row["purchased_at"])
        for row in conn.execute("SELECT user_id, report_id, purchased_at FROM purchases")
    ]
    views = [
        dict(
            user_id=row["user_id"],
            report_id=row["report_id"],
            viewed_at=row["viewed_at"],
            dwell_time_seconds=row["dwell_time_seconds"],
        )
        for row in conn.execute("SELECT user_id, report_id, viewed_at, dwell_time_seconds FROM views")
    ]
    campaigns = [
        dict(
            user_id=row["user_id"],
            report_id=row["report_id"],
            campaign_type=row["campaign_type"],
            action=row["action"],
            occurred_at=row["occurred_at"],
        )
        for row in conn.execute("SELECT user_id, report_id, campaign_type, action, occurred_at FROM campaigns")
    ]
    bookmarks = [
        dict(user_id=row["user_id"], report_id=row["report_id"], bookmarked_at=row["bookmarked_at"])
        for row in conn.execute("SELECT user_id, report_id, bookmarked_at FROM bookmarks")
    ]
    return {"purchases": purchases, "views": views, "campaigns": campaigns, "bookmarks": bookmarks}


def _init_from_db():
    with _connect() as conn:
        _ensure_schema(conn)
        rep = _load_reports(conn)
        usr = _load_users(conn)
        eng = _load_engagements(conn)
    return rep, usr, eng


def get_ai_insight(report_id: str) -> Optional[str]:
    with _connect() as conn:
        row = conn.execute("SELECT content FROM ai_insights WHERE report_id = ?", (report_id,)).fetchone()
        return row["content"] if row else None


def set_ai_insight(report_id: str, content: str):
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO ai_insights (report_id, content) VALUES (?, ?)",
            (report_id, content),
        )
        conn.commit()


reports, users, engagements = _init_from_db()
