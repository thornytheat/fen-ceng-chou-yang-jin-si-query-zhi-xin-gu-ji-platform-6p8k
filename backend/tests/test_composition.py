"""算法 C：线路占比合成 + Bonferroni 联合误差边界单测。

输入全部来自 ``estimation_service.ht_estimate`` 的同一批样本结果（共享样本，
不二次抽样）。手算场景固定方差/占比期望值；真实 seed 片段验证性质不变量与发布闸门。
"""
from __future__ import annotations

import math

import pytest

from src.services import composition_service, estimation_service
from src.services.composition_service import estimate_composition
from src.utils.numbers import z_for

TWO_STRATA = [
    {"code": "A", "label": "甲线", "population": 100},
    {"code": "B", "label": "乙线", "population": 50},
]

REAL_GMV_META = [
    {"code": "LTL_LONG", "label": "干线长途", "population": 30000},
    {"code": "REGIONAL", "label": "区域支线", "population": 24000},
    {"code": "URBAN", "label": "同城配送", "population": 26000},
    {"code": "COLD_CHAIN", "label": "冷链专线", "population": 12000},
    {"code": "HEAVY", "label": "大件重货", "population": 8000},
]

REAL_GMV_SAMPLES = {
    "LTL_LONG": [
        11316, 19179, 19859, 11482, 13993, 21479, 7699, 13077, 13730, 13904,
        30139, 20356, 19676, 16998, 32583, 12591, 18941, 13977, 34215, 16926,
        20997, 18328, 19888, 21007, 36429, 38216, 8460, 10082, 16356, 30610,
    ],
    "REGIONAL": [
        17693, 11481, 6877, 17626, 5184, 7599, 17247, 14427, 18494, 10406,
        9764, 21760, 10949, 7827, 11517, 19403, 19381, 12308, 8310, 5518,
        15446, 9636, 15054, 6397, 4166, 5440, 16147, 6819, 34905, 10484,
    ],
    "URBAN": [
        20407, 7684, 22530, 8862, 2969, 10963, 6359, 11114, 6050, 3951,
        7250, 10530, 5023, 6019, 10854, 10663, 10408, 5679, 12659, 8195,
        8948, 4487, 24955, 6688, 8059, 35387, 17601, 6465, 7385, 24565,
    ],
    "COLD_CHAIN": [
        33677, 47982, 35947, 25284, 24851, 35891, 34038, 56238, 34175, 14821,
        21940, 31265, 19172, 25147, 22016, 14137, 19829, 23672, 15927, 30333,
        38070, 40116, 20643, 19495, 23419, 28736, 26360, 23353, 26501, 18475,
    ],
    "HEAVY": [
        24654, 25693, 33855, 45095, 27953, 40358, 25354, 18797, 39203, 47015,
        50666, 39089, 54510, 49402, 23582, 48396, 27723, 56811, 23190, 45484,
        39448, 55827, 26044, 36677, 33778, 35829, 71735, 28862, 22646, 52941,
    ],
}


def _ht(meta, samples, confidence=0.95):
    return estimation_service.ht_estimate(meta, samples, confidence)


# ---------------------------------------------------------------- 手算路径


def test_two_strata_hand_computed_shares_and_joint_bounds() -> None:
    """手算：p_A=1200/1550=0.774194；V_A=12933.33、V_B=3133.33、V=16066.67；
    Var(p_A)=(V_A-2p_A·V_A+p_A²·V)/Ŷ²=0.0010562，SE=3.2499 个百分点；
    Bonferroni H=2 → z(1-α/(2H))=z(0.9875)=2.2414，联合半宽 7.28 个百分点。"""
    ht = _ht(TWO_STRATA, {"A": [10.0, 12.0, 14.0], "B": [5.0, 7.0, 9.0]})
    result = estimate_composition(ht, 0.95, min_stratum_sample=3)

    assert result["publishable"] is True
    assert result["family_size"] == 2
    assert result["method"] == "bonferroni"
    assert result["z_joint"] == pytest.approx(2.2414, abs=2e-3)
    assert result["z_joint"] > result["z_marginal"]

    row_a = next(row for row in result["rows"] if row["code"] == "A")
    row_b = next(row for row in result["rows"] if row["code"] == "B")
    # 点估计（最大余数法归一后仍等于原始值，因为 77.42+22.58 恰为 100.00）
    assert row_a["point_share_raw_pct"] == pytest.approx(77.4194, abs=1e-4)
    assert row_a["point_share_pct"] == pytest.approx(77.42, abs=1e-4)
    assert row_b["point_share_pct"] == pytest.approx(22.58, abs=1e-4)
    # 手算方差与联合半宽（V_h 直接取 HT 层方差，保证两层用同一批共享样本）
    v_a = next(s["variance"] for s in ht["strata"] if s["code"] == "A")
    v_total = float(ht["total_variance"])
    p_a = 1200 / 1550
    var_p_a = (v_a - 2 * p_a * v_a + p_a**2 * v_total) / 1550**2
    assert var_p_a == pytest.approx(0.0010562, abs=1e-7)
    assert row_a["std_error_pct"] == pytest.approx(math.sqrt(var_p_a) * 100, abs=1e-4)
    # p_A + p_B = 1 → 两条线路占比的 SE 必须相等（同一线性组合的两端）
    assert row_b["std_error_pct"] == pytest.approx(row_a["std_error_pct"], abs=1e-4)
    expected_joint_half = result["z_joint"] * math.sqrt(var_p_a) * 100
    assert row_a["joint_half_pct"] == pytest.approx(expected_joint_half, abs=0.01)
    assert row_a["joint_half_pct"] == pytest.approx(7.28, abs=0.02)
    # 联合区间 = 点估计 ± 联合半宽（未触边界时不裁剪）
    assert row_a["joint_low_pct"] == pytest.approx(row_a["point_share_raw_pct"] - row_a["joint_half_pct"], abs=0.02)
    assert row_a["joint_high_pct"] == pytest.approx(row_a["point_share_raw_pct"] + row_a["joint_half_pct"], abs=0.02)
    assert row_a["interval_clipped"] is False
    # 边缘半宽严格小于联合半宽
    assert row_a["marginal_half_pct"] < row_a["joint_half_pct"]


def test_point_shares_sum_to_exactly_100_after_largest_remainder() -> None:
    """真实 seed 片段：展示用点占比合计必须恰为 100.00%，不能 99.99/100.01。"""
    result = estimate_composition(_ht(REAL_GMV_META, REAL_GMV_SAMPLES), 0.95)

    assert result["point_total_pct"] == pytest.approx(100.00, abs=1e-9)
    assert sum(row["point_share_pct"] for row in result["rows"]) == pytest.approx(100.00, abs=1e-9)
    # 原始（未归一）占比也合计 100%（浮点容差），归一只改变末位小数
    assert sum(row["point_share_raw_pct"] for row in result["rows"]) == pytest.approx(100.0, abs=1e-6)
    assert all(0.0 <= row["point_share_pct"] <= 100.0 for row in result["rows"])


def test_real_seed_fragment_is_publishable_with_30_per_stratum() -> None:
    """每层 30 行恰好达到发布闸门，5 条线路全部给出联合区间。"""
    result = estimate_composition(_ht(REAL_GMV_META, REAL_GMV_SAMPLES), 0.95, min_stratum_sample=30)

    assert result["publishable"] is True
    assert result["reasons"] == []
    assert len(result["rows"]) == 5
    # 真实占比量级：干线/区域/同城是大头，大件最小
    by_code = {row["code"]: row for row in result["rows"]}
    assert by_code["HEAVY"]["point_share_pct"] < by_code["LTL_LONG"]["point_share_pct"]
    for row in result["rows"]:
        assert 0.0 <= row["joint_low_pct"] <= row["point_share_pct"] <= row["joint_high_pct"] <= 100.0


def test_joint_bounds_simultaneously_cover_every_stratum() -> None:
    """联合半宽必须对所有线路同时成立：每行都用同一个 Bonferroni z，且不小于边缘半宽。"""
    result = estimate_composition(_ht(REAL_GMV_META, REAL_GMV_SAMPLES), 0.95)

    for row in result["rows"]:
        assert row["joint_half_pct"] >= row["marginal_half_pct"]
        assert (row["joint_high_pct"] - row["joint_low_pct"]) <= 100.0 + 1e-9
    expected_z = composition_service._bonferroni_z(0.95, 5)
    assert result["z_joint"] == pytest.approx(expected_z, rel=1e-9)


# ---------------------------------------------------------------- 拒绝发布


def test_stratum_below_min_sample_is_rejected_with_reasons() -> None:
    """任一层 n_h < 30（含只有 1 条、方差不可估）→ 拒绝发布，rows 清空并点名层与行数。"""
    thin = {code: values[:20] for code, values in REAL_GMV_SAMPLES.items()}
    result = estimate_composition(_ht(REAL_GMV_META, thin), 0.95, min_stratum_sample=30)

    assert result["publishable"] is False
    assert result["rows"] == []
    text = "；".join(result["reasons"])
    assert "拒绝发布" in text
    assert "20 行" in text
    # 五层全部不达标，原因里应能找到每个层代码
    for code in REAL_GMV_SAMPLES:
        assert code in text


def test_single_sample_stratum_is_rejected_not_silently_zero_variance() -> None:
    """n_h=1 时样本方差不可估（HT 侧按 0 处理是已知降级），占比侧必须直接拒绝发布。"""
    samples = {"A": [10.0], "B": [5.0, 7.0, 9.0]}
    result = estimate_composition(_ht(TWO_STRATA, samples), 0.95, min_stratum_sample=2)

    assert result["publishable"] is False
    assert any("仅 1 行" in reason for reason in result["reasons"])


def test_missing_stratum_sample_is_rejected() -> None:
    """某层 0 样本被 HT 剔除后，剩余层仍可估金额，但占比口径缺层 → 拒绝发布。"""
    ht = _ht(TWO_STRATA, {"A": [10.0, 12.0, 14.0]}, 0.95)
    result = estimate_composition(ht, 0.95, min_stratum_sample=2)

    assert result["publishable"] is False
    assert any("占比口径缺层" in reason for reason in result["reasons"])


def test_nonpositive_total_estimate_is_rejected() -> None:
    """总额点估计非正 → 占比分母无效，显式拒绝而不是除零或返回脏占比。"""
    fake_ht = {
        "estimate_minor": 0.0,
        "total_variance": 0.0,
        "strata": [
            {"code": "A", "label": "甲", "sample_size": 30, "contribution": 0.0, "variance": 1.0},
        ],
    }
    result = estimate_composition(fake_ht, 0.95)

    assert result["publishable"] is False
    assert result["rows"] == []
    assert any("分母无效" in reason for reason in result["reasons"])


# ---------------------------------------------------------------- 边界与裁剪


def test_intervals_are_clipped_to_physical_bounds_and_flagged() -> None:
    """小占比 + 大方差时联合下界本应为负：必须裁剪到 0 并显式标注，绝不输出负数。

    直接构造 HT 结果：甲线占比 2%，但 SE 达 8 个百分点，联合半宽必然越过 0。
    """
    fake_ht = {
        "estimate_minor": 1_000_000.0,
        "total_variance": 40_000.0**2,
        "warnings": [],
        "strata": [
            {"code": "A", "label": "甲线", "sample_size": 30, "contribution": 20_000.0, "variance": 80_000.0**2},
            {"code": "B", "label": "乙线", "sample_size": 30, "contribution": 980_000.0, "variance": 100.0**2},
        ],
    }
    result = estimate_composition(fake_ht, 0.95)

    assert result["publishable"] is True
    row_a = next(row for row in result["rows"] if row["code"] == "A")
    assert row_a["point_share_pct"] == pytest.approx(2.0, abs=0.01)
    assert row_a["joint_low_pct"] == 0.0
    assert row_a["interval_clipped"] is True
    assert any("裁剪" in reason for reason in result["reasons"])
    for row in result["rows"]:
        assert row["joint_low_pct"] >= 0.0 and row["joint_high_pct"] <= 100.0


def test_zero_variance_gives_zero_bounds_with_warning_but_still_publishable() -> None:
    """层内全相同 → 占比方差为 0 → 区间半宽为 0，给口径提示但不触发拒绝发布。"""
    result = estimate_composition(
        _ht(TWO_STRATA, {"A": [10, 10, 10, 10], "B": [5, 5, 5, 5]}, 0.95), 0.95, min_stratum_sample=2
    )

    assert result["publishable"] is True
    assert all(row["joint_half_pct"] == 0.0 for row in result["rows"])
    assert all(row["joint_low_pct"] == row["joint_high_pct"] for row in result["rows"])
    assert any("方差均为 0" in reason for reason in result["reasons"])
    assert sum(row["point_share_pct"] for row in result["rows"]) == pytest.approx(100.0, abs=1e-9)


def test_empty_ht_result_is_rejected() -> None:
    """空分层结果没有可合成对象，直接 ValueError 而不是返回空壳成功响应。"""
    with pytest.raises(ValueError, match="分层估计结果为空"):
        estimate_composition({"strata": [], "estimate_minor": 0.0}, 0.95)


def test_bonferroni_z_grows_with_family_size() -> None:
    """线路越多，同时覆盖所需的分位数越大：H=2 < H=5 < H=10，且都大于边缘 z。"""
    z_edge = z_for(0.95)
    z2 = composition_service._bonferroni_z(0.95, 2)
    z5 = composition_service._bonferroni_z(0.95, 5)
    z10 = composition_service._bonferroni_z(0.95, 10)

    assert z_edge < z2 < z5 < z10
    # H=1 时联合边界退化为普通双侧边缘区间
    assert composition_service._bonferroni_z(0.95, 1) == pytest.approx(z_edge, rel=1e-9)


def test_higher_confidence_widens_joint_bounds() -> None:
    """同一批样本，99% 置信的联合半宽必须大于 95%，且点占比完全不变（同一份共享样本）。"""
    ht = _ht(REAL_GMV_META, REAL_GMV_SAMPLES)
    r95 = estimate_composition(ht, 0.95)
    r99 = estimate_composition(ht, 0.99)

    for a, b in zip(r95["rows"], r99["rows"]):
        assert a["code"] == b["code"]
        assert a["point_share_pct"] == b["point_share_pct"]
        assert b["joint_half_pct"] > a["joint_half_pct"]
