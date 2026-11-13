"""算法 A：Neyman 分层样本分配（截断重分配 + 最小层样本）单测。

输入直接取 seed 里的真实分层参数 `scripts.demo_config`（N_h / ȳ_h / S_h），
期望值是手算/离线复算后固定下来的，全部带 `pytest.approx`。
"""
from __future__ import annotations

import random

import pytest

from scripts.demo_config import DATASETS, STRATA
from src.services.sampling_service import StratumInput, compute_allocation


def build_strata(spec: dict) -> list[StratumInput]:
    return [
        StratumInput(
            code=code,
            label=label,
            population=int(pop),
            mean_minor=float(mean_minor),
            prior_std=float(prior_std),
            min_sample=30,
        )
        for (code, label), pop, mean_minor, prior_std in zip(
            STRATA, spec["populations"], spec["means_minor"], spec["prior_std_minor"]
        )
    ]


def by_code(result: dict) -> dict[str, int]:
    return {row["code"]: row["sample_size"] for row in result["allocation"]}


# ---------------------------------------------------------------- 正常路径


def test_gmv_plan_reproduces_main_flow_contract() -> None:
    """主流程验收：GMV / 95% / 目标误差 2% → n=2742，分配 [820,690,540,410,282]。"""
    gmv = DATASETS[0]
    result = compute_allocation(build_strata(gmv), 0.95, 2.0, "neyman")

    assert result["sample_size"] == 2742
    assert [row["sample_size"] for row in result["allocation"]] == [820, 690, 540, 410, 282]
    assert result["n_raw"] == pytest.approx(2742.60, abs=0.01)
    assert result["expected_ci_pct"] == pytest.approx(1.9718, abs=1e-3)
    assert result["z"] == 1.96
    assert result["method"] == "neyman"
    assert result["total_population"] == 100_000
    # Σ N_h·ȳ_h = 18,301,700.00 元 × 100（分）
    assert result["total_value_minor"] == 1_830_170_000
    # Neyman 权重按 N_h·S_h 归一，总计为 1
    assert sum(row["neyman_weight"] for row in result["allocation"]) == pytest.approx(1.0, abs=1e-5)
    assert result["capacity_warning"] == ""


def test_ontime_plan_triggers_min_stratum_topup() -> None:
    """时效数据集：n_raw=112 但 5 层各需 ≥30，补足后总样本上浮到 165。"""
    ontime = DATASETS[1]
    result = compute_allocation(build_strata(ontime), 0.95, 3.0, "neyman")

    assert result["sample_size"] == 165
    assert by_code(result) == {"LTL_LONG": 45, "REGIONAL": 30, "URBAN": 30, "COLD_CHAIN": 30, "HEAVY": 30}
    assert result["n_raw"] == pytest.approx(112.38, abs=0.01)
    assert result["expected_ci_pct"] == pytest.approx(2.6051, abs=1e-3)
    assert result["min_applied"] is True
    assert "最小层样本" in result["capacity_warning"]


def test_cost_plan_uses_ninety_percent_z() -> None:
    """成本数据集是 90% 置信：z=1.6449，n=462。"""
    cost = DATASETS[2]
    result = compute_allocation(build_strata(cost), 0.90, 2.5, "neyman")

    assert result["z"] == 1.6449
    assert result["sample_size"] == 462
    assert [row["sample_size"] for row in result["allocation"]] == [146, 105, 76, 76, 59]
    assert result["expected_ci_pct"] == pytest.approx(2.4232, abs=1e-3)


# ---------------------------------------------------------------- 边界


def test_empty_strata_is_rejected() -> None:
    """空总体没有可分配的样本，必须显式 ValueError 而不是返回 0/NaN。"""
    with pytest.raises(ValueError, match="分层总体为空"):
        compute_allocation([], 0.95, 2.0)


def test_single_stratum_allocates_only_itself() -> None:
    """单层：n=96 全部给该层，CI 由有限总体校正给出 1.902%。"""
    result = compute_allocation([StratumInput("ONLY", "唯一层", 1000, 1000.0, 100.0)], 0.95, 2.0)

    assert result["sample_size"] == 96
    assert by_code(result) == {"ONLY": 96}
    assert result["expected_ci_pct"] == pytest.approx(1.9020, abs=1e-3)


def test_zero_prior_std_falls_back_to_proportional() -> None:
    """先验标准差全为 0 时 Neyman 权重不可用，退化为比例分配并写明原因。"""
    result = compute_allocation(
        [
            StratumInput("A", "甲", 1000, 1000.0, 0.0),
            StratumInput("B", "乙", 500, 2000.0, 0.0),
        ],
        0.95,
        2.0,
        "neyman",
    )

    assert result["method"] == "proportional"
    assert "比例分配" in result["capacity_warning"]
    assert result["sample_size"] == 70
    assert by_code(result) == {"A": 40, "B": 30}
    assert result["expected_ci_pct"] == 0.0


def test_min_sample_never_exceeds_stratum_capacity() -> None:
    """回归：层容量 10 < 最小样本 30 时，旧实现会分配 30 行（抽出比总体还多）。"""
    result = compute_allocation(
        [
            StratumInput("TINY", "小层", 10, 1000.0, 100.0),
            StratumInput("BIG", "大层", 200, 1000.0, 100.0),
        ],
        0.95,
        2.0,
    )

    alloc = {row["code"]: row["sample_size"] for row in result["allocation"]}
    assert alloc == {"TINY": 10, "BIG": 91}
    assert result["sample_size"] == 101
    assert sum(alloc.values()) == result["sample_size"]
    for row in result["allocation"]:
        assert row["sample_size"] <= row["population"]
    assert "容量小于最小样本" in result["capacity_warning"]


def test_stratum_below_min_sample_is_capped_to_capacity() -> None:
    """整层容量 10 时最多只能抽 10 行，并给出层容量不足告警。"""
    result = compute_allocation([StratumInput("A", "甲", 10, 1000.0, 100.0)], 0.95, 2.0)

    assert result["sample_size"] == 10
    assert by_code(result) == {"A": 10}
    assert result["allocation"][0]["capped"] is True
    assert "层容量不足" in result["capacity_warning"]


# ---------------------------------------------------------------- 不变量 / 性质


@pytest.mark.parametrize("spec_index", [0, 1, 2])
def test_allocation_invariants_hold_for_real_datasets(spec_index: int) -> None:
    """三份真实分层的共性：Σn_h=n、n_h≤N_h、n 不超过总体、每层不少于 min(30,N_h)。"""
    spec = DATASETS[spec_index]
    result = compute_allocation(build_strata(spec), spec["confidence_level"], spec["precision_target_pct"])

    rows = result["allocation"]
    assert sum(row["sample_size"] for row in rows) == result["sample_size"]
    assert result["sample_size"] <= result["total_population"]
    assert all(row["sample_size"] <= row["population"] for row in rows)
    assert all(row["sample_size"] >= min(30, row["population"]) for row in rows)
    assert sum(row["stratum_share_pct"] for row in rows) == pytest.approx(100.0, abs=0.05)
    assert result["expected_ci_pct"] > 0


def test_allocation_is_deterministic_and_order_independent() -> None:
    """同一输入跑两次逐字节相同；打乱层顺序后按 code 对齐结果不变。"""
    gmv = DATASETS[0]
    strata = build_strata(gmv)
    first = compute_allocation(strata, 0.95, 2.0)
    second = compute_allocation(strata, 0.95, 2.0)
    assert first == second

    shuffled = strata[:]
    random.Random(583).shuffle(shuffled)
    assert by_code(compute_allocation(shuffled, 0.95, 2.0)) == by_code(first)
    assert compute_allocation(shuffled, 0.95, 2.0)["sample_size"] == first["sample_size"]


def test_sample_size_monotonic_in_target_error_and_confidence() -> None:
    """目标误差越小 / 置信度越高 → 样本量单调不减（阈值单调性质）。"""
    gmv = DATASETS[0]
    strata = build_strata(gmv)

    by_error = [compute_allocation(strata, 0.95, err)["sample_size"] for err in (5.0, 2.0, 1.0)]
    assert by_error == [438, 2742, 10970]
    assert by_error[0] < by_error[1] < by_error[2]

    by_conf = [compute_allocation(strata, conf, 2.0)["sample_size"] for conf in (0.80, 0.90, 0.95, 0.99)]
    assert by_conf == [1172, 1931, 2742, 4736]
    assert by_conf == sorted(by_conf)


# ---------------------------------------------------------------- 异常输入


def test_unknown_allocation_method_is_rejected() -> None:
    """拼错方法名不能静默按比例分配，必须 422 前在纯函数层就报错。"""
    with pytest.raises(ValueError, match="未知分配方法"):
        compute_allocation(build_strata(DATASETS[0]), 0.95, 2.0, "ney man")


def test_invalid_parameters_are_rejected() -> None:
    """非法置信度 / 非正目标误差 / 非正层容量都必须显式报错。"""
    strata = build_strata(DATASETS[0])
    with pytest.raises(ValueError, match="置信水平"):
        compute_allocation(strata, -0.5, 2.0)
    with pytest.raises(ValueError, match="目标相对误差"):
        compute_allocation(strata, 0.95, 0.0)
    with pytest.raises(ValueError, match="容量必须为正"):
        compute_allocation([StratumInput("A", "甲", -1, 1000.0, 100.0)], 0.95, 2.0)
    with pytest.raises(ValueError, match="容量必须为正"):
        compute_allocation(
            [StratumInput("Z", "空层", 0, 1000.0, 100.0), StratumInput("B", "乙", 100, 1000.0, 100.0)],
            0.95,
            2.0,
        )
