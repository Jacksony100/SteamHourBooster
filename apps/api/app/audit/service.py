import json

from sqlalchemy.orm import Session

from app.core.models import AuditLog, User


def write_audit(
    db: Session,
    action: str,
    target_type: str,
    target_id: str | int,
    actor: User | None = None,
    metadata: dict | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_user_id=actor.id if actor else None,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        metadata_json=json.dumps(metadata or {}),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
