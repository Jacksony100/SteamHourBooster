from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.admin import service
from app.admin.schemas import (
    AdminAuditResponse,
    AdminForceLogoutRequest,
    AdminForceLogoutResponse,
    AdminOverviewResponse,
    AdminPaymentResponse,
    AdminSubscriptionUpdate,
    AdminUserDetailResponse,
    AdminUserFilter,
    AdminUserListResponse,
    AdminUserResponse,
    AdminUserUpdate,
)
from app.billing.routes import serialize_subscription
from app.billing.schemas import SubscriptionResponse
from app.billing.service import entitlement
from app.core.database import get_db
from app.core.deps import admin_user, require_csrf
from app.core.models import User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/overview", response_model=AdminOverviewResponse)
def overview(actor: User = Depends(admin_user), db: Session = Depends(get_db)):
    return service.admin_overview(db)


@router.get("/users", response_model=AdminUserListResponse)
def users(
    query: str = "",
    filter: AdminUserFilter = "all",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    actor: User = Depends(admin_user),
    db: Session = Depends(get_db),
):
    return service.list_admin_users(db, query=query, user_filter=filter, page=page, page_size=page_size)


@router.get("/users/{user_id}", response_model=AdminUserDetailResponse)
def user_detail(user_id: int, actor: User = Depends(admin_user), db: Session = Depends(get_db)):
    return service.user_detail(db, user_id)


@router.patch("/users/{user_id}", response_model=AdminUserResponse, dependencies=[Depends(require_csrf)])
def update_user(user_id: int, payload: AdminUserUpdate, actor: User = Depends(admin_user), db: Session = Depends(get_db)):
    return service.update_user(db, actor=actor, user_id=user_id, payload=payload)


@router.patch("/users/{user_id}/subscription", response_model=SubscriptionResponse, dependencies=[Depends(require_csrf)])
def update_subscription(
    user_id: int,
    payload: AdminSubscriptionUpdate,
    actor: User = Depends(admin_user),
    db: Session = Depends(get_db),
):
    service.update_subscription(db, actor=actor, user_id=user_id, payload=payload)
    user = service.get_user_or_404(db, user_id)
    return serialize_subscription(entitlement(db, user))


@router.post("/users/{user_id}/force-logout-sessions", response_model=AdminForceLogoutResponse, dependencies=[Depends(require_csrf)])
def force_logout_sessions(
    user_id: int,
    payload: AdminForceLogoutRequest,
    actor: User = Depends(admin_user),
    db: Session = Depends(get_db),
):
    return service.force_logout_sessions(db, actor=actor, user_id=user_id, reason=payload.reason)


@router.get("/audit", response_model=list[AdminAuditResponse])
def audit(
    query: str = "",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    actor: User = Depends(admin_user),
    db: Session = Depends(get_db),
):
    return service.list_audit(db, query=query, page=page, page_size=page_size)


@router.get("/payments", response_model=list[AdminPaymentResponse])
def payments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    actor: User = Depends(admin_user),
    db: Session = Depends(get_db),
):
    return service.list_payments(db, page=page, page_size=page_size)


@router.get("/subscription-changes", response_model=list[AdminAuditResponse])
def subscription_changes(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    actor: User = Depends(admin_user),
    db: Session = Depends(get_db),
):
    return service.list_subscription_changes(db, page=page, page_size=page_size)
