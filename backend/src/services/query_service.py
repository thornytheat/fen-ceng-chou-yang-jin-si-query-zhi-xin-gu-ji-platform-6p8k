"""近似查询：抽样本 → HT 估计 → 全量真值对照 → 落库。

抽样是确定性的：明细行在 seed 时写入 sample_rank（64bit 混合哈希，20 位零填充字符串），
查询按 (dataset_id, stratum_code, sample_rank) 索引取每层最小的 n_h 行（字典序 = 数值序），
因此同样输入永远得到同样样本，可复现、可复核。
"""
from __future__ import annotations

import time
from datetime import datetime

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from src.constants.enums import QueryStatus
from src.constants.limits import MAX_STRATA_FILTER
from src.models.approx_query import ApproxQuery
from src.services import audit_service, dataset_service, estimation_service, plan_service
from src.utils.errors import AppError
from src.utils.timeutil import business_date, local_iso

SAMPLE_SQL = text(
    """
    SELECT value_minor
    FROM waybills
    WHERE dataset_id = :dataset_id AND stratum_code = :code
    ORDER BY sample_rank
    LIMIT :limit
    """
)

TRUTH_SQL = text(
    """
    SELECT COALESCE(SUM(value_minor), 0) AS total, COUNT(*) AS row_count
    FROM waybills
    WHERE dataset_id = :dataset_id
    """
)


def _next_code(db: Session) -> str:
    total = db.scalar(select(func.count()).select_from(ApproxQuery)) or 0
    return f"AQ-{business_date().replace('-', '')}-{int(total) + 1:02d}"


def list_queries(db: Session, plan_id: int | None = None, limit: int = 40) -> list[ApproxQuery]:
    stmt = select(ApproxQuery).order_by(ApproxQuery.id.desc()).limit(limit)
    if plan_id:
        stmt = stmt.where(ApproxQuery.plan_id == plan_id)
    return list(db.scalars(stmt))


def get_query(db: Session, query_id: int) -> ApproxQuery:
    row = db.get(ApproxQuery, query_id)
    if row is None:
        raise AppError("NOT_FOUND", 404, detail=f"query {query_id}")
    return row


def run_query(
    db: Session,
    plan_id: int,
    strata_filter: list[str] | None,
    note: str | None,
    actor: dict,
    ip: str | None = None,
) -> ApproxQuery:
    plan = plan_service.get_plan(db, plan_id)
    if plan.status != "active":
        raise AppError("PLAN_NOT_ACTIVE", 409, detail=f"plan status={plan.status}")
    dataset = plan.dataset
    known = {s.code for s in dataset.strata}
    wanted = [code for code in (strata_filter or []) if code]
    if len(wanted) > MAX_STRATA_FILTER:
        raise AppError("VALIDATION", 422, detail="too many strata")
    if wanted and not set(wanted).issubset(known):
        raise AppError("VALIDATION", 422, detail="unknown stratum code")
    meta = dataset_service.strata_inputs(dataset, wanted or None)
    if not meta:
        raise AppError("DATASET_EMPTY", 422, detail="no strata selected")

    alloc = {row["code"]: int(row["sample_size"]) for row in (plan.allocation or [])}
    samples: dict[str, list[float]] = {}
    started = time.perf_counter()
    for row in meta:
        limit = min(int(alloc.get(row["code"], 0)), int(row["population"]))
        if limit <= 0:
            samples[row["code"]] = []
            continue
        values = db.execute(
            SAMPLE_SQL, {"dataset_id": dataset.id, "code": row["code"], "limit": limit}
        ).scalars().all()
        samples[row["code"]] = [float(v) for v in values]
    estimate = estimation_service.ht_estimate(meta, samples, float(plan.confidence_level))
    sample_ms = (time.perf_counter() - started) * 1000.0

    truth_started = time.perf_counter()
    if wanted:
        placeholders = ", ".join(f":s{i}" for i in range(len(wanted)))
        params: dict = {"dataset_id": dataset.id}
        for i, code in enumerate(wanted):
            params[f"s{i}"] = code
        truth_row = db.execute(
            text(
                "SELECT COALESCE(SUM(value_minor), 0) AS total, COUNT(*) AS row_count FROM waybills "
                f"WHERE dataset_id = :dataset_id AND stratum_code IN ({placeholders})"
            ),
            params,
        ).one()
    else:
        truth_row = db.execute(TRUTH_SQL, {"dataset_id": dataset.id}).one()
    truth_ms = (time.perf_counter() - truth_started) * 1000.0
    truth_minor = int(truth_row.total or 0)
    if truth_minor <= 0:
        raise AppError("DATASET_EMPTY", 422, detail="no detail rows for the selected scope")

    compare = estimation_service.compare_with_truth(estimate["estimate_minor"], truth_minor)
    row = ApproxQuery(
        plan_id=plan.id,
        dataset_id=dataset.id,
        code=_next_code(db),
        filter_strata=wanted,
        sample_size=int(estimate["sample_size"]),
        value_estimate_minor=int(round(estimate["estimate_minor"])),
        ci_low_minor=int(round(estimate["ci_low_minor"])),
        ci_high_minor=int(round(estimate["ci_high_minor"])),
        rel_error_pct=round(estimate["rel_error_pct"], 4),
        std_error_minor=int(round(estimate["std_error_minor"])),
        truth_total_minor=truth_minor,
        truth_rel_error_pct=round(compare["rel_error_pct"], 4),
        strata_detail=[
            {
                "code": item["code"],
                "label": item["label"],
                "population": item["population"],
                "sample_size": item["sample_size"],
                "sample_mean": round(item["sample_mean"], 4),
                "contribution": round(item["contribution"], 4),
                "ci_half": round(item["ci_half"], 4),
                "contribution_share_pct": item["contribution_share_pct"],
                "variance_share_pct": item["variance_share_pct"],
                "ci_half_pct": item["ci_half_pct"],
                "fpc": item["fpc"],
                "verified": True,
            }
            for item in estimate["strata"]
        ],
        sample_ms=round(sample_ms, 2),
        truth_ms=round(truth_ms, 2),
        full_scan_baseline_ms=int(dataset.full_scan_baseline_ms),
        status=QueryStatus.COMPLETED.value,
        run_by=actor["email"],
    )
    row.created_at = datetime.utcnow()
    db.add(row)
    db.flush()
    audit_service.record(
        db,
        actor_email=actor["email"],
        actor_role=actor["role"],
        action="query.run",
        entity="approx_query",
        entity_id=str(row.id),
        detail={
            "code": row.code,
            "dataset": dataset.code,
            "plan": plan.code,
            "sample_size": row.sample_size,
            "estimate_minor": row.value_estimate_minor,
            "rel_error_pct": float(row.rel_error_pct),
            "truth_rel_error_pct": float(row.truth_rel_error_pct),
            "sample_ms": float(row.sample_ms),
            "note": note,
        },
        ip=ip,
    )
    db.flush()
    return row


def query_out(db: Session, row: ApproxQuery) -> dict:
    dataset = row.dataset
    scale = dataset.unit_scale
    ci_half = (row.ci_high_minor - row.ci_low_minor) / 2 / scale
    baseline = max(1, row.full_scan_baseline_ms)
    sample_ms = float(row.sample_ms)
    from src.models.qc_check import QcCheck

    qc = db.scalar(select(QcCheck).where(QcCheck.query_id == row.id))
    detail = []
    for item in row.strata_detail or []:
        detail.append(
            {
                "code": item.get("code"),
                "label": item.get("label"),
                "population": int(item.get("population", 0)),
                "sample_size": int(item.get("sample_size", 0)),
                "sample_mean": round(float(item.get("sample_mean", 0)) / scale, 2),
                "contribution": round(float(item.get("contribution", 0)) / scale, 2),
                "ci_half": round(float(item.get("ci_half", 0)) / scale, 2),
                "contribution_share_pct": float(item.get("contribution_share_pct", 0)),
                "variance_share_pct": float(item.get("variance_share_pct", 0)),
                "verified": bool(item.get("verified", True)),
            }
        )
    return {
        "id": row.id,
        "code": row.code,
        "plan_id": row.plan_id,
        "plan_name": row.plan.name,
        "dataset_id": row.dataset_id,
        "dataset_code": dataset.code,
        "dataset_name": dataset.name,
        "metric_label": dataset.metric_label,
        "unit": dataset.unit,
        "filter_strata": list(row.filter_strata or []),
        "sample_size": row.sample_size,
        "value_estimate": round(row.value_estimate_minor / scale, 2),
        "ci_low": round(row.ci_low_minor / scale, 2),
        "ci_high": round(row.ci_high_minor / scale, 2),
        "ci_half": round(ci_half, 2),
        "rel_error_pct": float(row.rel_error_pct),
        "true_value": round(row.truth_total_minor / scale, 2),
        "truth_rel_error_pct": float(row.truth_rel_error_pct),
        "speed_ratio": round(baseline / sample_ms, 1) if sample_ms > 0 else 0.0,
        "sample_ms": sample_ms,
        "truth_ms": float(row.truth_ms),
        "full_scan_baseline_ms": row.full_scan_baseline_ms,
        "status": row.status,
        "run_by": row.run_by,
        "created_at": local_iso(row.created_at),
        "strata_detail": detail,
        "qc_id": qc.id if qc else None,
        "qc_verdict": qc.verdict if qc else None,
    }
