from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AdminOverviewResponse(BaseModel):
    total_users: int
    active_subscriptions: int
    expired_subscriptions: int
    banned_users: int
    active_sessions: int
    failed_logins: int
    payments_total_cents: int


class AdminUserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool
    banned: bool
    subscription_status: str | None
    subscription_plan: str | None
    subscription_expires_at: datetime | None = None
    account_limit: int | None = None
    active_session_limit: int | None = None
    accounts_count: int = 0
    active_sessions_count: int = 0
    payments_total_cents: int = 0
    created_at: datetime
    last_seen_at: datetime | None
    last_ip: str | None = None


class AdminUserListResponse(BaseModel):
    items: list[AdminUserResponse]
    total: int
    page: int
    page_size: int


class AdminUserUpdate(BaseModel):
    banned: bool | None = None
    is_admin: bool | None = None
    subscription_status: str | None = None
    plan_code: str | None = None
    confirm_self_admin_revoke: bool = False
    reason: str | None = None


class AdminSubscriptionUpdate(BaseModel):
    plan_code: str | None = None
    status: str | None = None
    extend_days: int | None = None
    expires_at: datetime | None = None
    reason: str | None = None


class AdminForceLogoutRequest(BaseModel):
    reason: str | None = None


class AdminAccountSummary(BaseModel):
    id: int
    label: str
    steamid64: str | None
    status: str
    selected_games_count: int
    created_at: datetime
    last_login_at: datetime | None


class AdminSessionSummary(BaseModel):
    id: int
    account_id: int
    status: str
    selected_games: list[int] = Field(default_factory=list)
    started_at: datetime | None
    stopped_at: datetime | None
    last_heartbeat_at: datetime | None
    error_message: str | None


class AdminPaymentResponse(BaseModel):
    id: int
    user_id: int
    username: str | None = None
    plan_code: str
    provider: str
    status: str
    amount_cents: int
    currency: str
    created_at: datetime
    updated_at: datetime


class AdminAuditResponse(BaseModel):
    id: int
    actor_user_id: int | None
    actor_username: str | None = None
    action: str
    target_type: str
    target_id: str
    metadata: dict[str, Any]
    created_at: datetime


class AdminUserDetailResponse(BaseModel):
    user: AdminUserResponse
    accounts: list[AdminAccountSummary]
    sessions: list[AdminSessionSummary]
    payments: list[AdminPaymentResponse]
    audit_events: list[AdminAuditResponse]


class AdminForceLogoutResponse(BaseModel):
    stopped_sessions: int


AdminUserFilter = Literal["all", "active", "banned", "admin", "subscribed", "expired"]
