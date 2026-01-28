from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from .data_loader import engagements, reports, users
from .models import FeedItem, Report, User
from .settings import WEIGHTS

UTC = timezone.utc


def parse_date(value: str) -> datetime:
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    return datetime.fromisoformat(value).astimezone(UTC)


def recency_decay(then: datetime, half_life_days: float = 45.0) -> float:
    delta_days = max((datetime.now(UTC) - then).days, 0)
    return math.exp(-delta_days / half_life_days)


@dataclass
class Profile:
    cat_interest: Dict[str, float]
    tag_interest: Dict[str, float]
    purchased: set
    viewed: Dict[str, dict]
    campaigns: Dict[str, dict]
    bookmarks: set


def build_profiles() -> Dict[str, Profile]:
    profiles: Dict[str, Profile] = {}
    for user in users.values():
        profiles[user.id] = Profile(
            cat_interest=defaultdict(float),
            tag_interest=defaultdict(float),
            purchased=set(),
            viewed={},
            campaigns={},
            bookmarks=set(),
        )

    for entry in engagements.get("purchases", []):
        uid = entry["user_id"]
        rid = entry["report_id"]
        profiles[uid].purchased.add(rid)
        report = next((r for r in reports if r.id == rid), None)
        if report:
            decay = recency_decay(parse_date(entry["purchased_at"]), half_life_days=90)
            profiles[uid].cat_interest[report.category] += WEIGHTS["purchase_cat"] * decay
            for tag in report.tags:
                profiles[uid].tag_interest[tag] += WEIGHTS["purchase_tag"] * decay

    for entry in engagements.get("views", []):
        uid = entry["user_id"]
        rid = entry["report_id"]
        profiles[uid].viewed[rid] = entry
        report = next((r for r in reports if r.id == rid), None)
        if report:
            decay = recency_decay(parse_date(entry["viewed_at"]), half_life_days=60)
            dwell = entry.get("dwell_time_seconds", 0)
            dwell_factor = WEIGHTS["view_long_bonus"] if dwell >= 150 else 1.0
            profiles[uid].cat_interest[report.category] += WEIGHTS["view_cat"] * decay
            for tag in report.tags:
                profiles[uid].tag_interest[tag] += WEIGHTS["view_tag"] * decay
            profiles[uid].cat_interest[report.category] += dwell_factor * decay

    for entry in engagements.get("campaigns", []):
        uid = entry["user_id"]
        rid = entry["report_id"]
        profiles[uid].campaigns[rid] = entry
        weight = WEIGHTS["campaign_click"] if entry.get("action") == "clicked" else WEIGHTS["campaign_open"]
        decay = recency_decay(parse_date(entry["occurred_at"]), half_life_days=45)
        report = next((r for r in reports if r.id == rid), None)
        if report:
            profiles[uid].cat_interest[report.category] += weight * decay
            for tag in report.tags:
                profiles[uid].tag_interest[tag] += weight * 0.5 * decay

    for entry in engagements.get("bookmarks", []):
        uid = entry["user_id"]
        rid = entry["report_id"]
        profiles[uid].bookmarks.add(rid)
        decay = recency_decay(parse_date(entry["bookmarked_at"]), half_life_days=90)
        report = next((r for r in reports if r.id == rid), None)
        if report:
            profiles[uid].cat_interest[report.category] += WEIGHTS["bookmark"] * decay
            for tag in report.tags:
                profiles[uid].tag_interest[tag] += WEIGHTS["tag_match"] * decay

    # Seed with stated focus to avoid cold start
    for user in users.values():
        pf = profiles[user.id]
        for cat in user.focus_categories:
            pf.cat_interest[cat] += WEIGHTS["focus_cat"]
        for tag in user.focus_tags:
            pf.tag_interest[tag] += WEIGHTS["focus_tag"]
    return profiles


profiles = build_profiles()

popularity = Counter()
for entry in engagements.get("purchases", []) + engagements.get("views", []) + engagements.get("campaigns", []):
    popularity[entry["report_id"]] += 1


def compute_reason(report: Report, signals: Dict[str, float], profile: Profile) -> str:
    parts = []
    if report.category in profile.cat_interest and profile.cat_interest[report.category] > 0:
        parts.append(f"you engage with {report.category.lower()} content")
    tag_hits = [t for t in report.tags if profile.tag_interest.get(t)]
    if tag_hits:
        parts.append(f"tags you follow ({', '.join(tag_hits[:3])})")
    if report.id in profile.viewed:
        parts.append("you viewed this recently")
    if report.id in profile.bookmarks:
        parts.append("you bookmarked similar items")
    if report.id in profile.campaigns:
        action = profile.campaigns[report.id].get("action", "opened")
        parts.append(f"you {action} a campaign on this topic")
    if not parts and popularity.get(report.id):
        parts.append("popular in your region and recency boosted")
    if not parts:
        parts.append("recent and relevant to your stated focus")
    return "Because " + " and ".join(parts)


def why_it_matters(report: Report) -> str:
    tag_line = ""
    if "UAV" in report.tags or "air-defense" in report.tags:
        tag_line = "air and counter-UAS posture"
    elif "hydrogen" in report.tags or "LNG" in report.tags:
        tag_line = "energy export positioning"
    elif "policy" in report.tags or "governance" in report.tags:
        tag_line = "regulatory stability"
    elif "grid" in report.tags or "storage" in report.tags:
        tag_line = "infrastructure resilience"
    elif "elections" in report.tags:
        tag_line = "political timing and risk"
    if tag_line:
        return f"This shapes {tag_line} for regional stakeholders."
    return "Brief insight on strategic shifts affecting the region."


def score_report(report: Report, profile: Profile) -> Tuple[float, Dict[str, float]]:
    signals: Dict[str, float] = {}
    base = 0.0

    cat_bonus = profile.cat_interest.get(report.category, 0.0)
    if cat_bonus:
        signals["category_match"] = cat_bonus
        base += cat_bonus

    tag_hits = [tag for tag in report.tags if profile.tag_interest.get(tag)]
    if tag_hits:
        tag_score = sum(profile.tag_interest[tag] for tag in tag_hits) + WEIGHTS["tag_match"] * len(tag_hits)
        signals["tag_match"] = tag_score
        base += tag_score

    # Direct signals
    if report.id in profile.viewed:
        view = profile.viewed[report.id]
        dwell = view.get("dwell_time_seconds", 0)
        decay = recency_decay(parse_date(view["viewed_at"]), half_life_days=60)
        view_score = WEIGHTS["view_cat"] * decay + (WEIGHTS["view_long_bonus"] if dwell >= 150 else 1.0)
        signals["viewed"] = view_score
        base += view_score

    if report.id in profile.campaigns:
        campaign = profile.campaigns[report.id]
        weight = WEIGHTS["campaign_click"] if campaign.get("action") == "clicked" else WEIGHTS["campaign_open"]
        decay = recency_decay(parse_date(campaign["occurred_at"]), half_life_days=45)
        camp_score = weight * decay
        signals["campaign"] = camp_score
        base += camp_score

    if report.id in profile.bookmarks:
        signals["bookmark"] = WEIGHTS["bookmark"]
        base += WEIGHTS["bookmark"]

    # Recency of publication
    recency = recency_decay(parse_date(report.published_at), half_life_days=120)
    final_score = base * (1 + 0.5 * recency) + 0.5 * recency
    signals["recency_boost"] = round(0.5 * recency, 3)

    return final_score, signals


def build_feed(user_id: str, category: Optional[str] = None) -> List[FeedItem]:
    if user_id not in users:
        raise ValueError("user not found")
    profile = profiles[user_id]

    candidates = [r for r in reports if r.id not in profile.purchased]
    if category:
        candidates = [r for r in candidates if r.category.lower() == category.lower()]

    scored: List[FeedItem] = []
    for report in candidates:
        score, signals = score_report(report, profile)
        # slight popularity backstop
        score += 0.2 * popularity.get(report.id, 0)
        fi = FeedItem(
            id=report.id,
            title=report.title,
            category=report.category,
            tags=report.tags,
            published_at=report.published_at,
            score=round(score, 3),
            reason=compute_reason(report, signals, profile),
            signals={k: round(v, 3) for k, v in signals.items()},
            why_it_matters=why_it_matters(report),
        )
        scored.append(fi)

    scored.sort(key=lambda x: x.score, reverse=True)
    return scored
