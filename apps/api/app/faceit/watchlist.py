"""Server-side FACEIT watchlist for logged-in users (anonymous users use localStorage)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.models import FaceitWatch


def list_watches(db: Session, user_id: int) -> list[dict]:
    rows = db.execute(
        select(FaceitWatch).where(FaceitWatch.user_id == user_id).order_by(FaceitWatch.created_at.desc())
    ).scalars().all()
    return [{"player_id": r.player_id, "nickname": r.nickname, "country": r.country} for r in rows]


def add_watch(db: Session, user_id: int, player_id: str, *, nickname: str | None = None, country: str | None = None) -> dict:
    existing = db.execute(
        select(FaceitWatch).where(FaceitWatch.user_id == user_id, FaceitWatch.player_id == player_id)
    ).scalar_one_or_none()
    if existing:
        existing.nickname = nickname or existing.nickname
        existing.country = country or existing.country
        db.commit()
        return {"player_id": existing.player_id, "nickname": existing.nickname, "country": existing.country}

    db.add(FaceitWatch(user_id=user_id, player_id=player_id, nickname=nickname, country=country))
    try:
        db.commit()
    except IntegrityError:  # a concurrent request added it first — update that row instead
        db.rollback()
        row = db.execute(
            select(FaceitWatch).where(FaceitWatch.user_id == user_id, FaceitWatch.player_id == player_id)
        ).scalar_one_or_none()
        if row:
            row.nickname = nickname or row.nickname
            row.country = country or row.country
            db.commit()
    return {"player_id": player_id, "nickname": nickname, "country": country}


def remove_watch(db: Session, user_id: int, player_id: str) -> bool:
    existing = db.execute(
        select(FaceitWatch).where(FaceitWatch.user_id == user_id, FaceitWatch.player_id == player_id)
    ).scalar_one_or_none()
    if not existing:
        return False
    db.delete(existing)
    db.commit()
    return True
