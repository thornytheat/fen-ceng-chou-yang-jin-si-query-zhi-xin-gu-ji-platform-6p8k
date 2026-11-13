"""算法 1：分层抽样样本量计算与 Neyman / 比例分配。

口径（全部按最小货币单位整数计算，避免浮点累计误差）：

  T            = Σ N_h · S_h                       （Neyman 口径的层波动总量）
  n_raw        = (z · T / (e · Y))²                （目标相对误差 e，Y = Σ N_h · ȳ_h）
  n            = max(min_total, int(n_raw))         （向下取整，避免样本量虚高）
  n_h          = n · N_h·S_h / Σ N_h·S_h            （Neyman）
  n_h          = n · N_h / N                        （比例分配；S_h 缺失时自动退化）

约束：
  * 每层最小样本 min_sample（默认 30），不足则补足，总样本随之上浮；
  * n_h 超过层容量 N_h 时截断，并把缺口按未封顶层的权重二次分配；
  * 最大余数法取整，保证 Σ n_h == n。
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal

from src.config.settings import settings
from src.constants.enums import AllocationMethod
from src.utils.numbers import largest_remainder, z_for


@dataclass
class StratumInput:
    code: str
    label: str
    population: int
    mean_minor: float
    prior_std: float
    min_sample: int = 30


VALID_METHODS = (AllocationMethod.NEYMAN.value, AllocationMethod.PROPORTIONAL.value)


def compute_allocation(
    strata: list[StratumInput],
    confidence: float,
    target_error_pct: float,
    method: str = AllocationMethod.NEYMAN.value,
    min_total: int | None = None,
) -> dict:
    """纯函数：只吃分层参数，不依赖 DB/Session。

    非法参数一律显式 ValueError，避免产生负数 CI、超层容量样本等脏值。
    """
    if method not in VALID_METHODS:
        raise ValueError(f"未知分配方法: {method}")
    confidence = float(confidence)
    target_error_pct = float(target_error_pct)
    if not 0.0 < confidence < 1.0:
        raise ValueError("置信水平必须在 (0,1) 区间内")
    if not 0.0 < target_error_pct < 100.0:
        raise ValueError("目标相对误差必须在 (0,100) 区间内")
    for s in strata:
        if int(s.population) <= 0:
            raise ValueError(f"层 {s.code} 容量必须为正")
    z = z_for(confidence)
    e = float(target_error_pct) / 100.0
    total_population = sum(s.population for s in strata)
    total_value = sum(s.population * s.mean_minor for s in strata)
    if total_population <= 0 or total_value <= 0:
        raise ValueError("分层总体为空")

    fallback = ""
    stds = [max(0.0, float(s.prior_std)) for s in strata]
    use_neyman = method == AllocationMethod.NEYMAN.value and all(v > 0 for v in stds)
    if method == AllocationMethod.NEYMAN.value and not use_neyman:
        fallback = "存在层的先验标准差为 0，Neyman 权重不可用，本次退化为比例分配。"
        use_neyman = False

    if use_neyman:
        weights_raw = [s.population * stds[i] for i, s in enumerate(strata)]
        t_like = sum(weights_raw)
        n_raw = (z * t_like / (e * total_value)) ** 2
    else:
        # 比例分配下方差 ≈ (N/n)·Σ N_h S_h²，故等效 T = sqrt(N·Σ N_h S_h²)
        var_part = sum(s.population * stds[i] ** 2 for i, s in enumerate(strata))
        if var_part <= 0:
            n_raw = float(min_total or settings.min_total_sample)
        else:
            n_raw = z * z * total_population * var_part / ((e * total_value) ** 2)
        weights_raw = [float(s.population) for s in strata]
        t_like = float(total_population)

    floor_total = max(min_total or settings.min_total_sample, settings.min_total_sample)
    n = max(floor_total, int(n_raw))
    n = min(n, total_population)

    weights = [w / t_like for w in weights_raw] if t_like else [1 / len(strata)] * len(strata)

    # --- 初分配 ---
    capped: list[bool] = [False] * len(strata)
    n_h = [0] * len(strata)
    remaining = n
    active = list(range(len(strata)))
    for _ in range(len(strata) + 1):
        weight_sum = sum(weights[i] for i in active) or 1.0
        for i in active:
            n_h[i] = remaining * weights[i] / weight_sum
        capped_this_round = [i for i in active if n_h[i] >= strata[i].population]
        if not capped_this_round:
            break
        for i in capped_this_round:
            capped[i] = True
            n_h[i] = strata[i].population
            remaining -= strata[i].population
            active.remove(i)
        if not active:
            break
    n_h = largest_remainder(n, n_h)
    # --- 最小层样本（不得超过层容量，否则会抽出多于总体的样本）---
    min_applied = False
    capacity_limited: list[str] = []
    for i, s in enumerate(strata):
        need = max(s.min_sample, settings.min_stratum_sample)
        if n_h[i] < need and not capped[i]:
            target = min(need, s.population)
            if target > n_h[i]:
                n_h[i] = target
                min_applied = True
                if s.population < need:
                    capacity_limited.append(s.code)
    total_sample = min(sum(n_h), total_population)

    # --- 预期 CI（用先验 S_h 与有限总体校正）---
    var_total = 0.0
    rows = []
    for i, s in enumerate(strata):
        nh = n_h[i]
        divisor = max(1, nh)
        fpc = max(0.0, 1.0 - nh / s.population) if nh > 0 else 0.0
        var_h = s.population**2 * fpc * stds[i] ** 2 / divisor
        var_total += var_h
        ci_h = z * math.sqrt(var_h) / total_value * 100 if var_h > 0 else 0.0
        rows.append(
            {
                "code": s.code,
                "label": s.label,
                "population": s.population,
                "prior_std": round(stds[i], 2),
                "neyman_weight": round(weights[i], 6),
                "sample_size": nh,
                "stratum_share_pct": round(s.population / total_population * 100, 2),
                "expected_ci_contribution_pct": round(ci_h, 4),
                "min_sample": max(s.min_sample, settings.min_stratum_sample),
                "capped": capped[i],
            }
        )

    expected_ci = z * math.sqrt(var_total) / total_value * 100 if var_total > 0 else 0.0
    warning = fallback
    capped_codes = [strata[i].code for i, flag in enumerate(capped) if flag]
    if capped_codes:
        warning = (warning + " " if warning else "") + (
            "层容量不足：" + "、".join(capped_codes) + " 已截断到层容量，缺口按其余层权重重分配。"
        )
    if min_applied:
        warning = (warning + " " if warning else "") + "已触发最小层样本 30 的补足，总样本上浮。"
    if capacity_limited:
        warning = (warning + " " if warning else "") + (
            "层 " + "、".join(capacity_limited) + " 的容量小于最小样本，已按层容量全抽。"
        )

    return {
        "z": round(z, 4),
        "method": AllocationMethod.NEYMAN.value if use_neyman else AllocationMethod.PROPORTIONAL.value,
        "target_error_pct": float(target_error_pct),
        "confidence": float(confidence),
        "sample_size": total_sample,
        "n_raw": round(n_raw, 2),
        "expected_ci_pct": round(expected_ci, 4),
        "total_population": total_population,
        "total_value_minor": int(round(total_value)),
        "allocation": rows,
        "capacity_warning": warning,
        "min_applied": min_applied,
    }


def from_dataset(dataset, confidence: float | None = None, target: float | None = None, method: str = "neyman") -> dict:
    """把 Dataset + DatasetStratum ORM 对象转成算法入参。"""
    strata = [
        StratumInput(
            code=s.code,
            label=s.label,
            population=int(s.population),
            mean_minor=float(s.mean_minor),
            prior_std=float(Decimal(s.prior_std_minor)),
            min_sample=int(s.min_sample),
        )
        for s in dataset.strata
    ]
    conf = float(confidence if confidence is not None else dataset.confidence_level)
    err = float(target if target is not None else dataset.precision_target_pct)
    return compute_allocation(strata, conf, err, method)
