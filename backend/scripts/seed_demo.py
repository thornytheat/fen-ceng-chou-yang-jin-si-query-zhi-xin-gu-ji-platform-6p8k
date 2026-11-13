"""幂等 seed：3 数据集 / 5 层 / 12 万明细行 / 2 方案 / 3 账号。

自然键：
  users.email / datasets.code / dataset_strata(dataset_id, code) /
  waybills(dataset_id, stratum_code, sample_rank 由确定性哈希生成) /
  sample_plans.code / audit_logs.seed_key

明细行的生成是确定性的（参数化对数正态 + 64bit 混合哈希秩），
每层再按 N_h·ȳ_h 归一化，因此三个数据集的全量真值精确等于设计值：
  DS-WAYBILL-GMV       = ¥18,301,700.00
  DS-ONTIME-DURATION   = 344,640.0 小时
  DS-COST-PER-WAYBILL  = ¥927,680.00
两次 seed 的 SEED_SUMMARY 逐字一致；已有数据不会被覆盖。
"""
from __future__ import annotations

import math
from datetime import date, datetime, timedelta
from decimal import Decimal

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.dialects.mysql import insert as mysql_insert

from src.config.database import session_scope
from src.constants.enums import PlanStatus
from src.models.approx_query import ApproxQuery
from src.models.audit import AuditLog
from src.models.dataset import Dataset, DatasetStratum
from src.models.qc_check import QcCheck
from src.models.sample_plan import SamplePlan
from src.models.user import User
from src.models.waybill import Waybill
from src.services import audit_service, sampling_service
from src.utils.security import hash_password
from scripts.demo_config import (
    DATASETS,
    DEMO_PASSWORD,
    DEMO_USERS,
    GENERATOR_SALT,
    GENERATOR_SEED,
    PLANS,
    SEED_ANCHOR_DATE,
    SEED_AUDIT,
    SEED_DAYS,
    STRATA,
)

MASK = np.uint64(0xFFFFFFFFFFFFFFFF)


def ensure_users(db) -> dict[str, User]:
    users: dict[str, User] = {}
    for email, display_name, role in DEMO_USERS:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(
                email=email,
                password_hash=hash_password(DEMO_PASSWORD),
                display_name=display_name,
                role=role,
            )
            db.add(user)
            db.flush()
        users[email] = user
    return users


def ensure_dataset(db, spec: dict, dataset_index: int) -> Dataset:
    dataset = db.scalar(select(Dataset).where(Dataset.code == spec["code"]))
    if dataset is None:
        dataset = Dataset(
            code=spec["code"],
            name=spec["name"],
            scenario=spec["scenario"],
            metric_label=spec["metric_label"],
            unit=spec["unit"],
            unit_scale=spec["unit_scale"],
            row_count=0,
            source_rows=spec["source_rows"],
            strata_field=spec["strata_field"],
            value_field=spec["value_field"],
            precision_target_pct=Decimal(str(spec["precision_target_pct"])),
            confidence_level=Decimal(str(spec["confidence_level"])),
            prior_period=spec["prior_period"],
            full_scan_baseline_ms=spec["full_scan_baseline_ms"],
            truth_total_minor=0,
            note=spec["note"],
        )
        db.add(dataset)
        db.flush()
    existing = {row.code: row for row in dataset.strata}
    for index, (code, label) in enumerate(STRATA):
        if code in existing:
            continue
        db.add(
            DatasetStratum(
                dataset_id=dataset.id,
                code=code,
                label=label,
                population=int(spec["populations"][index]),
                mean_minor=int(round(spec["means_minor"][index])),
                prior_std_minor=Decimal(str(round(spec["prior_std_minor"][index], 2))),
                min_sample=30,
                sort_order=index,
            )
        )
    db.flush()
    db.refresh(dataset)
    return dataset


def _sample_rank(salt: int, stratum_index: int, row_index: np.ndarray) -> np.ndarray:
    """与查询侧 sample_rank 完全一致的 64bit 混合哈希（splitmix64 风格）。"""
    x = (
        np.uint64(salt) * np.uint64(1000003)
        + np.uint64(stratum_index * 7919 * 17)
        + row_index.astype(np.uint64)
    )
    x = x + np.uint64(0x9E3779B97F4A7C15)
    x = (x ^ (x >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
    x = (x ^ (x >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
    return x ^ (x >> np.uint64(31))


def _generate_values(spec: dict, h: int, rng: np.random.Generator) -> np.ndarray:
    """参数化对数正态，并按 N_h·均值 归一化到整数最小单位。"""
    mean_minor = float(spec["means_minor"][h])
    prior_std = float(spec["prior_std_minor"][h])
    count = int(spec["populations"][h])
    cv = spec["std_ratio"] * prior_std / mean_minor
    sigma = math.sqrt(math.log(1 + cv * cv))
    u = rng.random(12 * count).reshape(count, 12).sum(axis=1) - 6.0
    values = np.rint(mean_minor * np.exp(sigma * u - sigma * sigma / 2)).astype(np.int64)
    values = np.maximum(values, 1)
    target = int(round(count * mean_minor))
    values = np.rint(values * (target / float(values.sum()))).astype(np.int64)
    residual = target - int(values.sum())
    step = 1 if residual > 0 else -1
    for k in range(abs(residual)):
        values[k % count] += step
    return values


def ensure_waybills(db, dataset: Dataset, spec: dict, dataset_index: int) -> int:
    existing = db.scalar(select(func.count()).select_from(Waybill).where(Waybill.dataset_id == dataset.id)) or 0
    if existing:
        return 0
    anchor = date.fromisoformat(SEED_ANCHOR_DATE)
    rng = np.random.default_rng(GENERATOR_SEED + dataset_index * 101)
    salt = GENERATOR_SALT + dataset_index * 100003
    inserted = 0
    for h, (code, _label) in enumerate(STRATA):
        values = _generate_values(spec, h, rng)
        count = int(spec["populations"][h])
        idx = np.arange(count, dtype=np.uint64)
        ranks = _sample_rank(salt, h, idx)
        rows = []
        for i in range(count):
            rows.append(
                {
                    "dataset_id": dataset.id,
                    "stratum_code": code,
                    "value_minor": int(values[i]),
                    "sample_rank": f"{int(ranks[i]):020d}",
                    "biz_date": anchor - timedelta(days=int(i % SEED_DAYS)),
                }
            )
        for start in range(0, len(rows), 4000):
            db.execute(mysql_insert(Waybill), rows[start : start + 4000])
        inserted += len(rows)
        db.flush()
    db.flush()
    return inserted


def refresh_dataset_truth(db, dataset: Dataset) -> None:
    from src.services import dataset_service

    total = db.scalar(
        select(func.coalesce(func.sum(Waybill.value_minor), 0)).where(Waybill.dataset_id == dataset.id)
    )
    rows = db.scalar(select(func.count()).select_from(Waybill).where(Waybill.dataset_id == dataset.id)) or 0
    dataset.row_count = int(rows)
    dataset.truth_total_minor = int(total or 0)
    measured = dataset_service.measure_truth(db, dataset)
    dataset.row_count = int(rows)
    dataset.truth_total_minor = int(measured["truth_total_minor"])
    db.flush()


def ensure_plans(db, datasets: dict[str, Dataset], admin_email: str) -> int:
    created = 0
    for spec in PLANS:
        dataset = datasets[spec["dataset_code"]]
        plan = db.scalar(select(SamplePlan).where(SamplePlan.code == spec["code"]))
        if plan is not None:
            continue
        result = sampling_service.from_dataset(
            dataset,
            confidence=spec["confidence_level"],
            target=spec["target_error_pct"],
            method=spec["method"],
        )
        for row in result["allocation"]:
            row["capacity_warning"] = result["capacity_warning"]
        plan = SamplePlan(
            dataset_id=dataset.id,
            code=spec["code"],
            name=spec["name"],
            confidence_level=Decimal(str(spec["confidence_level"])),
            target_error_pct=Decimal(str(spec["target_error_pct"])),
            method=result["method"],
            status=spec["status"],
            sample_size=int(result["sample_size"]),
            allocation=result["allocation"],
            expected_ci_pct=Decimal(str(round(result["expected_ci_pct"], 3))),
            z_value=Decimal(str(round(result["z"], 4))),
            note=spec["note"],
            created_by=admin_email,
            approved_by=admin_email if spec["status"] == PlanStatus.ACTIVE.value else None,
            approved_at=datetime.utcnow() if spec["status"] == PlanStatus.ACTIVE.value else None,
            seed_key=spec["seed_key"],
        )
        db.add(plan)
        db.flush()
        created += 1
    return created


def ensure_seed_audit(db) -> None:
    for seed_key, email, role, action, entity, entity_id, detail in SEED_AUDIT:
        if db.scalar(select(AuditLog).where(AuditLog.seed_key == seed_key)):
            continue
        audit_service.record(
            db,
            actor_email=email,
            actor_role=role,
            action=action,
            entity=entity,
            entity_id=entity_id,
            detail=detail,
            layer="seed",
            ip="127.0.0.1",
            seed_key=seed_key,
        )
    db.flush()


def seed_all() -> str:
    with session_scope() as db:
        users = ensure_users(db)
        datasets: dict[str, Dataset] = {}
        for index, spec in enumerate(DATASETS):
            dataset = ensure_dataset(db, spec, index)
            inserted = ensure_waybills(db, dataset, spec, index)
            if inserted or not dataset.row_count:
                refresh_dataset_truth(db, dataset)
            datasets[spec["code"]] = dataset
        ensure_plans(db, datasets, admin_email="admin@sampleaqp.io")
        ensure_seed_audit(db)

        dataset_count = db.scalar(select(func.count()).select_from(Dataset)) or 0
        strata_count = db.scalar(select(func.count(func.distinct(DatasetStratum.code)))) or 0
        row_count = db.scalar(select(func.count()).select_from(Waybill)) or 0
        plan_count = (
            db.scalar(select(func.count()).select_from(SamplePlan).where(SamplePlan.seed_key.is_not(None))) or 0
        )
        user_count = db.scalar(select(func.count()).select_from(User)) or 0
        query_count = db.scalar(select(func.count()).select_from(ApproxQuery)) or 0
        qc_count = db.scalar(select(func.count()).select_from(QcCheck)) or 0

    print(f"[SEED_DEMO] detail queries={query_count} qc={qc_count} user_count={len(users)}", flush=True)
    summary = (
        f"SEED_SUMMARY brand=sampleaqp datasets={dataset_count} strata={strata_count} "
        f"rows={row_count} plans={plan_count} users={user_count}"
    )
    print(summary, flush=True)
    return summary


if __name__ == "__main__":
    seed_all()
