"""解析 / 归一工具单测：z 值查表、最大余数取整、样本统计量、百分比与货币取整。

全部为纯函数，不触碰 ORM / Session / 网络。
"""
from __future__ import annotations

import pytest

from src.utils.numbers import (
    mean,
    largest_remainder,
    pct,
    population_std,
    round_half_up,
    sample_variance,
    z_for,
)


def test_z_for_table_hits_are_exact() -> None:
    """95% 场景必须命中查表值 1.96，而不是浮点近似。"""
    assert z_for(0.95) == 1.9600
    assert z_for(0.90) == pytest.approx(1.6449, abs=1e-9)
    assert z_for(0.99) == pytest.approx(2.5758, abs=1e-9)
    assert z_for(0.80) == pytest.approx(1.2816, abs=1e-9)


def test_z_for_interpolated_confidence_matches_norm_ppf() -> None:
    """非查表置信度走 Acklam 反函数：97.5% → 2.2414027。"""
    assert z_for(0.975) == pytest.approx(2.2414027264652865, rel=1e-9)
    assert z_for(0.85) == pytest.approx(1.4395314724375905, rel=1e-9)
    # 95.5% 落在查表值与近似值之间，仍应单调大于 95% 的 1.96
    assert z_for(0.955) == pytest.approx(2.0046544619731654, rel=1e-9)


@pytest.mark.parametrize("bad", [0.0, 1.0, 1.5, -0.2])
def test_z_for_rejects_out_of_range_confidence(bad: float) -> None:
    """越界置信度以前会静默返回 0 或负 z（负数 CI），现在必须显式报错。"""
    with pytest.raises(ValueError, match=r"\(0,1\)"):
        z_for(bad)


def test_largest_remainder_sums_to_total() -> None:
    """整数化和必须恰等于目标样本量 n。"""
    assert largest_remainder(10, [3.4, 3.3, 3.3]) == [4, 3, 3]
    assert largest_remainder(6, [1.0, 2.0, 3.0]) == [1, 2, 3]
    assert sum(largest_remainder(2742, [819.6, 690.4, 539.8, 410.1, 282.1])) == 2742


def test_largest_remainder_tie_break_is_stable() -> None:
    """三份完全相同的余数按索引稳定排序：多出的 2 个给前两层。"""
    assert largest_remainder(8, [2.5, 2.5, 2.5]) == [3, 3, 2]


def test_largest_remainder_handles_overflow() -> None:
    """向下取整之和超过 total 时要回退（不是只补不减）。"""
    assert largest_remainder(3, [2.6, 2.6]) == [1, 2]


def test_mean_and_variance_of_real_sample_fragment() -> None:
    """样本统计量：n<2 时方差为 0；n>=2 用 n-1 分母。"""
    assert mean([]) == 0.0
    assert mean([2, 4, 4, 4, 5, 5, 7, 9]) == 5.0
    assert sample_variance([5]) == 0.0
    assert sample_variance([2, 4, 4, 4, 5, 5, 7, 9]) == pytest.approx(4.571428571428571)
    assert population_std([10, 12, 14]) == pytest.approx(1.632993161855452)


def test_pct_and_round_half_up_are_deterministic() -> None:
    """百分比归一 + 货币四舍五入（ROUND_HALF_UP，与 MySQL DECIMAL 一致）。"""
    assert pct(1, 4) == 25.0
    assert pct(1, 3, 2) == 33.33
    assert pct(1, 0) == 0.0
    assert round_half_up(2.5) == 3
    assert round_half_up(2.49) == 2
    assert round_half_up(-2.5) == -3
