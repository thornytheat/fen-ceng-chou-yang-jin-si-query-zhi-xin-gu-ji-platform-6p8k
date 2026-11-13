"""抽样方案：创建时即用算法 1 算出样本量与每层分配。"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.constants.enums import PLAN_STATUS_LABELS, AllocationMethod, PlanStatus
from src.models.sample_plan import SamplePlan
from src.services import audit_service, dataset_service, sampling_service
from src.utils.errors import AppError
from src.utils.timeutil import local_iso


def list_plans(db: Session, dataset_id: int | None = None) -> list[SamplePlan]:
    stmt = select(SamplePlan).order_by(SamplePlan.id.desc())
    if dataset_id:
        stmt = stmt.where(SamplePlan.dataset_id == dataset_id)
    return list(db.scalars(stmt))


def get_plan(db: Session, plan_id: int) -> SamplePlan:
    plan = db.get(SamplePlan, plan_id)
    if plan is None:
        raise AppError("NOT_FOUND", 404, detail=f"plan {plan_id}")
    return plan


def _next_code(db: Session) -> str:
    total = db.scalar(select(func.count()).select_from(SamplePlan)) or 0
    return f"PLAN-{int(total) + 1:03d}"


def plan_out(db: Session, plan: SamplePlan) -> dict:
    dataset = plan.dataset
    from src.models.approx_query import ApproxQuery

    query_count = db.scalar(select(func.count()).select_from(ApproxQuery).where(ApproxQuery.plan_id == plan.id)) or 0
    allocation = list(plan.allocation or [])
    return {
        "id": plan.id,
        "code": plan.code,
        "dataset_id": plan.dataset_id,
        "dataset_code": dataset.code,
        "dataset_name": dataset.name,
        "metric_label": dataset.metric_label,
        "name": plan.name,
        "confidence_level": float(plan.confidence_level),
        "target_error_pct": float(plan.target_error_pct),
        "method": plan.method,
        "method_label": AllocationMethod(plan.method).label,
        "status": plan.status,
        "status_label": PLAN_STATUS_LABELS.get(plan.status, plan.status),
        "sample_size": plan.sample_size,
        "expected_ci_pct": float(plan.expected_ci_pct),
        "z_value": float(plan.z_value),
        "allocation": [
            {
                "code": row.get("code"),
                "label": row.get("label"),
                "population": row.get("population", 0),
                "prior_std": round(float(row.get("prior_std", 0)), 2),
                "neyman_weight": float(row.get("neyman_weight", 0)),
                "sample_size": int(row.get("sample_size", 0)),
                "stratum_share_pct": float(row.get("stratum_share_pct", 0)),
                "expected_ci_contribution_pct": float(row.get("expected_ci_contribution_pct", 0)),
            }
            for row in allocation
        ],
        "note": plan.note,
        "created_by": plan.created_by,
        "approved_by": plan.approved_by,
        "approved_at": local_iso(plan.approved_at) if plan.approved_at else None,
        "query_count": int(query_count),
        "created_at": local_iso(plan.created_at),
        "capacity_warning": (plan.allocation or [{}])[0].get("capacity_warning") if allocation else None,
    }


def create_plan(db: Session, payload, actor: dict, ip: str | None = None) -> SamplePlan:
    dataset = dataset_service.get_dataset(db, payload.dataset_id)
    if not dataset.strata:
        raise AppError("DATASET_EMPTY", 422, detail="dataset has no strata")
    result = sampling_service.from_dataset(
        dataset,
        confidence=float(payload.confidence_level),
        target=float(payload.target_error_pct),
        method=payload.method.value if hasattr(payload.method, "value") else str(payload.method),
    )
    for row in result["allocation"]:
        row["capacity_warning"] = result["capacity_warning"]
    plan = SamplePlan(
        dataset_id=dataset.id,
        code=_next_code(db),
        name=payload.name.strip(),
        confidence_level=Decimal(str(round(float(payload.confidence_level), 3))),
        target_error_pct=Decimal(str(round(float(payload.target_error_pct), 2))),
        method=result["method"],
        status=PlanStatus.DRAFT.value,
        sample_size=int(result["sample_size"]),
        allocation=[{k: v for k, v in row.items()} for row in result["allocation"]],
        expected_ci_pct=Decimal(str(round(result["expected_ci_pct"], 3))),
        z_value=Decimal(str(round(result["z"], 4))),
        note=payload.note,
        created_by=actor["email"],
    )
    db.add(plan)
    db.flush()
    audit_service.record(
        db,
        actor_email=actor["email"],
        actor_role=actor["role"],
        action="plan.create",
        entity="sample_plan",
        entity_id=str(plan.id),
        detail={
            "code": plan.code,
            "dataset": dataset.code,
            "sample_size": plan.sample_size,
            "expected_ci_pct": float(plan.expected_ci_pct),
            "method": plan.method,
        },
        ip=ip,
    )
    db.flush()
    return plan


def approve_plan(db: Session, plan_id: int, actor: dict, ip: str | None = None) -> SamplePlan:
    plan = get_plan(db, plan_id)
    if plan.status == PlanStatus.ARCHIVED.value:
        raise AppError("PLAN_NOT_ACTIVE", 409, detail="archived plan cannot be approved")
    plan.status = PlanStatus.ACTIVE.value
    plan.approved_by = actor["email"]
    plan.approved_at = datetime.utcnow()
    audit_service.record(
        db,
        actor_email=actor["email"],
        actor_role=actor["role"],
        action="plan.approve",
        entity="sample_plan",
        entity_id=str(plan.id),
        detail={"code": plan.code, "sample_size": plan.sample_size},
        ip=ip,
    )
    db.flush()
    return plan


def archive_plan(db: Session, plan_id: int, actor: dict, ip: str | None = None) -> SamplePlan:
    plan = get_plan(db, plan_id)
    plan.status = PlanStatus.ARCHIVED.value
    audit_service.record(
        db,
        actor_email=actor["email"],
        actor_role=actor["role"],
        action="plan.archive",
        entity="sample_plan",
        entity_id=str(plan.id),
        detail={"code": plan.code},
        ip=ip,
    )
    db.flush()
    return plan
