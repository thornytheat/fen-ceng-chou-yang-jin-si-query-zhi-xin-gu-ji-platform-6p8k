"""算法 B：Horvitz–Thompson 分层估计、有限总体校正方差与 95% CI 单测。

正常路径用手算期望值与真实 seed 抽样片段（GMV 数据集每层 sample_rank 最小的 30 行，
由 seed 的确定性生成算法离线复算得到）；边界覆盖空输入、单条、零方差、样本不足。
"""
from __future__ import annotations

import pytest

from src.services.estimation_service import compare_with_truth, ht_estimate

TWO_STRATA = [
    {"code": "A", "label": "甲", "population": 100},
    {"code": "B", "label": "乙", "population": 50},
]

# seed 生成的真实抽样片段：GMV 数据集 5 层各取 sample_rank 最小的 30 行（单位：分）
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


# ---------------------------------------------------------------- 正常路径


def test_two_strata_hand_computed_estimate_and_ci() -> None:
    """手算：Ŷ=1550，V=16066.67，SE=126.754，CI 半宽=248.439，相对误差 16.0283%。"""
    result = ht_estimate(TWO_STRATA, {"A": [10.0, 12.0, 14.0], "B": [5.0, 7.0, 9.0]}, 0.95)

    assert result["estimate_minor"] == pytest.approx(1550.0)
    assert result["std_error_minor"] == pytest.approx(126.75435561221029)
    assert result["ci_half_minor"] == pytest.approx(248.43853699993215)
    assert result["ci_low_minor"] == pytest.approx(1301.5614630000678)
    assert result["ci_high_minor"] == pytest.approx(1798.4385369999322)
    assert result["rel_error_pct"] == pytest.approx(16.0283, abs=1e-4)
    assert result["sample_size"] == 6
    assert result["warnings"] == []


def test_real_seed_sample_fragment_estimates_gmv() -> None:
    """真实 seed 片段（每层 30 行）估计 18,128,880 元，与全量真值 18,301,700 差 0.9443%。"""
    result = ht_estimate(REAL_GMV_META, REAL_GMV_SAMPLES, 0.95)

    assert result["estimate_minor"] == pytest.approx(1_812_888_000.0, abs=0.5)
    assert result["sample_size"] == 150
    assert result["rel_error_pct"] == pytest.approx(7.6116, abs=1e-4)
    means = {row["code"]: row["sample_mean"] for row in result["strata"]}
    assert means["LTL_LONG"] == pytest.approx(19416.433333333334, abs=1e-6)
    assert means["REGIONAL"] == pytest.approx(12608.833333333334, abs=1e-6)
    assert means["URBAN"] == pytest.approx(11090.3, abs=1e-9)
    assert means["COLD_CHAIN"] == pytest.approx(27717.0, abs=1e-9)
    assert means["HEAVY"] == pytest.approx(38353.9, abs=1e-9)
    assert sum(row["contribution"] for row in result["strata"]) == pytest.approx(1_812_888_000.0)
    # 真实片段与全量真值（1,830,170,000 分）的相对误差应远小于 2% 精度标准
    truth = 1_830_170_000.0
    assert abs(result["estimate_minor"] - truth) / truth * 100 == pytest.approx(0.9443, abs=1e-3)


def test_higher_confidence_uses_larger_z() -> None:
    """同一批样本，99% 的 CI 半宽应为 95% 的 2.5758/1.96 = 1.3142 倍。"""
    samples = {"A": [10.0, 12.0, 14.0], "B": [5.0, 7.0, 9.0]}
    ci95 = ht_estimate(TWO_STRATA, samples, 0.95)["ci_half_minor"]
    ci99 = ht_estimate(TWO_STRATA, samples, 0.99)["ci_half_minor"]
    assert ci99 / ci95 == pytest.approx(2.5758 / 1.96, rel=1e-4)


# ---------------------------------------------------------------- 边界


def test_all_equal_values_gives_zero_variance() -> None:
    """层内全相同 → 零方差 → CI 半宽恰为 0，不是极小正数。"""
    result = ht_estimate(TWO_STRATA, {"A": [10, 10, 10], "B": [5, 5, 5]}, 0.95)

    assert result["estimate_minor"] == pytest.approx(1250.0)
    assert result["ci_half_minor"] == 0.0
    assert result["rel_error_pct"] == 0.0
    assert all(row["sample_std"] == 0.0 for row in result["strata"])


def test_single_sample_per_stratum_is_documented_degradation() -> None:
    """每层仅 1 条：样本方差不可估，CI 记为 0 且必须给出告警（不许静默当精确）。"""
    result = ht_estimate(TWO_STRATA, {"A": [10], "B": [5]}, 0.95)

    assert result["estimate_minor"] == pytest.approx(1250.0)
    assert result["ci_half_minor"] == 0.0
    assert len(result["warnings"]) == 2
    assert all("只有 1 个样本" in item for item in result["warnings"])


def test_missing_stratum_sample_is_excluded_with_warning() -> None:
    """某层没抽到样本 → 从估计中剔除并告警，估计值只含仍有样本的层。"""
    result = ht_estimate(TWO_STRATA, {"A": [10, 12]}, 0.95)

    assert result["estimate_minor"] == pytest.approx(1100.0)
    assert result["sample_size"] == 2
    assert result["warnings"] == ["层 B 没有抽到样本，已从估计中剔除"]
    assert [row["code"] for row in result["strata"]] == ["A"]


def test_all_samples_missing_returns_zero_with_warnings() -> None:
    """全部分层都没样本：估计为 0 但必须带每层告警，sample_size=0。"""
    result = ht_estimate(TWO_STRATA, {}, 0.95)

    assert result["estimate_minor"] == 0.0
    assert result["ci_half_minor"] == 0.0
    assert result["sample_size"] == 0
    assert len(result["warnings"]) == 2


def test_empty_strata_metadata_is_rejected() -> None:
    """空分层元数据没有任何可估计对象，必须显式报错。"""
    with pytest.raises(ValueError, match="分层元数据为空"):
        ht_estimate([], {}, 0.95)


def test_nonpositive_population_is_rejected() -> None:
    """层容量为 0/负会让 FPC 变成除零，必须显式拒绝。"""
    with pytest.raises(ValueError, match="容量必须为正"):
        ht_estimate([{"code": "A", "label": "甲", "population": 0}], {"A": [1.0]}, 0.95)


def test_missing_required_meta_field_is_rejected() -> None:
    """缺失 code/population 字段时不能 KeyError 式崩溃，要给出明确校验错误。"""
    with pytest.raises(ValueError, match="缺少 code/population"):
        ht_estimate([{"label": "甲", "population": 100}], {"A": [1.0]}, 0.95)
    with pytest.raises(ValueError, match="缺少 code/population"):
        ht_estimate([{"code": "A", "label": "甲"}], {"A": [1.0]}, 0.95)


# ---------------------------------------------------------------- 不变量 / 性质


def test_ci_ordering_and_share_sums() -> None:
    """CI 下界 < 点估计 < 上界；各层贡献占比与方差占比合计 100%。"""
    result = ht_estimate(REAL_GMV_META, REAL_GMV_SAMPLES, 0.95)

    assert result["ci_low_minor"] < result["estimate_minor"] < result["ci_high_minor"]
    assert 0.0 < result["rel_error_pct"] < 100.0
    assert sum(row["contribution_share_pct"] for row in result["strata"]) == pytest.approx(100.0, abs=0.01)
    assert sum(row["variance_share_pct"] for row in result["strata"]) == pytest.approx(100.0, abs=0.01)
    assert all(0.0 < row["fpc"] <= 1.0 for row in result["strata"])


def test_more_samples_shrink_ci() -> None:
    """每层样本 5 → 50 条时 CI 半宽单调收窄（含有限总体校正的精确比值 0.28494）。"""
    meta = [
        {"code": "A", "label": "甲", "population": 10000},
        {"code": "B", "label": "乙", "population": 5000},
    ]
    base = [100, 103, 97, 110, 92]
    small = {"A": base, "B": base}
    larger = {"A": base * 10, "B": base * 10}

    ci_small = ht_estimate(meta, small, 0.95)["ci_half_minor"]
    ci_large = ht_estimate(meta, larger, 0.95)["ci_half_minor"]
    assert ci_small == pytest.approx(65939.37846840838, rel=1e-9)
    assert ci_large == pytest.approx(18788.855420168627, rel=1e-9)
    assert ci_large < ci_small
    assert ci_large / ci_small == pytest.approx(0.28494134850194847, rel=1e-9)


# ---------------------------------------------------------------- 与真值对比


def test_compare_with_truth_reports_signed_and_absolute_error() -> None:
    """主流程数值：估计 18,264,926.85 vs 真值 18,301,700 → 相对误差 0.2009%。"""
    result = compare_with_truth(18264926.85, 18301700.0)

    assert result["abs_error_minor"] == pytest.approx(36773.15, abs=0.01)
    assert result["rel_error_pct"] == pytest.approx(0.2009, abs=1e-4)
    assert result["signed_pct"] == pytest.approx(-0.2009, abs=1e-4)


def test_compare_with_truth_rejects_nonpositive_truth() -> None:
    """真值为 0/负时不能静默返回 0% 误差（会假装完美命中）。"""
    with pytest.raises(ValueError, match="全量真值必须为正"):
        compare_with_truth(1000.0, 0.0)
    with pytest.raises(ValueError, match="全量真值必须为正"):
        compare_with_truth(1000.0, -1.0)
