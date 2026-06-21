import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit.service import write_audit
from app.billing.providers import ProviderEvent, provider_for
from app.core.config import get_settings
from app.core.models import BillingEvent, Payment, Plan, SessionStatus, SteamAccount, SteamSession, Subscription, User

PLAN_DEFINITIONS = [
    {
        "code": "trial",
        "name": "Trial / Demo",
        "price_cents": 0,
        "duration_days": 14,
        "account_limit": 1,
        "active_session_limit": 0,
        "support_level": "community",
        "features": ["1 Steam account", "Game selection preview", "Ban info panel", "No active sessions"],
    },
    {
        "code": "starter",
        "name": "Starter",
        "price_cents": 900,
        "duration_days": 30,
        "account_limit": 3,
        "active_session_limit": 1,
        "support_level": "community",
        "features": ["Up to 3 accounts", "1 active session", "Game selector", "Activity log"],
    },
    {
        "code": "pro",
        "name": "Pro",
        "price_cents": 1900,
        "duration_days": 30,
        "account_limit": 10,
        "active_session_limit": 3,
        "support_level": "priority",
        "features": ["Up to 10 accounts", "3 active sessions", "Ban info cache", "Priority support"],
    },
    {
        "code": "ultra",
        "name": "Ultra",
        "price_cents": 4900,
        "duration_days": 30,
        "account_limit": 30,
        "active_session_limit": 10,
        "support_level": "priority+",
        "features": ["Up to 30 accounts", "10 active sessions", "Admin-grade logs", "Priority+ support"],
    },
    {
        "code": "lifetime",
        "name": "Lifetime",
        "price_cents": 14900,
        "duration_days": None,
        "account_limit": 30,
        "active_session_limit": 10,
        "support_level": "lifetime",
        "features": ["Lifetime access", "Up to 30 accounts", "10 active sessions", "Manual approval or dedicated checkout"],
    },
]


ACTIVE_STATUSES = {"active", "trialing"}
PAID_STATUSES = {"paid", "succeeded", "confirmed", "completed"}
FAILED_STATUSES = {"failed", "expired", "canceled", "cancelled"}


def now_utc() -> datetime:
    return datetime.now(UTC)


def as_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def sync_default_plans(db: Session) -> list[Plan]:
    plans: list[Plan] = []
    for definition in PLAN_DEFINITIONS:
        plan = db.query(Plan).filter(Plan.code == definition["code"]).one_or_none()
        if not plan:
            plan = Plan(code=definition["code"])
            db.add(plan)
        plan.name = definition["name"]
        plan.price_cents = definition["price_cents"]
        plan.interval_days = definition["duration_days"]
        plan.duration_days = definition["duration_days"]
        plan.account_limit = definition["account_limit"]
        plan.active_session_limit = definition["active_session_limit"]
        plan.support_level = definition["support_level"]
        plan.features_json = json.dumps(definition["features"])
        plan.active = True
        plans.append(plan)
    db.commit()
    return plans


def get_plan(db: Session, plan_code: str) -> Plan:
    plan = db.query(Plan).filter(Plan.code == plan_code, Plan.active.is_(True)).one_or_none()
    if not plan:
        sync_default_plans(db)
        plan = db.query(Plan).filter(Plan.code == plan_code, Plan.active.is_(True)).one_or_none()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan


def plan_features(plan: Plan) -> list[str]:
    try:
        return list(json.loads(plan.features_json or "[]"))
    except json.JSONDecodeError:
        return []


def ensure_trial_subscription(db: Session, user: User) -> Subscription:
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).one_or_none()
    if subscription:
        return subscription

    plan = get_plan(db, "trial")
    started_at = now_utc()
    expires_at = started_at + timedelta(days=plan.duration_days or 14)
    subscription = Subscription(
        user_id=user.id,
        plan_id=plan.id,
        plan_code=plan.code,
        status="trialing",
        starts_at=started_at,
        expires_at=expires_at,
        ends_at=expires_at,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


def current_subscription(db: Session, user: User) -> Subscription:
    subscription = ensure_trial_subscription(db, user)
    if subscription.plan_id is None and subscription.plan_code:
        plan = db.query(Plan).filter(Plan.code == subscription.plan_code).one_or_none()
        if plan:
            subscription.plan_id = plan.id
            db.commit()
            db.refresh(subscription)
    expires_at = as_aware(subscription.expires_at or subscription.ends_at)
    if subscription.status in ACTIVE_STATUSES and expires_at and expires_at < now_utc():
        subscription.status = "expired"
        db.commit()
        db.refresh(subscription)
    return subscription


def subscription_plan(db: Session, subscription: Subscription) -> Plan | None:
    if subscription.plan:
        return subscription.plan
    if subscription.plan_id:
        return db.get(Plan, subscription.plan_id)
    if subscription.plan_code:
        return db.query(Plan).filter(Plan.code == subscription.plan_code).one_or_none()
    return None


def entitlement(db: Session, user: User) -> dict:
    subscription = current_subscription(db, user)
    plan = subscription_plan(db, subscription)
    expires_at = as_aware(subscription.expires_at or subscription.ends_at)
    is_active = not user.banned and subscription.status in ACTIVE_STATUSES and (expires_at is None or expires_at >= now_utc())
    cancel_at_period_end = bool(subscription.canceled_at) and subscription.status in ACTIVE_STATUSES and expires_at is not None
    return {
        "active": is_active,
        "status": "banned" if user.banned else subscription.status,
        "plan": plan,
        "subscription": subscription,
        "expires_at": expires_at,
        "canceled_at": as_aware(subscription.canceled_at),
        "cancel_at_period_end": cancel_at_period_end,
        "account_limit": plan.account_limit if plan else 0,
        "active_session_limit": plan.active_session_limit if plan else 0,
        "support_level": plan.support_level if plan else "none",
        "features": plan_features(plan) if plan else [],
    }


def cancel_subscription(db: Session, user: User) -> Subscription:
    """Cancel the subscription. Paid plans keep access until period end; plans
    with no expiry (lifetime / open-ended) are deactivated immediately."""

    subscription = current_subscription(db, user)
    if subscription.status not in ACTIVE_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active subscription to cancel")
    now = now_utc()
    subscription.canceled_at = now
    subscription.updated_at = now
    if as_aware(subscription.expires_at or subscription.ends_at) is None:
        # Nothing to ride out — cancel takes effect now.
        subscription.status = "canceled"
    db.commit()
    db.refresh(subscription)
    write_audit(db, "billing.subscription_canceled", "subscription", subscription.id, user, {"at_period_end": subscription.status in ACTIVE_STATUSES})
    return subscription


def reactivate_subscription(db: Session, user: User) -> Subscription:
    subscription = current_subscription(db, user)
    if not subscription.canceled_at or subscription.status not in ACTIVE_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No pending cancellation to reactivate")
    subscription.canceled_at = None
    subscription.updated_at = now_utc()
    db.commit()
    db.refresh(subscription)
    write_audit(db, "billing.subscription_reactivated", "subscription", subscription.id, user)
    return subscription


def require_active_entitlement(db: Session, user: User) -> dict:
    info = entitlement(db, user)
    if not info["active"]:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Active subscription required")
    return info


def assert_account_limit(db: Session, user: User) -> None:
    info = require_active_entitlement(db, user)
    current_count = db.query(SteamAccount).filter(SteamAccount.user_id == user.id).count()
    if current_count >= info["account_limit"]:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Plan account limit reached")


def assert_active_session_limit(db: Session, user: User) -> None:
    info = require_active_entitlement(db, user)
    current_count = (
        db.query(SteamSession)
        .filter(
            SteamSession.user_id == user.id,
            SteamSession.status.in_([SessionStatus.starting.value, SessionStatus.running.value, SessionStatus.stopping.value]),
        )
        .count()
    )
    if current_count >= info["active_session_limit"]:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Plan active session limit reached")


def create_checkout(db: Session, user: User, plan_code: str) -> Payment:
    sync_default_plans(db)
    plan = get_plan(db, plan_code)
    settings = get_settings()
    if plan.code == "trial":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trial does not require checkout")
    if plan.code == "lifetime" and not settings.enable_lifetime_checkout:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lifetime is issued manually or through a dedicated checkout")

    provider = provider_for()
    idempotency_key = f"pay_{uuid4().hex}"
    checkout = provider.create_checkout(
        plan_code=plan.code,
        plan_name=plan.name,
        amount_cents=plan.price_cents,
        currency=settings.billing_currency,
        idempotency_key=idempotency_key,
        user_id=user.id,
    )
    payment = Payment(
        user_id=user.id,
        plan_id=plan.id,
        provider=checkout.provider,
        provider_payment_id=checkout.provider_payment_id,
        idempotency_key=idempotency_key,
        checkout_url=checkout.checkout_url,
        status=checkout.status,
        amount_cents=plan.price_cents,
        currency=settings.billing_currency,
        metadata_json=json.dumps({"plan_code": plan.code}),
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    write_audit(db, "billing.checkout_created", "payment", payment.id, user, {"plan_code": plan.code, "provider": payment.provider})
    return payment


def apply_subscription_from_payment(db: Session, payment: Payment) -> Subscription:
    user = db.get(User, payment.user_id)
    plan = payment.plan or db.get(Plan, payment.plan_id)
    if not user or not plan:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment is not linked to a valid user and plan")

    started_at = now_utc()
    expires_at = started_at + timedelta(days=plan.duration_days) if plan.duration_days else None
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).one_or_none()
    if not subscription:
        subscription = Subscription(user_id=user.id)
        db.add(subscription)
    subscription.plan_id = plan.id
    subscription.plan_code = plan.code
    subscription.status = "active"
    subscription.starts_at = started_at
    subscription.expires_at = expires_at
    subscription.ends_at = expires_at
    subscription.manual_override = False
    subscription.canceled_at = None
    subscription.updated_at = started_at
    db.commit()
    db.refresh(subscription)
    write_audit(db, "billing.subscription_activated", "subscription", subscription.id, user, {"payment_id": payment.id, "plan_code": plan.code})
    return subscription


def process_provider_event(db: Session, provider_name: str, raw_body: bytes, signature: str | None) -> BillingEvent:
    event = provider_for(provider_name).parse_webhook(raw_body, signature)
    existing = db.query(BillingEvent).filter(BillingEvent.idempotency_key == event.idempotency_key).one_or_none()
    if existing:
        return existing

    payment = find_payment_for_event(db, event)
    billing_event = BillingEvent(
        payment_id=payment.id if payment else None,
        provider=event.provider,
        event_type=event.event_type,
        idempotency_key=event.idempotency_key,
        verified=event.verified,
        payload_json=json.dumps(event.payload),
    )
    db.add(billing_event)
    if event.verified and payment:
        transition_payment(db, payment, event)
    try:
        db.commit()
    except IntegrityError:
        # Concurrent duplicate webhook won the unique-key race; replay is a no-op.
        db.rollback()
        return db.query(BillingEvent).filter(BillingEvent.idempotency_key == event.idempotency_key).one()
    db.refresh(billing_event)
    return billing_event


def find_payment_for_event(db: Session, event: ProviderEvent) -> Payment | None:
    if event.provider_payment_id:
        payment = db.query(Payment).filter(Payment.provider == event.provider, Payment.provider_payment_id == event.provider_payment_id).one_or_none()
        if payment:
            return payment
    metadata = event.payload.get("_metadata") or event.payload.get("metadata") or {}
    idempotency_key = metadata.get("idempotency_key") or event.payload.get("idempotency_key")
    if idempotency_key:
        return db.query(Payment).filter(Payment.provider == event.provider, Payment.idempotency_key == idempotency_key).one_or_none()
    return None


def transition_payment(db: Session, payment: Payment, event: ProviderEvent) -> None:
    next_status = event.status.lower()
    payment.updated_at = now_utc()
    if next_status in PAID_STATUSES:
        payment.status = "paid"
        db.flush()
        apply_subscription_from_payment(db, payment)
        return
    if next_status in FAILED_STATUSES:
        payment.status = "failed" if next_status in {"failed", "expired"} else "canceled"
    else:
        payment.status = "pending"


def admin_update_subscription(
    db: Session,
    actor: User,
    target: User,
    *,
    plan_code: str | None = None,
    status_value: str | None = None,
    extend_days: int | None = None,
    expires_at: datetime | None = None,
    reason: str | None = None,
) -> Subscription:
    subscription = current_subscription(db, target)
    now = now_utc()
    if plan_code:
        plan = get_plan(db, plan_code)
        subscription.plan_id = plan.id
        subscription.plan_code = plan.code
        if expires_at is None and extend_days is None:
            expires_at = now + timedelta(days=plan.duration_days) if plan.duration_days else None
    if status_value:
        subscription.status = status_value
        if status_value == "canceled":
            subscription.canceled_at = now
    if extend_days:
        base = as_aware(subscription.expires_at or subscription.ends_at)
        base = base if base and base > now else now
        expires_at = base + timedelta(days=extend_days)
        subscription.status = "active"
    if expires_at is not None or (plan_code == "lifetime"):
        subscription.expires_at = expires_at
        subscription.ends_at = expires_at
    if subscription.status in ACTIVE_STATUSES and not subscription.starts_at:
        subscription.starts_at = now
    subscription.manual_override = True
    subscription.updated_at = now
    db.commit()
    db.refresh(subscription)
    write_audit(
        db,
        "admin.subscription_update",
        "subscription",
        subscription.id,
        actor,
        {
            "target_user_id": target.id,
            "plan_code": plan_code,
            "status": status_value,
            "extend_days": extend_days,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "reason": reason,
        },
    )
    return subscription
