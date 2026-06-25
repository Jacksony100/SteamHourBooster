from datetime import datetime
from enum import Enum
from typing import Optional

from app.core.database import Base
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Stored in password_encrypted when no real password is collected (demo / post-link).
DEMO_NO_PASSWORD_MARKER = "[deckpilot-demo-no-password-collected]"


class AccountStatus(str, Enum):
    offline = "offline"
    online = "online"
    starting = "starting"
    error = "error"


class SessionStatus(str, Enum):
    starting = "starting"
    pending = "pending"
    running = "running"
    stopping = "stopping"
    stopped = "stopped"
    error = "error"
    failed = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    email_verification_token_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    email_verification_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    # Set when the account was created via "Sign in with Steam" (Steam OpenID).
    steam_id: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True, index=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    banned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_ip: Mapped[str | None] = mapped_column(String(80), nullable=True)

    accounts: Mapped[list["SteamAccount"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    subscription: Mapped[Optional["Subscription"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    web_sessions: Mapped[list["UserSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    session_id_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="web_sessions")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    request_ip_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="password_reset_tokens")


class SteamAccount(Base):
    __tablename__ = "steam_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(120))
    username_encrypted: Mapped[str] = mapped_column(Text)
    password_encrypted: Mapped[str] = mapped_column(Text)
    # Encrypted Steam refresh token / login_key captured after first real login, so
    # subsequent sessions reuse it instead of the stored password.
    steam_refresh_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    steamid64: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=AccountStatus.offline.value)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped[User] = relationship(back_populates="accounts")
    selected_games: Mapped[list["AccountGame"]] = relationship(back_populates="account", cascade="all, delete-orphan")
    sessions: Mapped[list["ActivitySession"]] = relationship(back_populates="account", cascade="all, delete-orphan")
    steam_sessions: Mapped[list["SteamSession"]] = relationship(back_populates="account", cascade="all, delete-orphan")
    account_status: Mapped[Optional["AccountStatusRecord"]] = relationship(back_populates="account", cascade="all, delete-orphan")


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    app_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))


class AccountGame(Base):
    __tablename__ = "account_games"
    __table_args__ = (UniqueConstraint("account_id", "game_id", name="uq_account_game"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("steam_accounts.id", ondelete="CASCADE"), index=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True)

    account: Mapped[SteamAccount] = relationship(back_populates="selected_games")
    game: Mapped[Game] = relationship()


class ActivitySession(Base):
    __tablename__ = "activity_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("steam_accounts.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(32), default=SessionStatus.pending.value)
    current_games: Mapped[str] = mapped_column(Text, default="[]")
    worker_job_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    account: Mapped[SteamAccount] = relationship(back_populates="sessions")
    logs: Mapped[list["SessionLog"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class SessionLog(Base):
    __tablename__ = "session_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("activity_sessions.id", ondelete="CASCADE"), index=True)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped[ActivitySession] = relationship(back_populates="logs")


class AccountStatusRecord(Base):
    __tablename__ = "account_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("steam_accounts.id", ondelete="CASCADE"), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default=AccountStatus.offline.value, index=True)
    last_event: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    account: Mapped[SteamAccount] = relationship(back_populates="account_status")


class SteamSession(Base):
    __tablename__ = "steam_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("steam_accounts.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(32), default=SessionStatus.starting.value, index=True)
    selected_games: Mapped[str] = mapped_column(Text, default="[]")
    worker_job_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    account: Mapped[SteamAccount] = relationship(back_populates="steam_sessions")
    events: Mapped[list["SessionEvent"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class SessionEvent(Base):
    __tablename__ = "session_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("steam_sessions.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("steam_accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(120), index=True)
    message: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped[SteamSession | None] = relationship(back_populates="events")


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    price_cents: Mapped[int] = mapped_column(Integer)
    interval_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    account_limit: Mapped[int] = mapped_column(Integer, default=1)
    active_session_limit: Mapped[int] = mapped_column(Integer, default=1)
    support_level: Mapped[str] = mapped_column(String(80), default="community")
    features_json: Mapped[str] = mapped_column(Text, default="[]")
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="plan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="plan")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("plans.id", ondelete="SET NULL"), nullable=True)
    plan_code: Mapped[str] = mapped_column(String(64), default="free")
    status: Mapped[str] = mapped_column(String(32), default="inactive")
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    manual_override: Mapped[bool] = mapped_column(Boolean, default=False)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="subscription")
    plan: Mapped[Plan | None] = relationship(back_populates="subscriptions")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("plans.id", ondelete="SET NULL"), nullable=True)
    provider: Mapped[str] = mapped_column(String(40), index=True)
    provider_payment_id: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    checkout_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="pending", index=True)
    amount_cents: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(12), default="USD")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship()
    plan: Mapped[Plan | None] = relationship(back_populates="payments")
    events: Mapped[list["BillingEvent"]] = relationship(back_populates="payment", cascade="all, delete-orphan")


class BillingEvent(Base):
    __tablename__ = "billing_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_id: Mapped[int | None] = mapped_column(ForeignKey("payments.id", ondelete="SET NULL"), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(40), index=True)
    event_type: Mapped[str] = mapped_column(String(120), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    payment: Mapped[Payment | None] = relationship(back_populates="events")


class BanCache(Base):
    __tablename__ = "ban_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("steam_accounts.id", ondelete="CASCADE"), unique=True)
    payload: Mapped[str] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    target_type: Mapped[str] = mapped_column(String(80))
    target_id: Mapped[str] = mapped_column(String(80), index=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SteamProfileCache(Base):
    """Cached public Steam profile/avatar data for an account (no credentials)."""

    __tablename__ = "steam_profile_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("steam_accounts.id", ondelete="CASCADE"), unique=True, index=True)
    steamid64: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    persona_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    profile_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_small: Mapped[str | None] = mapped_column(String(512), nullable=True)
    avatar_medium: Mapped[str | None] = mapped_column(String(512), nullable=True)
    avatar_full: Mapped[str | None] = mapped_column(String(512), nullable=True)
    persona_state: Mapped[int | None] = mapped_column(Integer, nullable=True)
    visibility: Mapped[str] = mapped_column(String(32), default="unknown")
    fetch_status: Mapped[str] = mapped_column(String(32), default="ok", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SteamGameAsset(Base):
    """Cached, normalized Steam CDN artwork URLs for an app id."""

    __tablename__ = "steam_game_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    app_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    header_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    capsule_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    library_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    icon_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    store_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source: Mapped[str] = mapped_column(String(40), default="steam_cdn")
    last_fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SteamOwnedGameCache(Base):
    """Cached owned-games list per account (public ownership/playtime data)."""

    __tablename__ = "steam_owned_games_cache"
    __table_args__ = (UniqueConstraint("account_id", "app_id", name="uq_owned_game_cache"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("steam_accounts.id", ondelete="CASCADE"), index=True)
    app_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    playtime_forever: Mapped[int] = mapped_column(Integer, default=0)
    img_icon_hash: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FaceitEloSnapshot(Base):
    """Daily ELO snapshot for a FACEIT player, captured on lookup / by the watch job.

    Builds a *real* ELO time series over time (the exact per-match ELO API is keyless-
    only and Cloudflare-blocked). One row per player per calendar day (UTC)."""

    __tablename__ = "faceit_elo_snapshots"
    __table_args__ = (UniqueConstraint("player_id", "captured_on", name="uq_faceit_elo_snapshot_day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[str] = mapped_column(String(64), index=True)
    nickname: Mapped[str | None] = mapped_column(String(80), nullable=True)
    elo: Mapped[int] = mapped_column(Integer)
    skill_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    captured_on: Mapped[str] = mapped_column(String(10), index=True)  # YYYY-MM-DD (UTC)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FaceitWatch(Base):
    """A player a user pins to their FACEIT watchlist (for quick re-lookup + ELO tracking)."""

    __tablename__ = "faceit_watches"
    __table_args__ = (UniqueConstraint("user_id", "player_id", name="uq_faceit_watch"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    player_id: Mapped[str] = mapped_column(String(64), index=True)
    nickname: Mapped[str | None] = mapped_column(String(80), nullable=True)
    country: Mapped[str | None] = mapped_column(String(8), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
