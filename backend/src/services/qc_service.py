"""精度自检：相对误差 / CI 宽度 / 层最小样本 / 覆盖率 / 提速比 + 三角色复核链。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.constants.enums import (
    QC_VERDICT_LABELS,
    REVIEW_STATE_LABELS,
    SIGNOFF_ORDER,
    CheckCode,
    QcVerdict,
    ReviewState,
    SignoffStage,
)
from src.models.qc_check import QcCheck
from src.services import audit_service, query_service
from src.utils.errors import AppError
from src.utils.timeutil import local_iso

STAGE_LABELS = {stage.value: stage.label for stage in SignoffStage}
STAGE_ROLE = {
    SignoffStage.ANALYST.value: "analyst",
    SignoffStage.ADMIN.value: "admin",
    SignoffStage.VIEWER.value: "viewer",
}


def list_checks(db: Session, limit: int = 40) -> list[QcCheck]:
    return list(db.scalars(select(QcCheck).order_by(QcCheck.id.desc()).limit(limit)))


def get_check(db: Session, qc_id: int) -> QcCheck:
    row = db.get(QcCheck, qc_id)
    if row is None:
        raise AppError("NOT_FOUND", 404, detail=f"qc {qc_id}")
    return row


def _build_checks(db: Session, query, target_pct: float) -> tuple[list[dict], str, int, float]:
    dataset = query.dataset
    scale = dataset.unit_scale
    rel_error = float(query.truth_rel_error_pct)
    ci_pct = float(query.rel_error_pct)
    strata = query.strata_detail or []
    min_sample = min((int(item.get("sample_size", 0)) for item in strata), default=0)
    min_required = max((int(row.min_sample) for row in dataset.strata), default=30)
    population = sum(int(item.get("population", 0)) for item in strata) or dataset.row_count
    coverage = (query.sample_size / population * 100) if population else 0.0
    speed_ok = float(query.sample_ms) < float(query.full_scan_baseline_ms)

    checks = [
        {
            "code": CheckCode.REL_ERROR.value,
            "label": "相对误差（抽样点估计 vs 全量真值）",
            "actual": f"{rel_error:.4f}%",
            "threshold": f"≤ {target_pct:.2f}%",
            "ok": rel_error <= target_pct,
            "note": "误差小于精度标准即认为点估计可用",
        },
        {
            "code": CheckCode.CI_WIDTH.value,
            "label": "95% 置信区间半宽（相对）",
            "actual": f"±{ci_pct:.4f}%",
            "threshold": f"≤ {target_pct:.2f}%",
            "ok": ci_pct <= target_pct,
            "note": "方案目标误差必须覆盖置信区间，而不是只看点估计",
        },
        {
            "code": CheckCode.MIN_STRATUM.value,
            "label": "最小层样本量",
            "actual": f"{min_sample} 行",
            "threshold": f"≥ {min_required} 行",
            "ok": min_sample >= min_required,
            "note": "层内样本过少时方差估计不可靠",
        },
        {
            "code": CheckCode.COVERAGE.value,
            "label": "抽样覆盖率",
            "actual": f"{coverage:.4f}%",
            "threshold": "≥ 0.50%（参考项）",
            "ok": coverage >= 0.5,
            "note": "覆盖率只作参考，不参与达标判定",
        },
        {
            "code": CheckCode.SPEED.value,
            "label": "相对全量基线的耗时",
            "actual": f"{float(query.sample_ms):.2f} ms",
            "threshold": f"< {query.full_scan_baseline_ms} ms",
            "ok": speed_ok,
            "note": "全量基线取数据集上配置的生产扫描耗时",
        },
    ]
    blocking = [item for item in checks if item["code"] != CheckCode.COVERAGE.value]
    verdict = QcVerdict.PASS.value if all(item["ok"] for item in blocking) else QcVerdict.FAIL.value
    return checks, verdict, min_sample, coverage


def run_check(db: Session, query_id: int, target_pct: float | None, actor: dict, ip: str | None = None) -> QcCheck:
    query = query_service.get_query(db, query_id)
    dataset = query.dataset
    target = round(float(target_pct if target_pct is not None else dataset.precision_target_pct), 2)
    checks, verdict, min_sample, coverage = _build_checks(db, query, target)
    existing = db.scalar(select(QcCheck).where(QcCheck.query_id == query.id))
    if existing is None:
        existing = QcCheck(
            query_id=query.id,
            code=f"QC-{query.code}",
            target_pct=target,
            rel_error_pct=query.truth_rel_error_pct,
            ci_pct=query.rel_error_pct,
            min_stratum_sample=min_sample,
            coverage_pct=round(coverage, 4),
            checks=checks,
            verdict=verdict,
            review_state=ReviewState.PENDING.value,
            signoffs=[],
            created_by=actor["email"],
        )
        db.add(existing)
    else:
        existing.target_pct = target
        existing.rel_error_pct = query.truth_rel_error_pct
        existing.ci_pct = query.rel_error_pct
        existing.min_stratum_sample = min_sample
        existing.coverage_pct = round(coverage, 4)
        existing.checks = checks
        existing.verdict = verdict
    db.flush()
    audit_service.record(
        db,
        actor_email=actor["email"],
        actor_role=actor["role"],
        action="qc.run",
        entity="qc_check",
        entity_id=str(existing.id),
        detail={
            "query": query.code,
            "verdict": verdict,
            "rel_error_pct": float(query.truth_rel_error_pct),
            "ci_pct": float(query.rel_error_pct),
            "target_pct": target,
        },
        ip=ip,
    )
    db.flush()
    return existing


def next_stage(qc: QcCheck) -> str | None:
    approved = {entry.get("stage") for entry in (qc.signoffs or []) if entry.get("decision") == "approve"}
    for stage in SIGNOFF_ORDER:
        if stage not in approved:
            return stage
    return None


def sign_off(db: Session, qc_id: int, stage: str, decision: str, note: str | None, actor: dict, ip: str | None = None) -> QcCheck:
    qc = get_check(db, qc_id)
    stage_value = stage.value if hasattr(stage, "value") else str(stage)
    required_role = STAGE_ROLE.get(stage_value)
    if required_role is None:
        raise AppError("VALIDATION", 422, detail="unknown stage")
    if actor["role"] != required_role:
        raise AppError(
            "FORBIDDEN",
            403,
            detail=f"stage={stage_value} requires role={required_role}, actor_role={actor['role']}",
        )
    expected = next_stage(qc)
    if expected is None:
        raise AppError("QC_DUPLICATE_SIGNOFF", 409, detail="review chain already complete")
    if stage_value != expected:
        raise AppError("QC_ORDER", 409, detail=f"expected stage={expected}")
    entry = {
        "stage": stage_value,
        "stage_label": STAGE_LABELS.get(stage_value, stage_value),
        "actor_email": actor["email"],
        "actor_name": actor["email"].split("@")[0],
        "role": actor["role"],
        "decision": decision,
        "note": note,
        "at": local_iso(),
    }
    signoffs = list(qc.signoffs or [])
    signoffs.append(entry)
    qc.signoffs = signoffs
    approved = {item.get("stage") for item in signoffs if item.get("decision") == "approve"}
    qc.review_state = ReviewState.CONFIRMED.value if len(approved & set(SIGNOFF_ORDER)) == 3 else ReviewState.PENDING.value
    audit_service.record(
        db,
        actor_email=actor["email"],
        actor_role=actor["role"],
        action="qc.signoff",
        entity="qc_check",
        entity_id=str(qc.id),
        detail={"stage": stage_value, "decision": decision, "review_state": qc.review_state},
        ip=ip,
    )
    db.flush()
    return qc


def qc_out(db: Session, qc: QcCheck) -> dict:
    query = qc.query
    dataset = query.dataset
    scale = dataset.unit_scale
    return {
        "id": qc.id,
        "code": qc.code,
        "query_id": qc.query_id,
        "query_code": query.code,
        "dataset_name": dataset.name,
        "metric_label": dataset.metric_label,
        "target_pct": float(qc.target_pct),
        "rel_error_pct": float(qc.rel_error_pct),
        "ci_pct": float(qc.ci_pct),
        "min_stratum_sample": qc.min_stratum_sample,
        "coverage_pct": float(qc.coverage_pct),
        "verdict": qc.verdict,
        "verdict_label": QC_VERDICT_LABELS.get(qc.verdict, qc.verdict),
        "review_state": qc.review_state,
        "review_state_label": REVIEW_STATE_LABELS.get(qc.review_state, qc.review_state),
        "checks": list(qc.checks or []),
        "signoffs": list(qc.signoffs or []),
        "next_stage": next_stage(qc),
        "created_by": qc.created_by,
        "created_at": local_iso(qc.created_at),
        "sample_size": query.sample_size,
        "value_estimate": round(query.value_estimate_minor / scale, 2),
        "true_value": round(query.truth_total_minor / scale, 2),
        "unit": dataset.unit,
    }
