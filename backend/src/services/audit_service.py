"""审计日志写入与查询。"""
from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.models.audit import AuditLog


def record(
    db: Session,
    *,
    actor_email: str,
    actor_role: str,
    action: str,
    entity: str,
    entity_id: str | None = None,
    detail: dict | None = None,
    layer: str = "domain",
    ip: str | None = None,
    seed_key: str | None = None,
) -> AuditLog:
    row = AuditLog(
        actor_email=actor_email,
        actor_role=actor_role,
        action=action,
        entity=entity,
        entity_id=entity_id,
        detail=detail or {},
        layer=layer,
        ip=ip,
        seed_key=seed_key,
    )
    db.add(row)
    return row


def list_recent(db: Session, limit: int = 40) -> list[AuditLog]:
    return list(db.scalars(select(AuditLog).order_by(desc(AuditLog.id)).limit(limit)))
