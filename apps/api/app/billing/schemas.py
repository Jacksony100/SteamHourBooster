from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PlanResponse(BaseModel):
    code: str
    name: str
    price_cents: int
    duration_days: int | None
    account_limit: int
    active_session_limit: int
    support_level: str
    features: list[str]
    active: bool


class SubscriptionResponse(BaseModel):
    plan_code: str
    status: str
    active: bool
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    ends_at: datetime | None
    manual_override: bool = False
    canceled_at: datetime | None = None
    cancel_at_period_end: bool = False
    account_limit: int
    active_session_limit: int
    support_level: str
    features: list[str]


class CheckoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_code: str


class CheckoutResponse(BaseModel):
    payment_id: int
    provider: str
    status: str
    checkout_url: str | None
    idempotency_key: str


class PaymentResponse(BaseModel):
    id: int
    plan_code: str
    provider: str
    status: str
    amount_cents: int
    currency: str
    checkout_url: str | None
    idempotency_key: str
    provider_payment_id: str | None
    created_at: datetime
    updated_at: datetime


class WebhookResponse(BaseModel):
    ok: bool
    event_id: int
    event_type: str
    verified: bool
    payment_id: int | None
