"""数值工具：风格化取整、样本统计量、正态分位数。"""
from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal

# 常用置信度的双侧 z 值（正态近似）
Z_TABLE: dict[float, float] = {0.80: 1.2816, 0.90: 1.6449, 0.95: 1.9600, 0.99: 2.5758}


def z_for(confidence: float) -> float:
    """标准正态双侧临界值；命中查表值优先，其余用 Acklam 反函数近似。

    置信水平必须落在 (0,1)：越界会得到 0 或负的 z，属于静默脏值，直接拒绝。
    """
    confidence = float(confidence)
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in (0,1)")
    key = round(confidence, 3)
    if key in Z_TABLE:
        return Z_TABLE[key]
    return _norm_ppf(0.5 + key / 2.0)


def _norm_ppf(p: float) -> float:
    """Acklam 近似，绝对误差 < 1e-9，避免引入 scipy。"""
    if p <= 0.0 or p >= 1.0:
        raise ValueError("p must be in (0,1)")
    a = [-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02,
         1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00]
    b = [-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02,
         6.680131188771972e01, -1.328068155288572e01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00,
         -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00, 3.754408661907416e00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
                ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


def round_half_up(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def largest_remainder(total: int, exact: list[float]) -> list[int]:
    """最大余数法：把 total 个样本按 exact 权重分成整数份，和恰为 total。"""
    floors = [math.floor(x) for x in exact]
    rest = total - sum(floors)
    if rest > 0:
        order = sorted(range(len(exact)), key=lambda i: (exact[i] - floors[i], exact[i]), reverse=True)
        for i in order[:rest]:
            floors[i] += 1
    elif rest < 0:
        order = sorted(range(len(exact)), key=lambda i: (exact[i] - floors[i], exact[i]))
        for i in order[: -rest]:
            floors[i] -= 1
    return floors


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def sample_variance(values: list[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    m = sum(values) / n
    return sum((v - m) ** 2 for v in values) / (n - 1)


def population_std(values: list[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    m = sum(values) / n
    return math.sqrt(sum((v - m) ** 2 for v in values) / n)


def pct(numerator: float, denominator: float, digits: int = 4) -> float:
    if not denominator:
        return 0.0
    return round(numerator / denominator * 100.0, digits)
