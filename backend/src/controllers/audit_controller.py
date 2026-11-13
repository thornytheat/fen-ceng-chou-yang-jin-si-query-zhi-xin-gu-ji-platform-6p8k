"""审计日志 controller（仅 admin）。"""
from __future__ import annotations

from sqlalchemy.orm import Session

from src.services import audit_service
from src.utils.timeutil import local_iso


def list_audit(db: Session, limit: int = 40) -> dict:
    rows = audit_service.list_recent(db, limit)
    items = [
        {
            "id": row.id,
            "actor_email": row.actor_email,
            "actor_role": row.actor_role,
            "action": row.action,
            "entity": row.entity,
            "entity_id": row.entity_id,
            "layer": row.layer,
            "detail": row.detail,
            "created_at": local_iso(row.created_at),
        }
        for row in rows
    ]
    return {"items": items, "total": len(items)}
