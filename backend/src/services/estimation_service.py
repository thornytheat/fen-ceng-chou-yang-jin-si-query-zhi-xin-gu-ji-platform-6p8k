"""算法 2：Horvitz–Thompson 分层估计与 95% 置信区间（含有限总体校正）。

  Ŷ        = Σ_h N_h · ȳ_h
  V(Ŷ)     = Σ_h N_h² · (1 - n_h/N_h) · s_h² / n_h
  SE       = sqrt(V)
  CI       = Ŷ ± z·SE
  相对误差 = z·SE / Ŷ                （半宽 / 点估计）
"""
from __future__ import annotations

import math

from src.utils.numbers import mean, sample_variance, z_for


def ht_estimate(
    strata_meta: list[dict],
    samples: dict[str, list[float]],
    confidence: float = 0.95,
) -> dict:
    if not strata_meta:
        raise ValueError("分层元数据为空，无法估计")
    if not 0.0 < float(confidence) < 1.0:
        raise ValueError("置信水平必须在 (0,1) 区间内")
    for meta in strata_meta:
        if meta.get("code") is None or meta.get("population") is None:
            raise ValueError("分层元数据缺少 code/population 字段")
        if int(meta["population"]) <= 0:
            raise ValueError(f"层 {meta['code']} 容量必须为正")
    z = z_for(confidence)
    total_estimate = 0.0
    total_var = 0.0
    rows: list[dict] = []
    warnings: list[str] = []

    for meta in strata_meta:
        code = meta["code"]
        values = [float(v) for v in samples.get(code, [])]
        n_h = len(values)
        population = int(meta["population"])
        if n_h == 0:
            warnings.append(f"层 {code} 没有抽到样本，已从估计中剔除")
            continue
        if n_h == 1:
            warnings.append(f"层 {code} 只有 1 个样本，方差不可估计，CI 半宽按 0 处理（精度被高估）")
        sample_mean = mean(values)
        s2 = sample_variance(values)
        contribution = population * sample_mean
        fpc = max(0.0, 1.0 - n_h / population)
        var_h = population**2 * fpc * s2 / n_h
        ci_half_h = z * math.sqrt(var_h)
        rows.append(
            {
                "code": code,
                "label": meta.get("label", code),
                "population": population,
                "sample_size": n_h,
                "sample_mean": sample_mean,
                "sample_std": math.sqrt(s2),
                "contribution": contribution,
                "std_error": math.sqrt(var_h),
                "ci_half": ci_half_h,
                "variance": var_h,
                "fpc": round(fpc, 6),
            }
        )
        total_estimate += contribution
        total_var += var_h

    std_error = math.sqrt(total_var)
    ci_half = z * std_error
    ci_low = total_estimate - ci_half
    ci_high = total_estimate + ci_half
    rel_error = (ci_half / total_estimate * 100) if total_estimate else 0.0

    for row in rows:
        row["contribution_share_pct"] = round(row["contribution"] / total_estimate * 100, 4) if total_estimate else 0.0
        row["variance_share_pct"] = round(row["variance"] / total_var * 100, 4) if total_var else 0.0
        row["ci_half_pct"] = round(row["ci_half"] / total_estimate * 100, 4) if total_estimate else 0.0
        # variance 保留给算法 3（占比合成的 Delta 方差），不进落库 JSON

    return {
        "z": round(z, 4),
        "estimate_minor": total_estimate,
        "std_error_minor": std_error,
        "ci_low_minor": ci_low,
        "ci_high_minor": ci_high,
        "ci_half_minor": ci_half,
        "rel_error_pct": round(rel_error, 4),
        "sample_size": sum(r["sample_size"] for r in rows),
        "total_variance": total_var,
        "strata": rows,
        "warnings": warnings,
    }


def compare_with_truth(estimate_minor: float, truth_minor: float) -> dict:
    if truth_minor <= 0:
        raise ValueError("全量真值必须为正，无法计算相对误差")
    signed = (estimate_minor - truth_minor) / truth_minor * 100
    return {
        "abs_error_minor": abs(estimate_minor - truth_minor),
        "rel_error_pct": round(abs(signed), 4),
        "signed_pct": round(signed, 4),
    }
