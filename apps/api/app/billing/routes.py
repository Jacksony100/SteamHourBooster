from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.billing.schemas import CheckoutRequest, CheckoutResponse, PaymentResponse, PlanResponse, SubscriptionResponse, WebhookResponse
from app.billing.service import (
    cancel_subscription,
    create_checkout,
    entitlement,
    plan_features,
    process_provider_event,
    reactivate_subscription,
    sync_default_plans,
)
from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import current_user, require_csrf
from app.core.models import Payment, Plan, User
from app.core.rate_limit import rate_limit

router = APIRouter(prefix="/billing", tags=["billing"])


def serialize_plan(plan: Plan) -> PlanResponse:
    return PlanResponse(
        code=plan.code,
        name=plan.name,
        price_cents=plan.price_cents,
        duration_days=plan.duration_days,
        account_limit=plan.account_limit,
        active_session_limit=plan.active_session_limit,
        support_level=plan.support_level,
        features=plan_features(plan),
        active=plan.active,
    )


def serialize_subscription(info: dict) -> SubscriptionResponse:
    subscription = info["subscription"]
    plan = info["plan"]
    return SubscriptionResponse(
        plan_code=plan.code if plan else subscription.plan_code,
        status=info["status"],
        active=info["active"],
        starts_at=subscription.starts_at,
        expires_at=info["expires_at"],
        ends_at=subscription.ends_at,
        manual_override=subscription.manual_override,
        canceled_at=info.get("canceled_at"),
        cancel_at_period_end=info.get("cancel_at_period_end", False),
        account_limit=info["account_limit"],
        active_session_limit=info["active_session_limit"],
        support_level=info["support_level"],
        features=info["features"],
    )


def serialize_payment(payment: Payment) -> PaymentResponse:
    return PaymentResponse(
        id=payment.id,
        plan_code=payment.plan.code if payment.plan else "unknown",
        provider=payment.provider,
        status=payment.status,
        amount_cents=payment.amount_cents,
        currency=payment.currency,
        checkout_url=payment.checkout_url,
        idempotency_key=payment.idempotency_key,
        provider_payment_id=payment.provider_payment_id,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
    )


@router.get("/plans", response_model=list[PlanResponse])
def plans(db: Session = Depends(get_db)):
    sync_default_plans(db)
    rows = db.query(Plan).filter(Plan.active.is_(True)).order_by(Plan.price_cents.asc()).all()
    return [serialize_plan(plan) for plan in rows]


@router.get("/subscription", response_model=SubscriptionResponse)
def subscription(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return serialize_subscription(entitlement(db, user))


@router.get("/payments", response_model=list[PaymentResponse])
def payments(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(Payment).filter(Payment.user_id == user.id).order_by(Payment.id.desc()).limit(20).all()
    return [serialize_payment(payment) for payment in rows]


@router.post("/cancel", response_model=SubscriptionResponse, dependencies=[Depends(require_csrf)])
def cancel(user: User = Depends(current_user), db: Session = Depends(get_db)):
    cancel_subscription(db, user)
    return serialize_subscription(entitlement(db, user))


@router.post("/reactivate", response_model=SubscriptionResponse, dependencies=[Depends(require_csrf)])
def reactivate(user: User = Depends(current_user), db: Session = Depends(get_db)):
    reactivate_subscription(db, user)
    return serialize_subscription(entitlement(db, user))


@router.post("/checkout", response_model=CheckoutResponse, dependencies=[Depends(require_csrf), Depends(rate_limit("checkout", 10, 60 * 60))])
def checkout(payload: CheckoutRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    payment = create_checkout(db, user, payload.plan_code)
    return CheckoutResponse(
        payment_id=payment.id,
        provider=payment.provider,
        status=payment.status,
        checkout_url=payment.checkout_url,
        idempotency_key=payment.idempotency_key,
    )


@router.post(
    "/webhook/{provider_name}",
    response_model=WebhookResponse,
    dependencies=[Depends(rate_limit("webhook", 120, 60))],
)
async def webhook(
    provider_name: str,
    request: Request,
    x_cc_webhook_signature: str | None = Header(default=None, alias="X-CC-Webhook-Signature"),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    if settings.environment == "production" and provider_name == "mock":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    event = process_provider_event(db, provider_name, await request.body(), x_cc_webhook_signature)
    return WebhookResponse(
        ok=True,
        event_id=event.id,
        event_type=event.event_type,
        verified=event.verified,
        payment_id=event.payment_id,
    )
