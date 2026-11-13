"""抽样方案 controller。"""
from __future__ import annotations

from sqlalchemy.orm import Session

from src.services import plan_service


def list_plans(db: Session, dataset_id: int | None = None) -> dict:
    items = [plan_service.plan_out(db, row) for row in plan_service.list_plans(db, dataset_id)]
    return {"items": items, "total": len(items)}


def get_plan(db: Session, plan_id: int) -> dict:
    return plan_service.plan_out(db, plan_service.get_plan(db, plan_id))


def create_plan(db: Session, payload, actor: dict, ip: str | None = None) -> dict:
    plan = plan_service.create_plan(db, payload, actor, ip)
    db.commit()
    return plan_service.plan_out(db, plan_service.get_plan(db, plan.id))


def approve_plan(db: Session, plan_id: int, actor: dict, ip: str | None = None) -> dict:
    plan_service.approve_plan(db, plan_id, actor, ip)
    db.commit()
    return plan_service.plan_out(db, plan_service.get_plan(db, plan_id))


def archive_plan(db: Session, plan_id: int, actor: dict, ip: str | None = None) -> dict:
    plan_service.archive_plan(db, plan_id, actor, ip)
    db.commit()
    return plan_service.plan_out(db, plan_service.get_plan(db, plan_id))
