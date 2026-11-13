"""算法 3：线路占比合成 + 同时覆盖各线路比较的联合误差边界。

经营会要的不是每层各自的金额区间，而是「各线路在总额中的占比」，且所有占比
必须合计 100%、误差边界要能同时用于多条线路之间的比较。本模块只吃
``estimation_service.ht_estimate`` 的同一份共享样本结果，不重新抽样。

口径（与算法 2 同一批样本、同一套 HT 估计量）：

  Ŷ_h      = N_h · ȳ_h                         （层 h 的 HT 贡献）
  Ŷ        = Σ_h Ŷ_h
  p_h      = Ŷ_h / Ŷ                            （占比点估计，天然合计 100%）

  由多元 Delta 方法（线性化），Var(Ŷ_h)、Cov(Ŷ_h, Ŷ_k) 直接来自分层 HT 方差，
  令 D_h = Ŷ_h - p_h · Ŷ，则占比方差与跨层协方差为：

  Var(p_h)     = (Var(Ŷ_h) - 2·p_h·Cov(Ŷ_h, Ŷ) + p_h²·V(Ŷ)) / Ŷ²
               = (V_h - 2·p_h·V_h + p_h²·V) / Ŷ²          （Cov(Ŷ_h,Ŷ)=V_h）
  Cov(p_h,p_k) = (Cov(Ŷ_h,Ŷ_k) - p_k·V_h - p_h·V_k + p_h·p_k·V) / Ŷ²
               = -(p_k·V_h + p_h·V_k - p_h·p_k·V) / Ŷ²    （h ≠ k，跨层抽样独立）

  单线路边界（边缘 1-α）：        p_h ± z(1-α/2)·SE(p_h)
  联合边界（family-wise 1-α，
  同时覆盖全部 H 条线路的比较）：  p_h ± z(1-α/(2H))·SE(p_h)   （Bonferroni）

点估计按百分点保留 2 位小数并用最大余数法归一，展示值合计恰为 100.00%；
区间在原始精度上计算后裁剪到 [0,100]，裁剪会显式告警，绝不输出负数或 >100%。

抽样容量不足（任一层 n_h < 最小层样本，含 0/1 条无法估计方差的情形）时
``publishable=False`` 并给出拒绝原因——页面、自检、导出都必须按此口径拒绝发布。
"""
from __future__ import annotations

import math

from src.config.settings import settings
from src.utils.numbers import largest_remainder, z_for

# 占比点估计展示精度：百分点 2 位 → 用「基点」整数（1 基点 = 0.01 个百分点）做最大余数法
SHARE_DIGITS = 2
_SHARE_SCALE = 10 ** SHARE_DIGITS  # 百分比乘 100 后的整数单位，100.00% → 10000


def _bonferroni_z(confidence: float, family_size: int) -> float:
    """Bonferroni 联合分位数 z(1 - α/(2H))，family-wise 置信水平不低于 confidence。"""
    alpha = 1.0 - float(confidence)
    marginal = 1.0 - alpha / (2.0 * max(1, family_size))
    return z_for(2.0 * marginal - 1.0)  # z_for 吃双侧置信度：2m-1 = 1 - α/H


def estimate_composition(ht_result: dict, confidence: float, min_stratum_sample: int | None = None) -> dict:
    """纯函数：基于一次 ht_estimate 的共享样本结果，合成占比与联合误差边界。

    入参 ht_result 必须保留每层方差（``variance`` 字段）与总方差
    （``total_variance`` 字段），由 estimation_service 在同一批样本上给出。
    """
    strata = list(ht_result.get("strata") or [])
    if not strata:
        raise ValueError("分层估计结果为空，无法合成占比")
    if not 0.0 < float(confidence) < 1.0:
        raise ValueError("置信水平必须在 (0,1) 区间内")

    min_required = int(min_stratum_sample or settings.min_stratum_sample)
    total_estimate = float(ht_result["estimate_minor"])
    if total_estimate <= 0:
        # 总额非正时占比没有业务含义（分母为 0/负），显式拒绝而不是返回脏值
        return _rejected(
            strata,
            confidence,
            [f"总额点估计 {total_estimate:.2f} 非正，占比分母无效，无法合成线路占比"],
        )

    total_var = float(ht_result.get("total_variance", 0.0))
    family_size = len(strata)
    z_marginal = z_for(confidence)
    z_joint = _bonferroni_z(confidence, family_size)

    # --- 发布闸门：每层都要达到最小层样本（n_h=0/1 时方差本来就不可估）---
    reasons: list[str] = []
    # HT 会把 0 样本的层剔除并告警；占比口径缺层同样是硬失败，必须拒绝发布
    for warning in ht_result.get("warnings") or []:
        if "没有抽到样本" in str(warning):
            reasons.append(f"{warning}，占比口径缺层，拒绝发布占比结果")
    under = [
        f"{row.get('label', row['code'])}（{row['code']}）仅 {int(row['sample_size'])} 行"
        for row in strata
        if int(row["sample_size"]) < min_required
    ]
    if under:
        reasons.append(
            "抽样容量不足，达不到每层最小样本 "
            f"{min_required} 行："
            + "、".join(under)
            + "；占比方差不可信，拒绝发布占比结果，请提高方案样本量后重跑"
        )

    # --- 点估计：原始占比 + 最大余数法归一到合计 100.00% ---
    raw_shares = [float(row["contribution"]) / total_estimate for row in strata]
    scaled = [share * 100.0 * _SHARE_SCALE for share in raw_shares]  # 基点
    allocated = largest_remainder(100 * _SHARE_SCALE, scaled)
    point_pct = [value / _SHARE_SCALE for value in allocated]

    rows: list[dict] = []
    hard_rejected = any("拒绝发布" in item for item in reasons)
    for index, row in enumerate(strata):
        point = point_pct[index]
        raw_share = raw_shares[index]
        v_h = float(row["variance"])
        p_h = raw_share
        # Delta 方法线性化后的占比方差：
        # Cov(Ŷ_h, Ŷ) = V_h（Ŷ_h 与其他层独立），故
        # Var(p_h) = (V_h - 2·p_h·V_h + p_h²·V) / Ŷ²
        var_p = (v_h - 2.0 * p_h * v_h + p_h * p_h * total_var) / (total_estimate**2)
        var_p = max(0.0, var_p)  # 浮点兜底：理论非负
        se_p = math.sqrt(var_p)

        marginal_half = z_marginal * se_p * 100.0
        joint_half = z_joint * se_p * 100.0
        raw_low = raw_share * 100.0 - joint_half
        raw_high = raw_share * 100.0 + joint_half
        low = max(0.0, raw_low)
        high = min(100.0, raw_high)
        clipped = low != raw_low or high != raw_high

        rows.append(
            {
                "code": row["code"],
                "label": row.get("label", row["code"]),
                "sample_size": int(row["sample_size"]),
                "point_share_pct": round(point, SHARE_DIGITS),
                "point_share_raw_pct": round(raw_share * 100.0, 4),
                "std_error_pct": round(se_p * 100.0, 4),
                "marginal_half_pct": round(marginal_half, SHARE_DIGITS),
                "joint_half_pct": round(joint_half, SHARE_DIGITS),
                "joint_low_pct": round(low, SHARE_DIGITS),
                "joint_high_pct": round(high, SHARE_DIGITS),
                "interval_clipped": bool(clipped),
            }
        )

    if total_var <= 0.0:
        reasons.append("各层样本方差均为 0，联合误差边界按 0 处理（精度被高估），占比仅作参考")
    clipped_labels = [r["label"] for r in rows if r["interval_clipped"]]
    if clipped_labels:
        reasons.append("联合区间触及 0%/100% 物理边界，已裁剪到 [0,100]：" + "、".join(clipped_labels))

    if hard_rejected:
        # 硬拒绝：不发布任何占比数字，只保留拒绝原因（软提示如零方差不影响 rows 输出）
        rows = []
        point_total = 0.0
    else:
        point_total = round(sum(r["point_share_pct"] for r in rows), SHARE_DIGITS)
    return {
        "publishable": not hard_rejected,
        "confidence": float(confidence),
        "family_size": family_size,
        "z_marginal": round(z_marginal, 4),
        "z_joint": round(z_joint, 4),
        "method": "bonferroni",
        "min_stratum_sample": min_required,
        "point_total_pct": point_total,
        "rows": rows,
        "reasons": reasons,
    }


def _rejected(strata: list[dict], confidence: float, reasons: list[str]) -> dict:
    """容量/口径硬失败时的统一结构：占比与区间全部置空，只保留拒绝原因。"""
    return {
        "publishable": False,
        "confidence": float(confidence),
        "family_size": len(strata),
        "z_marginal": round(z_for(confidence), 4),
        "z_joint": round(_bonferroni_z(confidence, len(strata)), 4),
        "method": "bonferroni",
        "min_stratum_sample": int(settings.min_stratum_sample),
        "point_total_pct": 0.0,
        "rows": [],
        "reasons": reasons,
    }
