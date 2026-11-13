"""导出「近似估算说明」Markdown：给经营会用的最终交付物。"""
from __future__ import annotations

from src.constants.enums import QC_VERDICT_LABELS
from src.services.dataset_service import to_unit
from src.utils.timeutil import local_iso


def _money(value_minor: float, scale: int, unit: str) -> str:
    amount = value_minor / (scale or 1)
    if unit == "元":
        return f"¥{amount:,.2f}"
    return f"{amount:.1f} {unit}"


def build_estimate_markdown(query, qc=None) -> tuple[str, str]:
    dataset = query.dataset
    plan = query.plan
    scale = dataset.unit_scale
    unit = dataset.unit
    ci_half = (query.ci_high_minor - query.ci_low_minor) / 2
    coverage = (
        query.sample_size / sum(int(item.get("population", 0)) for item in (query.strata_detail or [])) * 100
        if query.strata_detail
        else 0.0
    )
    speed = query.full_scan_baseline_ms / float(query.sample_ms) if float(query.sample_ms) > 0 else 0.0

    lines: list[str] = []
    lines.append(f"# 近似估算说明 · {query.code}")
    lines.append("")
    lines.append("远舟物流 · 数据分析组 | 分层抽样近似查询（AQP）台 sampleaqp")
    lines.append("")
    lines.append("## 1. 本次估算的范围")
    lines.append("")
    lines.append("| 项目 | 内容 |")
    lines.append("| --- | --- |")
    lines.append(f"| 数据集 | `{dataset.code}` · {dataset.name} |")
    lines.append(f"| 指标 | {dataset.metric_label}（{unit}） |")
    lines.append(f"| 全量规模 | {dataset.row_count:,} 行（生产表约 {dataset.source_rows:,} 行） |")
    lines.append(f"| 分层字段 | `{dataset.strata_field}` · {len(dataset.strata)} 层 |")
    lines.append("| 查询范围 | " + ("、".join(query.filter_strata) if query.filter_strata else "全部层") + " |")
    lines.append(f"| 方案 | `{plan.code}` · {plan.name} |")
    lines.append(
        f"| 抽样口径 | {plan.method} · 置信 {float(plan.confidence_level):.0%} · 目标误差 {float(plan.target_error_pct):.2f}% · 样本 {plan.sample_size:,} 行 |"
    )
    lines.append(f"| 执行人 | {query.run_by} |")
    lines.append(f"| 执行时间 | {local_iso(query.created_at)} |")
    lines.append("")
    lines.append("## 2. 点估计与置信区间")
    lines.append("")
    lines.append("| 项目 | 数值 |")
    lines.append("| --- | --- |")
    lines.append(f"| Horvitz–Thompson 点估计 | {_money(query.value_estimate_minor, scale, unit)} |")
    lines.append(
        f"| 95% 置信区间 | {_money(query.ci_low_minor, scale, unit)} ～ {_money(query.ci_high_minor, scale, unit)}"
        f"（±{_money(ci_half, scale, unit)} / ±{float(query.rel_error_pct):.4f}%） |"
    )
    lines.append(f"| 全量真值（同口径全表聚合） | {_money(query.truth_total_minor, scale, unit)} |")
    lines.append(
        f"| 点估计相对误差 | {float(query.truth_rel_error_pct):.4f}%"
        f"（标准 ≤ {float(dataset.precision_target_pct):.2f}% → "
        f"{'达标' if float(query.truth_rel_error_pct) <= float(dataset.precision_target_pct) else '未达标'}） |"
    )
    lines.append(f"| 实际样本量 | {query.sample_size:,} 行（覆盖率 {coverage:.4f}%） |")
    lines.append(
        f"| 抽样耗时 | {float(query.sample_ms):.2f} ms（生产全量基线 {query.full_scan_baseline_ms:,} ms，提速 {speed:,.0f}×） |"
    )
    lines.append("")
    lines.append("## 3. 各层贡献与方差分摊")
    lines.append("")
    lines.append("| 层 | 层容量 N_h | 样本 n_h | 样本均值 | 层贡献估计 | 贡献占比 | 方差占比 | 层 CI 半宽 |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for item in query.strata_detail or []:
        lines.append(
            "| {label}（{code}） | {pop:,} | {n:,} | {mean} | {contrib} | {share:.2f}% | {var:.2f}% | ±{ci} |".format(
                label=item.get("label"),
                code=item.get("code"),
                pop=int(item.get("population", 0)),
                n=int(item.get("sample_size", 0)),
                mean=_money(float(item.get("sample_mean", 0)), scale, unit),
                contrib=_money(float(item.get("contribution", 0)), scale, unit),
                share=float(item.get("contribution_share_pct", 0)),
                var=float(item.get("variance_share_pct", 0)),
                ci=_money(float(item.get("ci_half", 0)), scale, unit),
            )
        )
    lines.append("")
    lines.append("## 4. 线路运费占比与联合误差边界")
    lines.append("")
    composition = getattr(query, "composition", None)
    if composition is None:
        lines.append("> **本查询生成于占比功能上线前，没有占比结果，不予发布占比口径；请重跑近似查询后再导出。**")
    elif not composition.get("publishable"):
        lines.append("> **占比结果拒绝发布（抽样容量不足 / 口径失效），本说明不提供线路占比与误差边界。原因：**")
        for reason in composition.get("reasons") or ["未提供具体原因"]:
            lines.append(f"> - {reason}")
    else:
        conf_pct = int(round(float(composition.get("confidence", 0.95)) * 100))
        lines.append(
            f"占比点估计由同一次抽样的 HT 贡献 `p_h = Ŷ_h / Ŷ` 合成，最大余数法归一，合计恰为 "
            f"{float(composition['point_total_pct']):.2f}%。"
        )
        lines.append("")
        lines.append(
            f"误差边界为 **{conf_pct}% family-wise 联合置信区间（Bonferroni，"
            f"H={composition['family_size']}，z={composition['z_joint']}）**："
            "同一组区间同时覆盖全部线路的真实占比，可直接用于多条线路之间的比较；"
            "单线路边缘区间（z="
            f"{composition['z_marginal']}）仅作参考，不能用于跨线路同时下结论。"
        )
        lines.append("")
        lines.append("| 线路层 | n_h | 占比点估计 | 联合区间下界 | 联合区间上界 | 联合误差半宽 | 单线路边缘半宽（参考） |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
        for item in composition["rows"]:
            lines.append(
                "| {label}（{code}） | {n:,} | {point:.2f}% | {low:.2f}% | {high:.2f}% | ±{half:.2f} pp | ±{marginal:.2f} pp |".format(
                    label=item.get("label"),
                    code=item.get("code"),
                    n=int(item.get("sample_size", 0)),
                    point=float(item.get("point_share_pct", 0)),
                    low=float(item.get("joint_low_pct", 0)),
                    high=float(item.get("joint_high_pct", 0)),
                    half=float(item.get("joint_half_pct", 0)),
                    marginal=float(item.get("marginal_half_pct", 0)),
                )
            )
        lines.append("")
        lines.append(f"- 占比点估计合计：**{float(composition['point_total_pct']):.2f}%**（归一保证，无负数 / 无超 100%）")
        lines.append(
            f"- 发布闸门：每层 n_h ≥ {int(composition['min_stratum_sample'])} 行；"
            "不达标时本章节直接拒绝发布，页面与自检同步标记为不可发布。"
        )
        if composition.get("reasons"):
            for reason in composition["reasons"]:
                lines.append(f"- 口径提示：{reason}")
    lines.append("")
    lines.append("## 5. 精度自检")
    lines.append("")
    if qc is None:
        lines.append("尚未做精度自检：请先在「精度自检」页对本查询跑一次自检，再导出说明。")
    else:
        lines.append(f"- 自检编号：`{qc.code}`")
        lines.append(f"- 结论：**{QC_VERDICT_LABELS.get(qc.verdict, qc.verdict)}**")
        lines.append(f"- 精度标准：相对误差 ≤ {float(qc.target_pct):.2f}%，CI 半宽 ≤ {float(qc.target_pct):.2f}%")
        lines.append("")
        lines.append("| 检查项 | 实测 | 阈值 | 结果 |")
        lines.append("| --- | --- | --- | --- |")
        for item in qc.checks or []:
            lines.append(
                f"| {item.get('label')} | {item.get('actual')} | {item.get('threshold')} | "
                f"{'通过' if item.get('ok') else '不通过'} |"
            )
        lines.append("")
        lines.append("## 6. 三角色复核链")
        lines.append("")
        if not (qc.signoffs or []):
            lines.append("复核链尚未开始（分析师提交 → 负责人复核 → 业务方知悉）。")
        else:
            for index, entry in enumerate(qc.signoffs or [], start=1):
                decision = "通过" if entry.get("decision") == "approve" else "驳回"
                lines.append(
                    f"{index}. {entry.get('stage_label')}：{entry.get('actor_email')}（{entry.get('role')}）"
                    f" → {decision}，{entry.get('at')}"
                    + (f"；备注：{entry.get('note')}" if entry.get("note") else "")
                )
    lines.append("")
    lines.append("## 7. 口径与复现")
    lines.append("")
    lines.append("- 样本量：`n = (z·Σ N_h·S_h / (e·Y))²`，`n_h = n·N_h·S_h / Σ N_h·S_h`（Neyman）；S_h 缺失退化为比例分配，每层最小 30 行、超出层容量截断重分配。")
    lines.append("- 估计量：`Ŷ = Σ_h N_h·ȳ_h`；方差 `V = Σ_h N_h²·(1 - n_h/N_h)·s_h²/n_h`（有限总体校正）；`CI = Ŷ ± z·√V`。")
    lines.append("- 线路占比：`p_h = Ŷ_h / Ŷ`，最大余数法归一到合计 100.00%；占比方差由 Delta 方法在同一批样本的 HT 方差上线性化得到，联合区间用 Bonferroni 分位 `z(1-α/(2H))`，family-wise 同时覆盖各线路比较；区间裁剪到 [0,100] 并显式标注。")
    lines.append("- 发布闸门：任一层 `n_h < 30`（含 0/1 条无法估计方差）或总额非正时，占比结果拒绝发布，页面、自检、导出三处口径一致。")
    lines.append("- 抽样实现：明细行 seed 时写入确定性 `sample_rank`，查询按每层最小 rank 取 n_h 行，同样输入永远同样样本，可复现。")
    lines.append("- 全量真值：同一数据集、同一过滤范围的 `SUM(value_minor)` 真实全表聚合，不是写死的对照值。")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("由 sampleaqp 生成；示例数据为演示用配送运单明细（12 万行），生产表规模按 8,000 万行标注。")
    filename = f"sampleaqp-estimate-{query.code}.md"
    return filename, "\n".join(lines)
