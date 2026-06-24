"""Real ELO history via daily snapshots.

The exact per-match ELO endpoint is keyless-only and routinely Cloudflare-blocked,
and the official Data API exposes no per-match ELO. So we accumulate a genuine time
series by snapshotting a player's current ELO once per day — passively on every
lookup, and (optionally) via a scheduled job for watchlisted players.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.models import FaceitEloSnapshot, FaceitWatch


def _today() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def record_elo_snapshot(db: Session, player_id: str, elo, *, nickname: str | None = None, skill_level=None) -> None:
    """Upsert today's ELO snapshot for a player (one row per player per UTC day)."""
    if not player_id or elo in (None, ""):
        return
    try:
        elo_int = int(elo)
    except (TypeError, ValueError):
        return

    today = _today()
    lvl = int(skill_level) if skill_level is not None else None

    def _update(row: FaceitEloSnapshot) -> None:
        row.elo = elo_int
        if lvl is not None:
            row.skill_level = lvl
        if nickname:
            row.nickname = nickname

    existing = db.execute(
        select(FaceitEloSnapshot).where(
            FaceitEloSnapshot.player_id == player_id, FaceitEloSnapshot.captured_on == today
        )
    ).scalar_one_or_none()
    if existing:
        _update(existing)
        db.commit()
        return

    db.add(FaceitEloSnapshot(player_id=player_id, nickname=nickname, elo=elo_int, skill_level=lvl, captured_on=today))
    try:
        db.commit()
    except IntegrityError:  # a concurrent request inserted today's row first — update it instead
        db.rollback()
        row = db.execute(
            select(FaceitEloSnapshot).where(
                FaceitEloSnapshot.player_id == player_id, FaceitEloSnapshot.captured_on == today
            )
        ).scalar_one_or_none()
        if row:
            _update(row)
            db.commit()


def snapshot_series(db: Session, player_id: str, limit: int = 60) -> list[dict]:
    """Real ELO points (oldest→newest) for a player, from accumulated snapshots."""
    if not player_id:
        return []
    rows = db.execute(
        select(FaceitEloSnapshot)
        .where(FaceitEloSnapshot.player_id == player_id)
        .order_by(FaceitEloSnapshot.captured_on.desc())
        .limit(limit)
    ).scalars().all()
    return [{"date": r.captured_on, "elo": r.elo} for r in reversed(rows)]


def watched_player_ids(db: Session) -> list[str]:
    rows = db.execute(select(FaceitWatch.player_id).distinct()).scalars().all()
    return [r for r in rows if r]


def run_watchlist_snapshots() -> int:
    """Scheduled job: snapshot today's ELO for every watchlisted player.

    Enqueue from cron / a scheduler (the RQ worker can run it). Returns how many
    players were snapshotted. Safe to run repeatedly — one row per player per day.
    """
    from app.core.database import SessionLocal
    from app.faceit.service import find_player  # local import to avoid a cycle

    db = SessionLocal()
    count = 0
    try:
        for player_id in watched_player_ids(db):
            result = find_player(player_id)
            if result.get("found") and result.get("player_id"):
                record_elo_snapshot(
                    db, result["player_id"], result.get("faceit_elo"),
                    nickname=result.get("nickname"), skill_level=result.get("skill_level"),
                )
                count += 1
    finally:
        db.close()
    return count
